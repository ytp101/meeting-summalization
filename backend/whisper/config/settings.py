"""
Whisper Service Configuration Module.

This module sets up environment variables and hardware configurations
for initializing and running the Whisper ASR model. It supports 
Hugging Face model caching, hardware detection (GPU/CPU), and model parameters.

Key Configurations:
- HF_HOME: Custom Hugging Face model cache directory.
- MODEL_ID: Identifier for the Whisper model to be used.
- LANGUAGE: Default transcription language.
- REQUEST_TIMEOUT: Timeout limit for processing a request.
- DEVICE: Automatically detects and sets computation device (GPU or CPU).
- DTYPE: Chooses float16 when GPU is available for performance.

Dependencies:
- pathlib
- os
- torch

Typical usage:
    from whisper.config.settings import DEVICE, DTYPE, MODEL_ID
"""

from pathlib import Path 
import os 
import torch

# Hugging Face cache directory
HF_HOME = Path(os.getenv("HF_HOME", "/home/app/.cache"))
HF_HOME.mkdir(parents=True, exist_ok=True)
os.environ["HF_HOME"] = str(HF_HOME)

# Whisper model configuration
MODEL_ID = os.getenv("MODEL_ID", "openai/whisper-large-v3-turbo")
LANGUAGE = os.getenv("LANGUAGE", "en")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 1200))

# Hardware configuration
DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if torch.cuda.is_available() else torch.float32
