from pathlib import Path
from typing import List, Optional, Tuple
import asyncio, inspect
import torchaudio

from whisper.models.whisper_request import DiarSegment
from whisper.models.whisper_response import WordSegment
from whisper.utils.load_model import get_whisper_model
from whisper.utils.post_processing import postprocess_text
from whisper.services.merger import words_to_utterances
from whisper.config.settings import LANGUAGE
from whisper.utils.same_speaker import merge_turns_by_speaker
from whisper.utils.fix_missing_end import _fix_missing_ends  # expects list[chunk]

def _supports_prev_text(pipeline_obj) -> bool:
    try:
        return "condition_on_prev_text" in inspect.signature(pipeline_obj.__call__).parameters
    except Exception:
        return False

async def transcribe(
    wav_path: Path,
    segments: Optional[List[DiarSegment]]
) -> Tuple[List[WordSegment], List[str]]:
    # 1) Load audio
    waveform, sample_rate = await asyncio.to_thread(torchaudio.load, str(wav_path))

    # 2) Diarization segments (or whole file)
    if segments:
        diar_segments = sorted(segments, key=lambda s: s.start)
    else:
        total_dur = waveform.shape[1] / sample_rate
        diar_segments = [DiarSegment(start=0.0, end=total_dur)]

    model = get_whisper_model()

    flat_word_dicts: List[dict] = []
    word_results: List[WordSegment] = []

    # 3) Build batched inputs (GPU-efficient)
    batched: List[dict] = []
    meta: List[Tuple[DiarSegment, float, float]] = []

    for seg in diar_segments:
        t0, t1 = float(seg.start), float(seg.end)
        s0 = int(t0 * sample_rate); s1 = int(t1 * sample_rate)
        chunk = waveform[:, s0:s1]

        audio_mono = chunk.mean(dim=0) if chunk.shape[0] > 1 else chunk.squeeze(0)
        audio_np = audio_mono.float().cpu().numpy()
        batched.append({"array": audio_np, "sampling_rate": sample_rate})
        meta.append((seg, t0, t1))

    # 4) Single batched call
    call_kwargs = {
        "return_timestamps": "word",
        "generate_kwargs": {
            "language": str(LANGUAGE),  # e.g., "th"
            "num_beams": 5,
            "task": "transcribe",
        },
    }
    if _supports_prev_text(model):
        call_kwargs["condition_on_prev_text"] = True

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
