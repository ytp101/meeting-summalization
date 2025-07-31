"""
Root Router for Whisper ASR Service.

This module defines the root-level FastAPI route used to confirm that the
Whisper service is up and running. It provides basic service status and
metadata such as the active model ID.

Routes:
- GET / : Returns a JSON payload indicating service status and model in use.

Response Example:
    {
        "status": "running",
        "model": "openai/whisper-large-v3-turbo"
    }

Dependencies:
- whisper.config.settings: Provides current model configuration (MODEL_ID).
"""

from fastapi import APIRouter 
from whisper.config.settings import MODEL_ID

router = APIRouter() 

@router.get("/", summary="Service status")
def root():
    return {"status": "running", "model": MODEL_ID}
