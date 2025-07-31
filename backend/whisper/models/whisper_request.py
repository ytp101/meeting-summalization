"""
Pydantic Schemas for Whisper Transcription Service.

This module defines request and data models used by the transcription service.
These schemas ensure structured and validated input for handling audio
transcription jobs, optionally including speaker diarization data.

Classes:
- DiarSegment: Represents a diarization segment with start/end timestamps and optional speaker label.
- TranscribeRequest: Request model for initiating transcription, including file name, output directory, and optional diarization segments.

Usage Example:
    payload = TranscribeRequest(
        filename="meeting_audio",
        output_dir="/outputs/",
        segments=[
            DiarSegment(start=0.0, end=5.3, speaker="A"),
            DiarSegment(start=5.3, end=10.1, speaker="B")
        ]
    )
"""

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
