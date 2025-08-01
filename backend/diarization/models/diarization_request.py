"""
diarization.models.schemas

Defines request and response models for the diarization API.
These models are used for validation, documentation, and serialization.
"""

from pydantic import BaseModel, Field

class DiarizationRequest(BaseModel):
    """
    Schema for diarization request payload.

    Attributes:
        audio_path (str): Absolute or relative file path to a WAV audio file
                          to be processed by the diarization pipeline.
                          Must be accessible by the backend.
    """
    audio_path: str = Field(..., example="/path/to/audio.wav", description="Full path to a WAV audio file")
