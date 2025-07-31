"""
Healthcheck Router for Whisper ASR Service.

This module provides a FastAPI route to check the operational status of the
Whisper model and the availability of GPU acceleration. Useful for monitoring,
debugging, and automated service validation in production deployments.

Routes:
- GET /healthcheck: Returns JSON indicating model load status and GPU availability.

Response Example:
    {
        "model_loaded": true,
        "gpu_available": "cuda:0"
    }

Dependencies:
- whisper.config.settings: For device info (CPU/GPU).
- whisper.utils.load_model: For model load status.
"""

from fastapi import APIRouter 
from whisper.config.settings import DEVICE
from whisper.utils.load_model import is_model_loaded

router = APIRouter()

@router.get("/healthcheck", summary="Healthcheck GPU & Model")
def healthcheck():
    return {"model_loaded": is_model_loaded(), "gpu_available": str(DEVICE)}
