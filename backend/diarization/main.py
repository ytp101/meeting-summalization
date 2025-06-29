import os
import logging

import torch
import torchaudio
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pyannote.audio import Pipeline

# ——— Logging ——————————————————————————————————————————————————————————————
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Starting Speaker Diarization Service")

# ——— Configuration ————————————————————————————————————————————————————————
HF_TOKEN      = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    logger.error("HF_TOKEN environment variable is not set")
    raise RuntimeError("HF_TOKEN environment variable is required")

DIA_MODEL     = os.getenv("DIAR_MODEL", "pyannote/speaker-diarization-3.1")
BASE_DIR_WAV  = os.getenv("BASE_DIR_WAV", "/usr/local/app/data/wav/")
PORT          = int(os.getenv("PORT", 8004))

# ——— Model Initialization ————————————————————————————————————————————————————
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
try:
    logger.info(f"Loading diarization model '{DIA_MODEL}' on {device}")
    diarization_pipeline = Pipeline.from_pretrained(
        DIA_MODEL, 
        use_auth_token=HF_TOKEN,
    )
    diarization_pipeline.to(device)
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load diarization model: {e}")
    raise

# ——— FastAPI App & Schemas ——————————————————————————————————————————————————
app = FastAPI(title="Speaker Diarization Service")

class DiarizationRequest(BaseModel):
    filename: str

# ——— Health Endpoints ——————————————————————————————————————————————————————
@app.get("/")
async def root():
    return {
        "status": "running",
        "model": DIA_MODEL,
        "device": device
    }

@app.get("/healthcheck")
async def healthcheck():
    # A simple check: model is loaded and torch sees GPU if expected
    is_loaded = diarization_pipeline is not None
    return JSONResponse({
        "status": "healthy" if is_loaded else "unhealthy",
        "model_loaded": is_loaded,
        "device": device
    }, status_code=200 if is_loaded else 503)

# ——— Diarization Endpoint ——————————————————————————————————————————————————————
@app.post("/diarization/")
async def diarize(req: DiarizationRequest):
    # Build path to the WAV file
    audio_path = os.path.join(BASE_DIR_WAV, f"{req.filename}.wav")
    if not os.path.isfile(audio_path):
        logger.warning(f"Audio file not found: {audio_path}")
        raise HTTPException(status_code=404, detail="Audio file not found")

    # Load audio
    try:
        waveform, sample_rate = torchaudio.load(audio_path)
    except Exception as e:
        logger.error(f"Failed to load audio: {e}")
        raise HTTPException(status_code=500, detail="Could not load audio file")

    # Run diarization
    try:
        annotation = diarization_pipeline({
            "waveform": waveform,
            "sample_rate": sample_rate
        })
    except Exception as e:
        logger.error(f"Diarization processing failed: {e}")
        raise HTTPException(status_code=500, detail="Diarization processing failed")

    # Extract segments
    segments = [
        {
            "start": round(turn.start, 3),
            "end":   round(turn.end,   3),
            "speaker": label
        }
        for turn, _, label in annotation.itertracks(yield_label=True)
    ]

    return {"segments": segments}

# ——— Run Uvicorn ——————————————————————————————————————————————————————
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, log_level="info")
