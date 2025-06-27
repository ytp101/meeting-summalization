from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pyannote.audio import Pipeline
from fastapi.responses import JSONResponse
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Starting VAD service")

# Environment variables
HF_TOKEN = os.getenv("HF_TOKEN")
BASE_DIR_WAV = os.getenv("BASE_DIR_WAV", "/usr/local/app/data/wav/")

# Validate HF Token
if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN environment variable is not set.")

# Load the VAD model
try:
    logger.info("Loading VAD model from Hugging Face")
    pipeline = Pipeline.from_pretrained(
        "pyannote/voice-activity-detection",
        use_auth_token=HF_TOKEN
    )
except Exception as e:
    logger.error(f"Failed to load VAD model: {e}")
    raise RuntimeError("VAD model loading failed")

# FastAPI app
app = FastAPI(title="Voice Activity Detection (VAD) Service")

# Request model
class AudioFile(BaseModel):
    filename: str

@app.get("/")
def root():
    return {"status": "VAD service running", "model": "pyannote/voice-activity-detection"}

@app.post("/vad/")
def vad_segments(file: AudioFile):
    audio_path = os.path.join(BASE_DIR_WAV, f"{file.filename}.wav")
    
    if not os.path.exists(audio_path):
        logger.warning(f"Audio file not found: {audio_path}")
        raise HTTPException(status_code=404, detail="Audio file not found")

    try:
        logger.info(f"Running VAD on file: {file.filename}")
        output = pipeline(audio_path)
        segments = [
            {"start": round(speech.start, 3), "end": round(speech.end, 3)}
            for speech in output.get_timeline().support()
        ]
        logger.info(f"Detected {len(segments)} segments")
        return {"segments": segments}
    
    except Exception as e:
        logger.error(f"VAD processing failed: {e}")
        raise HTTPException(status_code=500, detail="VAD processing failed")
