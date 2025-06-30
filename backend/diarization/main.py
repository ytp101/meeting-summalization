import os
import logging
import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import torch
import torchaudio
from pyannote.audio import Pipeline

# ——— Logging ——————————————————————————————————————————————————————————————
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Starting Speaker Diarization Service")

# ——— FastAPI App ——————————————————————————————————————————————————————————
app = FastAPI(title="Speaker Diarization Service")

# ——— Configuration via ENV —————————————————————————————————————————————————————
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    logger.error("HF_TOKEN environment variable is not set")
    raise RuntimeError("HF_TOKEN environment variable is required")

DIA_MODEL = os.getenv("DIAR_MODEL", "pyannote/speaker-diarization-3.1")
PORT = int(os.getenv("PORT", 8004))

# ——— Load Model ———————————————————————————————————————————————————————————
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

try:
    logger.info(f"Loading diarization model '{DIA_MODEL}' on {device}")
    diarization_pipeline = Pipeline.from_pretrained(
        DIA_MODEL,
        use_auth_token=HF_TOKEN,
    )
    diarization_pipeline.to(device)
    logger.info("Diarization model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load diarization model: {e}")
    raise

# ——— Pydantic Schema ———————————————————————————————————————————————————————
class DiarizationRequest(BaseModel):
    audio_path: str  # Full path to WAV file

# ——— Health Endpoints ———————————————————————————————————————————————————————
@app.get("/", summary="Liveness check")
async def root():
    return {
        "status": "running",
        "model": DIA_MODEL,
        "device": str(device)
    }

@app.get("/healthcheck", summary="Dependency health check")
async def healthcheck():
    model_loaded = diarization_pipeline is not None
    return JSONResponse(
        {"status": "healthy" if model_loaded else "unhealthy",
         "model_loaded": model_loaded,
         "device": str(device)},
        status_code=200 if model_loaded else 503
    )

# ——— Diarization Endpoint —————————————————————————————————————————————————————
@app.post("/diarization/", summary="Perform speaker diarization on audio file")
async def diarize(req: DiarizationRequest):
    # Validate input path
    audio_path = Path(req.audio_path)
    if not audio_path.is_file():
        logger.warning(f"Audio file not found: {audio_path}")
        raise HTTPException(status_code=404, detail="Audio file not found")

    # Load audio on background thread
    try:
        waveform, sample_rate = await asyncio.to_thread(
            torchaudio.load, str(audio_path)
        )
    except Exception as e:
        logger.error(f"Failed to load audio: {e}")
        raise HTTPException(status_code=500, detail="Could not load audio file")

    # Run diarization
    try:
        annotation = await asyncio.to_thread(
            diarization_pipeline, 
            {"waveform": waveform, "sample_rate": sample_rate}
        )
    except Exception as e:
        logger.error(f"Diarization processing failed: {e}")
        raise HTTPException(status_code=500, detail="Diarization processing failed")

    # Extract speaker segments
    segments = [
        {"start": round(turn.start, 3),
         "end": round(turn.end, 3),
         "speaker": label}
        for turn, _, label in annotation.itertracks(yield_label=True)
    ]

    return {"segments": segments}

# ——— Run Server —————————————————————————————————————————————————————
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
