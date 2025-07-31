"""
Transcription Service Logic.

Defines the core `transcribe()` function that takes a WAV file path and optional
diarization segments, and returns word-level segments and formatted transcript lines.

Returns:
    Tuple[List[WordSegment], List[str]]: Detailed segments and plain text lines.
"""

from pathlib import Path
from typing import List, Optional, Tuple
import asyncio
import torchaudio

from whisper.models.whisper_request import DiarSegment
from whisper.models.whisper_response import WordSegment
from whisper.utils.load_model import get_whisper_model

# ─── Transcription Logic ───────────────────────────────────────────────────────────
async def transcribe(
    wav_path: Path,
    segments: Optional[List[DiarSegment]]
) -> Tuple[List[WordSegment], List[str]]:
    
    # 1) Load audio
    waveform, sample_rate = await asyncio.to_thread(torchaudio.load, str(wav_path))

    # 2) Determine diarization segments
    if segments:
        diar_segments = segments
    else:
        total_dur = waveform.shape[1] / sample_rate
        diar_segments = [DiarSegment(start=0.0, end=total_dur)]

    results: List[WordSegment] = []
    lines: List[str] = []
    model = get_whisper_model()

    # 3) Transcribe each segment
    for seg in diar_segments:
        t0, t1 = seg.start, seg.end
        start_frame = int(t0 * sample_rate)
        end_frame   = int(t1 * sample_rate)
        chunk = waveform[:, start_frame:end_frame]

        # run model in background
        audio_np = chunk.mean(dim=0).cpu().numpy()
        out = await asyncio.to_thread(model, audio_np)

        # 3a) word-level chunks
        if isinstance(out, dict) and "chunks" in out:
            for c in out["chunks"]:
                c0, c1 = c.get("timestamp", (None, None))
                text   = c.get("text", "").strip()
                if c0 is None or not text:
                    continue
                c1 = c1 or t1
                ws = WordSegment(start=c0, end=c1, speaker=seg.speaker, text=text)
                results.append(ws)
                lines.append(f"[{c0:.2f}-{c1:.2f}] {seg.speaker or 'Speaker'}: {text}")
        # 3b) chunk-level fallback
        else:
            text = out.get("text", "").strip() if isinstance(out, dict) else ""
            if text:
                ws = WordSegment(start=t0, end=t1, speaker=seg.speaker, text=text)
                results.append(ws)
                lines.append(f"[{t0:.2f}-{t1:.2f}] {seg.speaker or 'Speaker'}: {text}")

    return results, lines