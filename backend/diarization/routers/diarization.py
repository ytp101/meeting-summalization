"""
Diarization Endpoint

This route handles POST requests for speaker diarization on local audio files.
It returns a list of speaker-labeled segments with start and end timestamps.
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
import torchaudio
import asyncio
import httpx
import math

# ——— Internal imports —————————————————————————————————————
from diarization.utils.load_model import get_diarization_pipeline
from diarization.utils.logger import logger
from diarization.models.diarization_request import DiarizationRequest
from diarization.models.diarization_response import Segment, DiarizationResponse

router = APIRouter()

def _ensure_under_base(p: Path, base: Path = Path("/data")) -> None:
    try:
        rp = p.resolve(); basep = base.resolve()
        rp.relative_to(basep)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Path must be under {base}")

@router.post(
    "/diarization/",
    response_model=DiarizationResponse,
    summary="Perform speaker diarization on audio file",
    tags=["Diarization"]
)
async def diarize(request: DiarizationRequest):
    """
    Run speaker diarization on a local WAV file and return labeled speaker segments.
    """

    audio_path = Path(request.audio_path)
    _ensure_under_base(audio_path)

    if not audio_path.is_file():
        logger.warning(f"Audio file not found: {audio_path}")
        raise HTTPException(status_code=404, detail="Audio file not found")

    try:
        waveform, sample_rate = await asyncio.to_thread(torchaudio.load, str(audio_path))
    except Exception as e:
        logger.error(f"Failed to load audio: {e}")
        raise HTTPException(status_code=500, detail="Could not load audio file")

    pmin = float(request.progress_min) if request.progress_min is not None else None
    pmax = float(request.progress_max) if request.progress_max is not None else None

    if request.progress_url and request.task_id and pmin is not None:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(request.progress_url, json={
                    "service": "diarization", "step": "run", "status": "started", "progress": pmin
                }, timeout=5.0)
        except Exception:
            pass

    try:
        pipeline = get_diarization_pipeline()
        if pipeline is None:
            logger.error("Diarization pipeline is not initialized")
            raise HTTPException(status_code=503, detail="Diarization model not available")

        total_dur = waveform.shape[1] / float(sample_rate)
        # If hooks provided, run chunked for progress; else single-shot
        if request.progress_url and pmin is not None and pmax is not None and total_dur > 1.0:
            chunk_s = 60.0
            n_chunks = int(math.ceil(total_dur / chunk_s))
            all_segments = []
            for idx in range(n_chunks):
                t0 = idx * chunk_s
                t1 = min((idx + 1) * chunk_s, total_dur)
                s0 = int(t0 * sample_rate)
                s1 = int(t1 * sample_rate)
                wav = waveform[:, s0:s1]
                ann = await asyncio.to_thread(pipeline, {"waveform": wav, "sample_rate": sample_rate})
                for turn, _, label in ann.itertracks(yield_label=True):
                    all_segments.append(Segment(start=round(t0 + turn.start, 3), end=round(t0 + turn.end, 3), speaker=label))

                # progress
                prog = pmin + ((idx + 1) / n_chunks) * (pmax - pmin)
                try:
                    async with httpx.AsyncClient() as client:
                        await client.post(request.progress_url, json={
                            "service": "diarization", "step": "run", "status": "progress",
                            "progress": prog, "done": idx + 1, "total": n_chunks
                        }, timeout=5.0)
                except Exception:
                    pass

            # Simple merge of adjacent same-speaker segments with small gaps
            all_segments.sort(key=lambda s: s.start)
            merged = []
            for seg in all_segments:
                if not merged:
                    merged.append(seg)
                else:
                    prev = merged[-1]
                    if seg.speaker == prev.speaker and seg.start <= prev.end + 0.5:
                        prev.end = max(prev.end, seg.end)
                    else:
                        merged.append(seg)
            segments = merged

            # completed
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(request.progress_url, json={
                        "service": "diarization", "step": "run", "status": "completed", "progress": pmax,
                        "segments_count": len(segments)
                    }, timeout=5.0)
            except Exception:
                pass
        else:
            # single-shot
            annotation = await asyncio.to_thread(pipeline, {"waveform": waveform, "sample_rate": sample_rate})
            segments = [
                Segment(
                    start=round(turn.start, 3),
                    end=round(turn.end, 3),
                    speaker=label
                )
                for turn, _, label in annotation.itertracks(yield_label=True)
            ]
            if request.progress_url and request.task_id and pmax is not None:
                try:
                    async with httpx.AsyncClient() as client:
                        await client.post(request.progress_url, json={
                            "service": "diarization", "step": "run", "status": "completed", "progress": pmax,
                            "segments_count": len(segments)
                        }, timeout=5.0)
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"Diarization failed: {e}")
        raise HTTPException(status_code=500, detail="Diarization processing failed")
    return DiarizationResponse(segments=segments)
