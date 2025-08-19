"""
settings.py
-----------

This configuration module centralizes all environment-dependent settings
for the summarization service or its microservices (e.g., healthcheck).

Environment variables are loaded using Python's `os.getenv()` with defaults
to ensure robustness in both development and production environments.

Settings:
- OLLAMA_HOST: URL of the Ollama inference server.
- MODEL_ID: Model name to be used for summarization or healthcheck.
- SYSTEM_PROMPT: Base system prompt prepended before transcript input.
- MAX_TOKENS: Max token limit for model prediction.
- TEMPERATURE: Controls randomness of model output.
- REQUEST_TIMEOUT: Request timeout for Ollama API (in seconds).

Usage:
    from config.settings import MODEL_ID, OLLAMA_HOST

These constants are intended to be imported wherever runtime config is needed.

Author:
    yodsran
"""

import os

OLLAMA_HOST    = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_ID       = os.getenv("MODEL_ID", "llama3")
SYSTEM_PROMPT  = os.getenv("SYSTEM_PROMPT", "Summarize the following transcript in a concise, structured format.")
MAX_TOKENS     = int(os.getenv("MAX_TOKENS", 4096))
TEMPERATURE    = float(os.getenv("TEMPERATURE", 0.2))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 300))

# 2 pass .env 
PASS1_MODEL = "meta-llama/Llama-3.1-8B-Instruct"
PASS2_MODEL = "Qwen/Qwen2.5-14B-Instruct-AWQ"