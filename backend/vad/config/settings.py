"""
config.py – Environment variable loader and global constants

This module:
- Loads Hugging Face token (HF_TOKEN) for authenticated model access
- Reads FastAPI server port (PORT)
- Logs any critical configuration errors
"""

import os

# ─── Hugging Face Token ─────────────────────────────────────────────
def get_hf_token() -> str: 
    token = os.getenv("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN must be set to load the VAD model.")
    return token

# ─── API Port ───────────────────────────────────────────────────────
PORT = int(os.getenv("PORT", 8002))
