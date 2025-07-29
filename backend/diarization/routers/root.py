from fastapi import APIRouter
from pydantic import BaseModel
from diarization.config.settings import DIARIZATION_MODEL, DEVICE

router = APIRouter()

class LivenessResponse(BaseModel):
    status: str
    model: str
    device: str

@router.get(
    "/",
    summary="Liveness check",
    response_model=LivenessResponse,
    tags=["Health"]
)
async def root():
    """
    Basic liveness check to confirm the service is up.
    Returns model name and device context.
    """
    return {
        "status": "running",
        "model": str(DIARIZATION_MODEL),
        "device": str(DEVICE)
    }
