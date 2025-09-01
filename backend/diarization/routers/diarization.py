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

        annotation = await asyncio.to_thread(
            pipeline,
            {"waveform": waveform, "sample_rate": sample_rate}
        )
    except Exception as e:
        logger.error(f"Diarization failed: {e}")
        raise HTTPException(status_code=500, detail="Diarization processing failed")

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
    return DiarizationResponse(segments=segments)
