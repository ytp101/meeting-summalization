"""
routers/healthcheck.py – Health check endpoint for VAD service.

This route allows external systems (e.g., load balancers, uptime monitors)
to verify whether the VAD pipeline model has been successfully loaded and is ready.
"""

from fastapi import APIRouter
from services.vad_service import vad_pipeline

router = APIRouter()

@router.get("/healthcheck", tags=["health"])
def healthcheck():
    """
    Returns the health status of the VAD service.

    - "healthy" if the VAD model is loaded and ready
    - "unhealthy" if the pipeline has not yet been initialized

    Returns:
        JSON response with keys:
        - status (str): "healthy" or "unhealthy"
        - model_loaded (bool): True if model is initialized
    """
    ready = vad_pipeline is not None
    return {"status": "healthy" if ready else "unhealthy", "model_loaded": ready}
