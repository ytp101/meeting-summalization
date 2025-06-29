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

# Directories
BASE_DIR_MP4 = Path(os.getenv("BASE_DIR_MP4", "/usr/local/app/data/mp4"))
BASE_DIR_WAV = Path(os.getenv("BASE_DIR_WAV", "/usr/local/app/data/wav"))
# FFmpeg timeout
FFMPEG_TIMEOUT = int(os.getenv("FFMPEG_TIMEOUT", 600))  # seconds

# Make sure dirs exist
for d in (BASE_DIR_MP4, BASE_DIR_WAV):
    d.mkdir(parents=True, exist_ok=True)

# FastAPI app
app = FastAPI(title="Meeting Audio Preprocessor")


# ——— Pydantic Model ————————————————————————————————————————————————
class FilePath(BaseModel):
    filename: str


# ——— FFmpeg Helpers ————————————————————————————————————————————————
async def _ffmpeg_available() -> bool:
    """Quickly check if `ffmpeg` is on PATH by invoking `ffmpeg -version`."""
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-version",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()
    return proc.returncode == 0


async def run_ffmpeg(input_file: Path, output_file: Path) -> None:
    """
    Run ffmpeg to convert <input_file> → <output_file>:
      - drop video
      - 16 kHz mono 16-bit PCM
      - loudness normalization
    Raises HTTPException on any failure or timeout.
    """
    cmd = [
        "ffmpeg", "-y", "-i", str(input_file),
        "-vn",                         # no video
        "-ar", "16000",                # 16 kHz sample rate
        "-ac", "1",                    # mono
        "-c:a", "pcm_s16le",           # 16-bit PCM
        "-af", "loudnorm",             # normalize volume
        str(output_file)
    ]
    logger.info(f"FFmpeg command: {' '.join(cmd)}")

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=FFMPEG_TIMEOUT)

        if proc.returncode != 0:
            err = stderr.decode(errors="ignore")
            logger.error(f"FFmpeg failed (code {proc.returncode}): {err.strip()}")
            raise HTTPException(500, f"FFmpeg processing failed: {err.splitlines()[-1]}")
    except asyncio.TimeoutError:
        logger.error(f"FFmpeg timed out after {FFMPEG_TIMEOUT}s")
        proc.kill()
        raise HTTPException(504, f"FFmpeg timed out after {FFMPEG_TIMEOUT}s")


# ——— Startup & Health ——————————————————————————————————————————————
@app.on_event("startup")
async def on_startup():
    logger.info("Preprocess service starting up")
    if not await _ffmpeg_available():
        logger.error("`ffmpeg` not found on PATH — service will fail")
    else:
        logger.info("`ffmpeg` is available")


@app.get("/", summary="Basic liveness check")
def root():
    return {"status": "Preprocess service is running"}


@app.get("/healthcheck", summary="Dependency healthcheck")
async def healthcheck():
    ok = await _ffmpeg_available()
    status = "healthy" if ok else "unhealthy"
    return {"status": status, "ffmpeg": "available" if ok else "unavailable"}


# ——— Main Preprocess Endpoint —————————————————————————————————————
@app.post(
    "/preprocess/",
    summary="Convert an MP4 (in BASE_DIR_MP4) to a normalized WAV (in BASE_DIR_WAV)",
)
async def preprocess(fp: FilePath):
    # Validate input filename
    name = fp.filename
    in_mp4 = BASE_DIR_MP4 / f"{name}.mp4"
    out_wav = BASE_DIR_WAV / f"{name}.wav"

    logger.info(f"Preprocessing request for `{name}.mp4`")

    if not in_mp4.exists():
        logger.error(f"Input MP4 not found: {in_mp4}")
        raise HTTPException(404, "Input file not found")

    # Ensure output directory exists
    out_wav.parent.mkdir(parents=True, exist_ok=True)

    # Run the conversion
    await run_ffmpeg(in_mp4, out_wav)

    # Final sanity check
    if not out_wav.exists():
        logger.error(f"WAV not produced: {out_wav}")
        raise HTTPException(500, "Failed to produce WAV file")

    logger.info(f"Produced WAV → {out_wav}")
    # Return the _stem_ only, for downstream services
    response = [{"preprocessed_file_path": name}]
    return JSONResponse(content=jsonable_encoder(response))


# ——— Serve ————————————————————————————————————————————————————————
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "preprocess:app", host="0.0.0.0",
        port=int(os.getenv("PORT", 8001)), log_level="info"
    )
