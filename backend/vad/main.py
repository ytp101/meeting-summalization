"""
main.py – FastAPI app entrypoint for the Voice Activity Detection (VAD) service.

Includes:
- Lifespan context for model loading
- Routing setup
- Startup initialization for VAD model
"""

# TODO: write unit test 
# TODO: write README.md

from contextlib import asynccontextmanager
from fastapi import FastAPI

from routers import root, healthcheck, vad  
from services.vad_service import load_vad_model
from utils.logger import logger  # Use logger instead of print

# ─── Lifespan startup/shutdown logic ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI): 
    logger.info("🚀 Loading VAD model...")
    await load_vad_model()
    logger.info("✅ VAD model ready")
    yield

# ─── FastAPI Initialization ───────────────────────────────────────────────────────
app = FastAPI(
    title="Voice Activity Detection Service",
    lifespan=lifespan
)

# ─── Route Registration ──────────────────────────────────────────────────────────
app.include_router(root.router)
app.include_router(healthcheck.router)
app.include_router(vad.router)