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
    filename: str                           # Absolute path to input audio (e.g., .opus/.wav)
    output_dir: str
    segments: Optional[List[DiarSegment]] = None  # Precomputed diarization segments
    # Optional progress streaming fields (gateway orchestrated)
    task_id: Optional[str] = None
    progress_url: Optional[str] = None
    progress_min: Optional[float] = None
    progress_max: Optional[float] = None
