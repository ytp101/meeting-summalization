from pathlib import Path
from typing import List, Optional, Tuple
import asyncio
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
from whisper.utils.logger import logger

from .audio import best_mono, normalize_peak
from .asr import build_hf_asr_kwargs, asr_with_policy_ladder
from .progress import tqdm as _tqdm, post_progress as _post_progress, map_progress as _map_progress


# ——— Main ASR ————————————————————————————————————————————————

async def transcribe(
    wav_path: Path,
    segments: Optional[List[DiarSegment]],
    *,
    task_id: Optional[str] = None,
    progress_url: Optional[str] = None,
    progress_min: Optional[float] = None,
    progress_max: Optional[float] = None,
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

    # Progress bounds
    pmin = float(progress_min) if progress_min is not None else None
    pmax = float(progress_max) if progress_max is not None else None
    if progress_url and pmin is not None:
        await _post_progress(progress_url, {
            "service": "whisper", "step": "prep", "status": "started", "progress": pmin,
            "total_segments": len(segments) if segments else 1,
        })

    flat_word_dicts: List[dict] = []
    word_results: List[WordSegment] = []

    batched: List[dict] = []
    meta: List[Tuple[DiarSegment, float, float]] = []

    for i, segment in enumerate(_tqdm(diar_segments, desc="Prep segments", unit="seg")):
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
        # HF ASR pipeline expects dict inputs as {"raw": np.ndarray, "sampling_rate": int}
        batched.append({"raw": audio_np, "sampling_rate": sample_rate})
        meta.append((segment, t0, t1))

    if not batched:
        return [], []

    # 4) Single batched call (HF pipeline) via policy ladder
    call_kwargs = build_hf_asr_kwargs(
        model, batch_len=len(batched), language=str(LANGUAGE) if LANGUAGE else None
    )
    # progress callback for ASR batches
    async def _cb(done: int, total: int, stage: str):
        if progress_url and pmin is not None and pmax is not None:
            prog = _map_progress(done, total, pmin, pmax)
            await _post_progress(progress_url, {
                "service": "whisper", "step": f"asr:{stage}", "status": "progress", "progress": prog,
                "done": done, "total": total,
            })

    outs = await asr_with_policy_ladder(model, batched, call_kwargs, progress_cb=_cb)
    if not isinstance(outs, list):
        outs = [outs]

    # 5) Parse → per-word segments with global timestamps
    for idx, ((segment, t0, t1), out) in enumerate(zip(meta, outs)):
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
        # parse progress
        if progress_url and pmin is not None and pmax is not None:
            prog = _map_progress(idx + 1, len(meta), pmin, pmax)
            await _post_progress(progress_url, {
                "service": "whisper", "step": "parse", "status": "progress", "progress": prog,
                "done": idx + 1, "total": len(meta)
            })

    # 6) Merge words → utterances (speaker-aware), then collapse adjacent same-speaker turns
    utterances = words_to_utterances(flat_word_dicts, joiner="", max_gap_s=0.6)
    logger.info(utterances)
    turns = merge_turns_by_speaker(utterances, max_gap_s=None, joiner=" ")

    # 7) Render lines
    lines: List[str] = [
        f"[{u['start']:.2f}-{u['end']:.2f}] {u['speaker']}: {postprocess_text(u['text'], day_first=True)}"
        for u in turns if u.get("text")
    ]

    if progress_url and pmax is not None:
        await _post_progress(progress_url, {
            "service": "whisper", "step": "parse", "status": "completed", "progress": pmax,
        })

    return word_results, lines
