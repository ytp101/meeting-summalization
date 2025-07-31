"""
routers/root.py – Basic root endpoint to confirm the API is up.

Useful for quick health pings or basic load balancer checks.
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/", tags=["health"])
def root():
    """
    Root endpoint that confirms the VAD API is running.

    Returns:
        JSON response:
        - status (str): "running"
    """
    return {"status": "running"}
