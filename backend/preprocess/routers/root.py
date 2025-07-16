"""
Module: routers/root.py

Purpose:
Defines the root-level endpoint for the audio preprocessing service. 
Primarily used for confirming that the service is live and reachable. 
Intended for use in infrastructure health checks or uptime monitors.

Author: yodsran
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/", summary="Service live check")
def root():
    """
    Returns a basic status message to confirm the service is operational.

    Returns:
        dict: A simple status indicator confirming that the 
              audio preprocessing service is up.

    Example Response:
        {
            "status": "preprocess running"
        }
    """
    return {"status": "preprocess running"}
