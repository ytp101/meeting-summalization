from pydantic import BaseModel
from typing import Optional

class WordSegment(BaseModel):
    start: float
    end: float
    speaker: Optional[str]
    text: str

class TranscriptionResponse(BaseModel):
    transcription_file_path: str