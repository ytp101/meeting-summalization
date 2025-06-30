import os
import asyncio
import logging
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

# ——— Logging & Configuration ——————————————————————————————————
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Meeting Audio Preprocessor")

# Timeout for ffmpeg operations (seconds)
FFMPEG_TIMEOUT = int(os.getenv("FFMPEG_TIMEOUT", 600))

# ——— Pydantic Model for Input ————————————————————————————————————————————————
class PreprocessRequest(BaseModel):
    input_path: str  # Full path to the source media file
    output_dir: str  # Directory where the WAV should be written

# ——— FFmpeg Helpers ————————————————————————————————————————————————
async def _ffmpeg_available() -> bool:
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-version",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()
    return proc.returncode == 0

async def run_ffmpeg(input_file: Path, output_file: Path) -> None:
    """
    Convert input_file to output_file with:
      - audio only (drop video)
      - 16 kHz mono 16-bit PCM
      - loudness normalization
    Raises HTTPException on failure or timeout.
    """
    cmd = [
        "ffmpeg", "-y", "-i", str(input_file),
        "-vn",              # no video
        "-ar", "16000",   # sample rate
        "-ac", "1",       # mono
        "-c:a", "pcm_s16le",  # PCM 16-bit
        "-af", "loudnorm",     # normalize volume
        str(output_file)
    ]
    logger.info(f"Running FFmpeg: {' '.join(cmd)}")

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=FFMPEG_TIMEOUT
        )
        if proc.returncode != 0:
            error_msg = stderr.decode(errors="ignore").strip().splitlines()[-1]
            logger.error(f"FFmpeg error [{proc.returncode}]: {error_msg}")
            raise HTTPException(500, f"FFmpeg failed: {error_msg}")
    except asyncio.TimeoutError:
        logger.error(f"FFmpeg timed out after {FFMPEG_TIMEOUT}s")
        proc.kill()
        raise HTTPException(504, f"FFmpeg timed out after {FFMPEG_TIMEOUT}s")

# ——— Startup & Health ————————————————————————————————————————————————
@app.on_event("startup")
async def on_startup():
    if await _ffmpeg_available():
        logger.info("FFmpeg is available")
    else:
        logger.error("FFmpeg not found on PATH — service may fail")

@app.get("/", summary="Liveness check")
def root():
    return {"status": "preprocess running"}

@app.get("/healthcheck", summary="Dependency health check")
async def healthcheck():
    ok = await _ffmpeg_available()
    return {"status": "healthy" if ok else "unhealthy"}

# ——— Preprocess Endpoint ———————————————————————————————————————————————
@app.post("/preprocess/", summary="Convert audio/video to normalized WAV")
async def preprocess(req: PreprocessRequest):
    # Validate input path
    input_path = Path(req.input_path)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise HTTPException(404, "Input file not found")

    # Prepare output
    output_dir = Path(req.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{input_path.stem}.wav"

    # Run conversion
    await run_ffmpeg(input_path, output_file)

    if not output_file.exists():
        logger.error(f"WAV not produced: {output_file}")
        raise HTTPException(500, "Failed to produce WAV file")

    logger.info(f"Produced WAV: {output_file}")
    response = [{"preprocessed_file_path": str(output_file)}]
    return JSONResponse(content=jsonable_encoder(response))

# ——— Serve ———————————————————————————————————————————————————————
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "preprocess:app", host="0.0.0.0",
        port=int(os.getenv("PORT", 8001)), log_level="info"
    )
