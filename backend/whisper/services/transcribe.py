from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import asyncio, inspect
import torchaudio
import torch

from whisper.models.whisper_request import DiarSegment
from whisper.models.whisper_response import WordSegment
from whisper.utils.load_model import get_whisper_model
from whisper.utils.post_processing import postprocess_text
from whisper.services.merger import words_to_utterances
from whisper.config.settings import LANGUAGE, PAD_S, MIN_LEN_S, TARGET_SR
from whisper.utils.same_speaker import merge_turns_by_speaker
from whisper.utils.fix_missing_end import _fix_missing_ends


# ——— Audio helpers ———————————————————————————————————————————————

def best_mono(chunk: torch.Tensor) -> torch.Tensor:
    """
    Pick the cleanest single channel by mean-abs amplitude proxy.
    Input: (C, T) or (T,)
    Output: (T,)
    """
    if chunk.ndim == 1:
        return chunk.contiguous()
    if chunk.shape[0] == 1:
        return chunk.squeeze(0).contiguous()
    ch_energy = chunk.abs().mean(dim=1)  # (C,)
    best_idx = int(torch.argmax(ch_energy).item())
    return chunk[best_idx].contiguous()


def normalize_peak(x: torch.Tensor, peak_target: float = 0.95) -> torch.Tensor:
    peak = x.abs().max()
    if peak > 0:
        x = (x / peak) * peak_target
    return x.contiguous()


# ——— HF pipeline call helpers (version-safe) —————————————————————

def build_hf_asr_kwargs(model, batch_len: int, language: Optional[str] = "th") -> Dict[str, Any]:
    """
    Build kwargs for transformers.AutomaticSpeechRecognitionPipeline with feature-gating
    for args that may not exist in older versions.
    """
    ck: Dict[str, Any] = {
        "return_timestamps": "word",            # falls back to True if unsupported
        "chunk_length_s": 20,                   # 15–30 works well
        "stride_length_s": (5.0, 5.0),
        "batch_size": max(1, min(8, batch_len)),
        "generate_kwargs": {
            "language": str(language) if language else None,  # None => auto-detect
            "task": "transcribe",
            "temperature": 0.0,
        },
    }
    # Feature-gate optional arg
    try:
        sig = inspect.signature(model.__call__)
        if "condition_on_prev_text" in sig.parameters:
            ck["condition_on_prev_text"] = False
    except Exception:
        pass
    return ck


async def safe_asr_call(model, batched: List[dict], call_kwargs: Dict[str, Any]):
    """
    Robustly call the HF ASR pipeline:
      • If TypeError mentions an unexpected kwarg, drop it and retry.
      • Fallback 'return_timestamps'='word' -> True on older versions.
    """
    try:
        return await asyncio.to_thread(model, batched, **call_kwargs)
    except TypeError as e:
        msg = str(e)
        if "condition_on_prev_text" in msg:
            call_kwargs = dict(call_kwargs)
            call_kwargs.pop("condition_on_prev_text", None)
            return await asyncio.to_thread(model, batched, **call_kwargs)
        if "return_timestamps" in msg and call_kwargs.get("return_timestamps") == "word":
            call_kwargs = dict(call_kwargs)
            call_kwargs["return_timestamps"] = True
            return await asyncio.to_thread(model, batched, **call_kwargs)
        raise


# ——— Memory policy ladder (keeps model, trades throughput) ———————————

POLICIES: Dict[str, Dict[str, Any]] = {
    "standard": {"batch_size": 2, "chunk_length_s": 20, "stride_length_s": (5.0, 5.0)},
    "tight":    {"batch_size": 1, "chunk_length_s": 10, "stride_length_s": (2.0, 2.0)},
    "ultra":    {"batch_size": 1, "chunk_length_s": 6,  "stride_length_s": (1.5, 1.5), "return_timestamps": True},
}

def _merge_kwargs(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    out.update(overrides)
    return out

async def _asr_with_policy_ladder(model, batched: List[dict], base_kwargs: Dict[str, Any]) -> List[dict]:
    import torch as _t
    # 0) Standard
    try:
        kw = _merge_kwargs(base_kwargs, POLICIES["standard"])
        outs = await safe_asr_call(model, batched, kw)
        return outs if isinstance(outs, list) else [outs]
    except _t.cuda.OutOfMemoryError:
        _t.cuda.empty_cache()
    # 1) Tight
    try:
        kw = _merge_kwargs(base_kwargs, POLICIES["tight"])
        outs = await safe_asr_call(model, batched, kw)
        return outs if isinstance(outs, list) else [outs]
    except _t.cuda.OutOfMemoryError:
        _t.cuda.empty_cache()
    # 2) Ultra
    try:
        kw = _merge_kwargs(base_kwargs, POLICIES["ultra"])
        outs = await safe_asr_call(model, batched, kw)
        return outs if isinstance(outs, list) else [outs]
    except _t.cuda.OutOfMemoryError:
        _t.cuda.empty_cache()
    # 3) Sequentialized ultra (last resort)
    results: List[dict] = []
    kw = _merge_kwargs(base_kwargs, POLICIES["ultra"])
    for item in batched:
        try:
            out_i = await safe_asr_call(model, [item], kw)
            results.extend(out_i if isinstance(out_i, list) else [out_i])
        except _t.cuda.OutOfMemoryError:
            _t.cuda.empty_cache()
            safer = dict(kw, chunk_length_s=5, stride_length_s=(1.0, 1.0))
            out_i = await safe_asr_call(model, [item], safer)
            results.extend(out_i if isinstance(out_i, list) else [out_i])
    return results


# ——— Main ASR ————————————————————————————————————————————————

async def transcribe(
    wav_path: Path,
    segments: Optional[List[DiarSegment]]
) -> Tuple[List[WordSegment], List[str]]:
    """
    Transcribe diarized (or full) audio using the HF Whisper pipeline.
    Guardrails: 16k resample, segment padding, best channel, peak normalize, silence/length filters,
    and adaptive VRAM policy ladder.
    """
    # 1) Load audio
    waveform, sample_rate = await asyncio.to_thread(torchaudio.load, str(wav_path))  # (C, T)
    waveform = waveform.float().contiguous()

    # 2) Explicit resample to Whisper SR
    if sample_rate != TARGET_SR:
        waveform = torchaudio.functional.resample(
            waveform, sample_rate, TARGET_SR, lowpass_filter_width=64
        )
        sample_rate = TARGET_SR

    total_samples = waveform.shape[1]
    total_dur = total_samples / sample_rate

    # 3) Diar segments (or whole file) with padding/clamp
    if segments and len(segments) > 0:
        diar_segments = sorted(segments, key=lambda s: s.start)
    else:
        diar_segments = [DiarSegment(start=0.0, end=total_dur)]

    model = get_whisper_model()

    flat_word_dicts: List[dict] = []
    word_results: List[WordSegment] = []

    batched: List[dict] = []
    meta: List[Tuple[DiarSegment, float, float]] = []

    for segment in diar_segments:
        # pad & clamp to avoid mid-phoneme cuts
        t0 = max(0.0, float(segment.start) - float(PAD_S))
        t1 = min(float(segment.end) + float(PAD_S), total_dur)

        s0 = int(t0 * sample_rate)
        s1 = int(t1 * sample_rate)
        if s1 <= s0:
            continue

        chunk = waveform[:, s0:s1]  # (C, L)
        if chunk.numel() == 0:
            continue

        # pick best single channel (avoid destructive mean across channels)
        audio_mono = best_mono(chunk).to(torch.float32)  # (L,)

        # quick silence/too-short guards
        if audio_mono.abs().mean().item() < 1e-4:
            continue
        if audio_mono.shape[0] < int(float(MIN_LEN_S) * sample_rate):
            continue

        # normalize peaks to stable dynamic range
        audio_mono = normalize_peak(audio_mono)

        # numpy float32 buffer
        audio_np = audio_mono.cpu().numpy().astype("float32")
        batched.append({"array": audio_np, "sampling_rate": sample_rate})
        meta.append((segment, t0, t1))

    if not batched:
        return [], []

    # 4) Single batched call (HF pipeline) via policy ladder
    call_kwargs = build_hf_asr_kwargs(
        model, batch_len=len(batched), language=str(LANGUAGE) if LANGUAGE else None
    )
    outs = await _asr_with_policy_ladder(model, batched, call_kwargs)
    if not isinstance(outs, list):
        outs = [outs]

    # 5) Parse → per-word segments with global timestamps
    for (segment, t0, t1), out in zip(meta, outs):
        chunks = out.get("chunks") if isinstance(out, dict) else None
        
        if isinstance(chunks, list):
            chunks = _fix_missing_ends(out["chunks"])
            for c in chunks:
                c0, c1 = c.get("timestamp", (None, None))
                txt = (c.get("text") or "").strip()
                if c0 is None or not txt:
                    continue
                g0 = t0 + float(c0)
                g1 = t0 + float(c1 if c1 is not None else c0)

                ws = WordSegment(start=g0, end=g1, speaker=segment.speaker, text=txt)
                word_results.append(ws)
                flat_word_dicts.append({
                    "start": g0,
                    "end": g1,
                    "speaker": segment.speaker or "Speaker",
                    "text": txt,
                })
        else:
            # Fallback: segment-level only
            txt = out.get("text", "").strip() if isinstance(out, dict) else ""
            if txt:
                ws = WordSegment(start=t0, end=t1, speaker=segment.speaker, text=txt)
                word_results.append(ws)
                flat_word_dicts.append({
                    "start": t0,
                    "end": t1,
                    "speaker": segment.speaker or "Speaker",
                    "text": txt,
                })

    # 6) Merge words → utterances (speaker-aware), then collapse adjacent same-speaker turns
    utterances = words_to_utterances(flat_word_dicts, joiner="", max_gap_s=0.6)
    turns = merge_turns_by_speaker(utterances, max_gap_s=0.6, joiner="")

    # 7) Render lines
    lines: List[str] = [
        f"[{u['start']:.2f}-{u['end']:.2f}] {u['speaker']}: {postprocess_text(u['text'], day_first=True)}"
        for u in turns if u.get("text")
    ]

    return word_results, lines
