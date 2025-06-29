import os
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pyannote.audio import Pipeline as PyannotePipeline

# ——— Configuration & Logging —————————————————————————————————————————————
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

HF_TOKEN = os.getenv("HF_TOKEN")
BASE_DIR_WAV = Path(os.getenv("BASE_DIR_WAV", "/usr/local/app/data/wav/"))
MODEL_NAME = "pyannote/voice-activity-detection"

# ——— FastAPI Initialization —————————————————————————————————————————————————
app = FastAPI(title="Voice Activity Detection (VAD) Service")

class AudioFile(BaseModel):
    filename: str

vad_pipeline: PyannotePipeline | None = None

# ——— Startup Event: Validate & Load Model ———————————————————————————————————
@app.on_event("startup")
def startup_event():
    global vad_pipeline

    # check HF token
    if not HF_TOKEN:
        logger.error("HF_TOKEN environment variable is missing.")
        raise RuntimeError("HF_TOKEN must be set to load the VAD model.")
    
    # ensure WAV directory exists
    BASE_DIR_WAV.mkdir(parents=True, exist_ok=True)
    logger.info(f"WAV directory: {BASE_DIR_WAV}")

    # load the pyannote VAD pipeline
    try:
        logger.info(f"Loading VAD model '{MODEL_NAME}' from Hugging Face…")
        vad_pipeline = PyannotePipeline.from_pretrained(
            MODEL_NAME,
            use_auth_token=HF_TOKEN
        )
        logger.info("VAD model loaded successfully.")
    except Exception:
        logger.exception("Failed to load VAD model.")
        raise

# ——— Root & Healthcheck Endpoints ——————————————————————————————————————————
@app.get("/", tags=["health"])
def root():
    return {"status": "running", "model": MODEL_NAME}

@app.get("/healthcheck", tags=["health"])
def healthcheck():
    if vad_pipeline is None:
        return {"status": "unhealthy", "detail": "VAD model not initialized"}
    if not BASE_DIR_WAV.exists():
        return {"status": "unhealthy", "detail": f"WAV dir missing: {BASE_DIR_WAV}"}
    return {"status": "healthy", "model": MODEL_NAME, "wav_dir": str(BASE_DIR_WAV)}

# ——— VAD Endpoint ————————————————————————————————————————————————————————
@app.post("/vad/", response_model=dict, tags=["inference"])
def vad_segments(request: AudioFile):
    if vad_pipeline is None:
        logger.error("VAD pipeline is not ready.")
        raise HTTPException(status_code=503, detail="Service unavailable")

    audio_path = BASE_DIR_WAV / f"{request.filename}.wav"
    if not audio_path.exists():
        logger.warning(f"Requested file not found: {audio_path}")
        raise HTTPException(status_code=404, detail="Audio file not found")

    try:
        logger.info(f"Running VAD on '{audio_path.name}'")
        result = vad_pipeline(str(audio_path))

        # Extract the “speech” segments timeline
        timeline = result.get_timeline().support()
        segments = [
            {"start": round(seg.start, 3), "end": round(seg.end, 3)}
            for seg in timeline
        ]

        logger.info(f"Detected {len(segments)} speech segments")
        return JSONResponse(content={"segments": segments})

    except Exception:
        logger.exception("VAD processing failed")
        raise HTTPException(status_code=500, detail="VAD processing failed")
