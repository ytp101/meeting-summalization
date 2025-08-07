"""
Main entrypoint for the Speaker Diarization FastAPI service.

This file initializes the FastAPI app, attaches modular routers,
and serves as the starting point for deployment via Uvicorn or ASGI.
"""

from fastapi import FastAPI
from diarization.routers import root, healthcheck, diarization
import os 

import os

os.environ["HF_HOME"] = "/home/app/.cache/huggingface"
os.environ["XDG_CACHE_HOME"] = "/home/app/.cache"

# ——— FastAPI App Initialization ——————————————————————————————————————
app = FastAPI(
    title="Speaker Diarization Service",
    description="A microservice for performing speaker diarization on WAV audio files.",
    version="1.0.0"
)

# ——— Register Routers ——————————————————————————————————————————————
app.include_router(root.router)          # Liveness check ("/")
app.include_router(healthcheck.router)   # Health probe ("/healthcheck")
app.include_router(diarization.router)   # Main diarization endpoint ("/diarization/")