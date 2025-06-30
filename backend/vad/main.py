import os
import logging
import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pyannote.audio import Pipeline as PyannotePipeline

# ─── Logging & Configuration ─────────────────────────────────────────────────────
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
logger = logging.getLogger("vad_service")

HF_TOKEN   = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    logger.error("HF_TOKEN environment variable is missing.")
    raise RuntimeError("HF_TOKEN must be set to load the VAD model.")

# ─── FastAPI Initialization ───────────────────────────────────────────────────────
app = FastAPI(title="Voice Activity Detection Service")

# ─── Pydantic Schemas ─────────────────────────────────────────────────────────────
class VADRequest(BaseModel):
    input_path: str  # full path to .wav file

class Segment(BaseModel):
    start: float
    end: float

class VADResponse(BaseModel):
    segments: list[Segment]

# ─── Model Loader ─────────────────────────────────────────────────────────────────
ad_global: PyannotePipeline | None = None

@app.on_event("startup")
async def load_vad_model():
    global vad_pipeline
    logger.info("Loading VAD model 'pyannote/voice-activity-detection'")
    vad_pipeline = await asyncio.to_thread(
        PyannotePipeline.from_pretrained,
        "pyannote/voice-activity-detection",
        use_auth_token=HF_TOKEN
    )
    logger.info("VAD model loaded successfully")

# ─── Health Endpoints ─────────────────────────────────────────────────────────────
@app.get("/", tags=["health"])
def root():
    return {"status": "running"}

@app.get("/healthcheck", tags=["health"])
def healthcheck():
    ready = vad_pipeline is not None
    return {"status": "healthy" if ready else "unhealthy", "model_loaded": ready}

# ─── VAD Inference Endpoint ───────────────────────────────────────────────────────
@app.post("/vad/", response_model=VADResponse, tags=["inference"])
async def vad_segments(req: VADRequest):
    if vad_pipeline is None:
        logger.error("VAD pipeline unavailable")
        raise HTTPException(status_code=503, detail="Service unavailable")

    wav_path = Path(req.input_path)
    if not wav_path.is_file():
        logger.warning(f"WAV file not found: {wav_path}")
        raise HTTPException(status_code=404, detail="Audio file not found")

    try:
        # Run pipeline off main thread
        result = await asyncio.to_thread(vad_pipeline, str(wav_path))
    except Exception as e:
        logger.exception("VAD processing failed")
        raise HTTPException(status_code=500, detail="VAD processing error")

    timeline = result.get_timeline().support()
    segments = [Segment(start=round(seg.start,3), end=round(seg.end,3)) for seg in timeline]
    logger.info(f"Detected {len(segments)} segments")

    return JSONResponse(content={"segments": [s.dict() for s in segments]})

# ─── Serve ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8002)), log_level="info")