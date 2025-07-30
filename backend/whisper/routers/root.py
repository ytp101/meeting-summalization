from fastapi import APIRouter 
from whisper.config.settings import MODEL_ID

router = APIRouter() 

@router.get("/", summary="Service status")
def root():
    return {"status": "running", "model": MODEL_ID}
