"""
Module: routers/healthcheck.py

Purpose:
Defines the healthcheck endpoint for the audio preprocessing service.
This route verifies the availability of required dependencies, 
specifically the presence and accessibility of FFmpeg in the runtime environment.

Author: yodsran
"""

from fastapi import APIRouter
from utils.ffmpeg_checker import is_ffmpeg_available

router = APIRouter()

@router.get("/healthcheck", summary="Dependency health check")
async def healthcheck():
    """
    Perform a runtime health check to validate FFmpeg availability.

    Returns:
        dict: A status indicator showing whether the required dependencies 
              (e.g., FFmpeg) are functional.

    Response Example:
        {
            "status": "healthy"
        }
    """
    ok = await is_ffmpeg_available()
    return {"status": "healthy" if ok else "unhealthy"}
