"""
🎙️ vad_service.py — Voice Activity Detection (VAD) Service Layer

This module provides asynchronous utility functions to load and run a pre-trained
Voice Activity Detection (VAD) model from Hugging Face (`pyannote/voice-activity-detection`).

It serves as the backend inference layer for the FastAPI VAD microservice.

Dependencies:
- pyannote.audio
- asyncio
- Hugging Face token (HF_TOKEN) from config.settings

Usage:
- Call `load_vad_model()` at application startup
- Use `run_vad_on_file()` to infer VAD segments from a WAV file
"""

import asyncio
from pyannote.audio import Pipeline as PyannotePipeline

from vad.config.settings import get_hf_token

# Global pipeline instance
vad_pipeline = None

async def load_vad_model():
    """
    Load the VAD model from Hugging Face asynchronously and store it in a global variable.

    Raises:
        RuntimeError: If HF_TOKEN is invalid or model fails to load.
    """
    global vad_pipeline
    hf_token = get_hf_token
    vad_pipeline = await asyncio.to_thread(
        PyannotePipeline.from_pretrained,
        "pyannote/voice-activity-detection",
        use_auth_token=hf_token
    )

async def run_vad_on_file(file_path: str):
    """
    Run VAD inference on the given WAV file using the preloaded pipeline.

    Args:
        file_path (str): Full path to the WAV audio file.

    Returns:
        pyannote.core.Annotation: VAD result containing speech segment timestamps.

    Raises:
        RuntimeError: If the pipeline hasn't been loaded before calling.
    """
    if vad_pipeline is None:
        raise RuntimeError("VAD pipeline not loaded.")
    return await asyncio.to_thread(vad_pipeline, file_path)
