"""
models/vad.py – Pydantic models for VAD request and response payloads.
Defines input/output schemas used by the /vad API endpoint.
"""

from pydantic import BaseModel
from typing import List

class Segment(BaseModel):
    """
    Segment represents a single speech region detected by the VAD pipeline.

    Attributes:
        chunk_id (int): The sequential index of the detected chunk.
        start (float): Start time of the segment in seconds.
        end (float): End time of the segment in seconds.
    """
    chunk_id: int
    start: float
    end: float

class VADResponse(BaseModel):
    """
    VADResponse wraps the list of speech segments detected in the input audio.

    Attributes:
        segments (List[Segment]): List of detected voice activity segments.
    """
    segments: List[Segment]
