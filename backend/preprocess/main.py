"""
Module: preprocess/main.py 
Service: Converts input media files to normalized 16bit mono WAV format using FFmpeg. 
         Intended as a preprocessing step before Diarization and ASR (e.g., Whisper)
Author: yodsran
"""
# TODO: Rewrite Docker file
# TODO: Write unit test (liveness, healthcheck, process_file)
from fastapi import FastAPI
from contextlib import asynccontextmanager

from preprocess.utils.ffmpeg_checker import is_ffmpeg_available
from preprocess.utils.logger import logger
from preprocess.routers import root, healthcheck, preprocess

# FastAPI app
app = FastAPI(title="Audio Preprocessor")

# Add route 
app.include_router(root.router)
app.include_router(healthcheck.router)
app.include_router(preprocess.router)

# ——— Startup ———————
@asynccontextmanager
async def lifespan(app: FastAPI): 
    if await is_ffmpeg_available():
        logger.info("FFmpeg is available")
    else:
        logger.error("FFmpeg is not installed. Please install it first.")

    yield

    logger.info("Shutting down Audio Preprocessor")