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
import inspect

from whisper.models.whisper_request import DiarSegment
from whisper.models.whisper_response import WordSegment
from whisper.utils.load_model import get_whisper_model
from whisper.utils.post_processing import postprocess_text
from whisper.services.merger import words_to_utterances

def _supports_prev_text(p):
    # Works across transformers versions; only add the arg if supported
    try:
        return "condition_on_prev_text" in inspect.signature(p.__call__).parameters
    except Exception:
        return False


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

    model = get_whisper_model()

    flat_word_dicts: List[dict] = [] 
    word_results: List[WordSegment] = []

    # 3) Transcribe each segment
    for seg in diar_segments:
        t0, t1 = float(seg.start), float(seg.end)
        start_frame = int(t0 * sample_rate)
        end_frame   = int(t1 * sample_rate)
        chunk = waveform[:, start_frame:end_frame]

        # run model in background
        call_kwargs = {
            "return_timestamps": "word",
            "chunk_length_s": 30,
            "sampling_rate": sample_rate,
            "generate_kwargs": {
                "language": "th",   # or from settings
                "num_beams": 5,
                "task": "transcribe",
            },
        }
        if _supports_prev_text(model):
            call_kwargs["condition_on_prev_text"] = True

        audio_np = chunk.mean(dim=0).cpu().numpy()
        out = await asyncio.to_thread(model, audio_np, **call_kwargs)

        # 3a) word-level chunks
        if isinstance(out, dict) and "chunks" in out:
            for c in out["chunks"]:
                c0, c1 = c.get("timestamp", (None, None))
                txt    = (c.get("text") or "").strip()
                if c0 is None or not text:
                    continue
                
                # make timestamps global (offset by diar segment start)
                g0 = t0 + float(c0)
                g1 = t0 + float(c1 if c1 is not None else c0) 


                # Apply post-processing to the word token 
                clean_txt = postprocess_text(txt, day_first=True)

                ws = WordSegment(
                    start=g0, 
                    end=g1, 
                    speaker=seg.speaker, 
                    text=clean_txt
                )
                word_results.append(ws) 

                flat_word_dicts.append({ 
                    "start": g0, 
                    "end": g1, 
                    "speaker": seg.speaker or "Speaker", 
                    "text": clean_txt
                })
                
        # 3b) chunk-level fallback
        else:
            text = out.get("text", "").strip() if isinstance(out, dict) else ""
            if text:
                clean_txt = postprocess_text(text, day_first=True)
                
                # Emit a single word-like span to keep outputs consistent
                ws = WordSegment(start=t0, end=t1, speaker=seg.speaker, text=clean_txt)
                word_results.append(ws)
                flat_word_dicts.append({
                    "start": t0,
                    "end": t1, 
                    "speaker": seg.speaker or "Speaker", 
                    "text": clean_txt 
                })

        # 4)  Merge word in utterances (speaker-aware) and render user line 
        utterances = words_to_utterances(flat_word_dicts, joiner="", max_gap_s=0.6)

        lines: List[str] = [] 
        for u in utterances: 
            # Post-process the merged line text as a second pass (safe idempotent)
            line_txt = postprocess_text(u["text"], day_first=True)
            lines.append(f"[{u['start']:.2f}-{u['end']:.2f}] {u['speaker']}: {line_txt}")
    
    return word_results, lines