"""
diarization.config.settings

This module handles environment-based configuration for the speaker diarization service.
It reads and validates essential environment variables required to initialize and run the pipeline.

Key responsibilities:
- Load Hugging Face access token
- Define model identifier
- Set default port for the FastAPI app
- Select appropriate device (CUDA or CPU)

Raises:
    RuntimeError: If HF_TOKEN is not set in the environment.
"""

import os
import torch
from diarization.utils.logger import logger

# Hugging Face access token (must be set via ENV)
HF_TOKEN: str = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    logger.error("HF_TOKEN environment variable is not set")
    raise RuntimeError("HF_TOKEN environment variable is required")

# Model ID for diarization (default: pyannote/speaker-diarization-3.1)
DIARIZATION_MODEL: str = os.getenv("DIARIZATION_MODEL", "pyannote/speaker-diarization-3.1")

# Device to run inference on: 'cuda' if available, otherwise 'cpu'
DEVICE: str = os.getenv("DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
