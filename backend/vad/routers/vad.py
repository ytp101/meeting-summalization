"""
services/vad_service.py – VAD pipeline loader and inference runner.

This module loads the Hugging Face PyAnnote VAD pipeline and provides
an async-safe function to perform inference on audio files in a
FastAPI-compatible way.
"""

import asyncio
from pyannote.audio import Pipeline as PyannotePipeline
from config.settings import HF_TOKEN

# Global VAD pipeline instance
vad_pipeline = None

async def load_vad_model():
    """
    Asynchronously load the PyAnnote VAD model from Hugging Face Hub
    using the provided HF_TOKEN. This should be called during FastAPI startup.

    Raises:
        Exception if model loading fails.
    """
    global vad_pipeline
    vad_pipeline = await asyncio.to_thread(
        PyAnnotePipeline.from_pretrained,
        "pyannote/voice-activity-detection",
        use_auth_token=HF_TOKEN
    )

async def run_vad_on_file(file_path: str):
    """
    Asynchronously run VAD inference on the given audio file.

    Args:
        file_path (str): Absolute path to the .wav audio file.

    Returns:
        pyannote.core.Annotation: Resulting timeline of speech segments.

    Raises:
        RuntimeError: If the pipeline has not been loaded.
        Any: If model inference fails.
    """
    if vad_pipeline is None:
        raise RuntimeError("VAD pipeline not loaded.")
    return await asyncio.to_thread(vad_pipeline, file_path)
