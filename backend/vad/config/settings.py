"""
config.py – Environment variable loader and global constants

This module:
- Loads Hugging Face token (HF_TOKEN) for authenticated model access
- Reads FastAPI server port (PORT)
- Logs any critical configuration errors
"""

import os
from utils.logger import logger

# ─── Hugging Face Token ─────────────────────────────────────────────
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    logger.error("HF_TOKEN environment variable is missing.")
    raise RuntimeError("HF_TOKEN must be set to load the VAD model.")

# ─── API Port ───────────────────────────────────────────────────────
PORT = int(os.getenv("PORT", 8002))
