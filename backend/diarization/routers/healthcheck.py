from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from diarization.utils.load_model import get_diarization_pipeline
from diarization.config.settings import DIARIZATION_MODEL, DEVICE

router = APIRouter()

class HealthcheckResponse(BaseModel):
    status: str
    message: str
    model: str
    device: str

@router.get(
    "/healthcheck",
    summary="Dependency health check",
    response_model=HealthcheckResponse,
    tags=["Health"]
)
async def healthcheck():
    """
    Verifies if the diarization pipeline is loaded and available.
    Returns model and device info if healthy.
    """
    try:
        get_diarization_pipeline()
        return JSONResponse(
            content={
                "status": "healthy",
                "message": "Diarization service is running",
                "model": DIARIZATION_MODEL,
                "device": DEVICE,
            },
            status_code=200
        )
    except Exception as e:
        return JSONResponse(
            content={
                "status": "unhealthy",
                "message": f"Diarization pipeline error: {str(e)}",
                "model": DIARIZATION_MODEL,
                "device": DEVICE,
            },
            status_code=503
        )
