from pathlib import Path
from typing import List, Optional, Tuple
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

def best_mono(chunk: torch.Tensor) -> torch.Tensor:
    # chunk: (C, T) 
    if chunk.ndim == 1: 
        return chunk 
    if chunk.shape[0] == 1:
        return chunk.squeeze(0).contiguous() 

    ch_energy = chunk.abs().mean(dim=1)  # (C,)
    best_idx = int(torch.argmax(ch_energy).item())
    return chunk[best_idx].contiguous()  # (T,)

def normalize_peak(x: torch.Tensor, peak_target: float = 0.95) -> torch.Tensor:
    peak = x.abs().max() 
    if peak > 0: 
        x = (x / peak) * peak_target
    return x

async def transcribe(
    wav_path: Path,
    segments: Optional[List[DiarSegment]]
) -> Tuple[List[WordSegment], List[str]]:
    # 1) Load audio
    waveform, sample_rate = await asyncio.to_thread(torchaudio.load, str(wav_path))
    waveforn = waveform.float().contiguous()

    # 2) Explicit resample to Whisper's SR 
    if sample_rate != TARGET_SR: 
        waveform = torchaudio.functional.resample(
            waveform, sample_rate, TARGET_SR, lowpass_filter_width=64
        )
        sample_rate = TARGET_SR
    
    total_sameples = waveform.shape[1] 
    total_dur = total_sameples / sample_rate 

    # 3) Diarization segments (or whole file), with small padding
    if segments:
        diar_segments = sorted(segments, key=lambda s: s.start)
    else:
        diar_segments = [DiarSegment(start=0.0, end=total_dur)]

    model = get_whisper_model()

    flat_word_dicts: List[dict] = []
    word_results: List[WordSegment] = []

    batched: List[dict] = [] 
    meta: List[Tuple[DiarSegment, float, float]] = []

    for segment in diar_segments:
        # pad & clamp 
        t0 = max(0.0, float(segment.start) - PAD_S) 
        t1 = min(float(segment.end) + PAD_S, total_dur)

        s0 = int(t0 * sample_rate)
        s1 = int(t1 * sample_rate) 
        if s1 <= s0: 
            continue 

        chunk = waveform[:, s0:s1]  # (C, L)
        if chunk.numel() == 0: 
            continue

        # choose best single channel 
        audio_mono = best_mono(chunk)  # (Tesg,) 
        # quick silence/too-short filter 
        if audio_mono.abs().mean().item() < 1e-4: 
            continue 
        if audio_mono.shape[0] < int(MIN_LEN_S * sample_rate):
            continue 

        # normalize peaks 
        audio_mono = normalize_peak(audio_mono)

        # numpy float32 
        audio_np = audio_mono.numpy().astype("float32")
        batched.append({"array": audio_np, "sampling_rate": sample_rate})
        meta.append((segment, t0, t1))
    
    if not batched:
        return [], []

    # 4) Single batched call
    call_kwargs = {
        "return_timestamps": "word",
        "chunk_length_s": 20,
        "stride_length_s": (5.0, 5.0),
        "batch_size": max(1, min(8, len(batched))),
        "generate_kwargs": {
            "language": LANGUAGE,
            "task": "transcribe",
            "suppress_blank": True,
            "temperature": 0.0,
        },
        "condition_on_previous_text": False,
    }

    outs = await asyncio.to_thread(model, batched, **call_kwargs)
    if not isinstance(outs, list):
        outs = [outs]

    # 5) Parse results → per-word segments (global timestamps)
    for (seg, t0, t1), out in zip(meta, outs):
        if isinstance(out, dict) and "chunks" in out and isinstance(out["chunks"], list):
            chunks = _fix_missing_ends(out["chunks"])  # fill missing end times
            for c in chunks:
                c0, c1 = c.get("timestamp", (None, None))
                txt = (c.get("text") or "").strip()
                if c0 is None or not txt:
                    continue
                g0 = t0 + float(c0)
                g1 = t0 + float(c1 if c1 is not None else c0)

                # Keep word text raw here; we post-process at turn-level (fewer ops)
                ws = WordSegment(start=g0, end=g1, speaker=seg.speaker, text=txt)
                word_results.append(ws)
                flat_word_dicts.append({
                    "start": g0, "end": g1,
                    "speaker": seg.speaker or "Speaker",
                    "text": txt,
                })
        else:
            # Fallback: chunk-level only
            txt = out.get("text", "").strip() if isinstance(out, dict) else ""
            if txt:
                ws = WordSegment(start=t0, end=t1, speaker=seg.speaker, text=txt)
                word_results.append(ws)
                flat_word_dicts.append({
                    "start": t0, "end": t1,
                    "speaker": seg.speaker or "Speaker",
                    "text": txt,
                })

    # 6) Merge words → utterances (speaker-aware), then collapse adjacent same-speaker turns
    utterances = words_to_utterances(flat_word_dicts, joiner="", max_gap_s=0.6)
    turns = merge_turns_by_speaker(utterances, max_gap_s=0.6, joiner="")

    # 7) Render lines (post-process once at the turn level; idempotent)
    lines: List[str] = [
        f"[{u['start']:.2f}-{u['end']:.2f}] {u['speaker']}: {postprocess_text(u['text'], day_first=True)}"
        for u in turns if u.get("text")
    ]

    return word_results, lines