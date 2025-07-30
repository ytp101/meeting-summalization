from pydantic import BaseModel
from typing import Optional, List

class DiarSegment(BaseModel):
    start: float
    end: float
    speaker: Optional[str] = None

class TranscribeRequest(BaseModel):
    filename: str                           # WAV filename (without extension)
    output_dir: str                     
    segments: Optional[List[DiarSegment]] = None  # Precomputed diarization segments