from fastapi import APIRouter 
from whisper.config.settings import DEVICE
from whisper.utils.load_model import is_model_loaded

router = APIRouter()

@router.get("/healthcheck", summary="Healthcheck GPU & Model")
def healthcheck():
    return {"model_loaded": is_model_loaded(), "gpu_available": str(DEVICE)}