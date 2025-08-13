"""
Pydantic Response Schemas for Whisper Transcription Service.

This module defines structured output models returned by the transcription service,
including word-level segments with optional speaker labeling and output file path metadata.

Classes:
- WordSegment: Represents a single word or phrase segment with start/end time, optional speaker, and transcribed text.
- TranscriptionResponse: Represents the response payload containing the transcription output file path.

Typical Usage:
    response = TranscriptionResponse(
        transcription_file_path="/outputs/meeting_audio.txt"
    )

    word = WordSegment(
        start=0.0,
        end=1.2,
        speaker="A",
        text="Hello"
    )
"""

from pydantic import BaseModel
from typing import Optional

class WordSegment(BaseModel):
    start: float
    end: float
    speaker: Optional[str]
    text: str

class TranscriptionResponse(BaseModel):
    transcription_file_path: str
    word_segmnts_path: Optional[str] = None 
    utterances_path: Optional[str] = None