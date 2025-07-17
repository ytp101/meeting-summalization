"""
models/vad.py – Pydantic models for VAD request/response payloads.
"""

from pydantic import BaseModel

class VADRequest(BaseModel):
    """
    VADRequest defines the input schema for the /vad endpoint.
    
    Attributes:
        input_path (str): Full absolute path to the .wav audio file to analyze.
    """
    input_path: str  # Full path to the WAV audio file to process
