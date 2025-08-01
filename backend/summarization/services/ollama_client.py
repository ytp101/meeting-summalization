"""
ollama_client.py
----------------

This module provides utility functions to interact with the Ollama LLM backend API.

Functions:
- call_ollama(): Sends a summarization prompt to the Ollama model and returns the output.
- health_check(): Verifies if the configured model is registered and reachable.

These functions are reused across API routes for both summarization and service monitoring.

Author:
    yodsran
"""

import httpx
from fastapi import HTTPException
from summarization.utils.logger import logger
from summarization.config.settings import (
    OLLAMA_HOST,
    MODEL_ID,
    SYSTEM_PROMPT,
    MAX_TOKENS,
    TEMPERATURE,
    REQUEST_TIMEOUT
)

async def call_ollama(transcript: str) -> str:
    """
    Call the Ollama LLM model to summarize a transcript.

    Args:
        transcript (str): Raw transcript text to summarize.

    Returns:
        str: Model-generated summary text.

    Raises:
        HTTPException: If the model fails or returns an error response.
    """
    payload = {
        "model": MODEL_ID,
        "prompt": f"{SYSTEM_PROMPT}\n\n{transcript}",
        "stream": False,
        "options": {
            "num_predict": MAX_TOKENS,
            "temperature": TEMPERATURE,
            "context_window": 8192
        }
    }
    url = f"{OLLAMA_HOST}/api/generate"

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.post(url, json=payload)

    if resp.status_code != 200:
        logger.error("❌ Ollama error %d: %s", resp.status_code, resp.text)
        raise HTTPException(status_code=500, detail="Ollama API error")

    data = resp.json()
    return data.get("response") or (data.get("choices") or [{}])[0].get("text", "")


async def health_check() -> dict:
    """
    Check the availability of the Ollama model backend.

    Returns:
        dict: Health status object with status and model info.
            Example:
                {
                    "status": "healthy",
                    "model": "llama3"
                }

    Fallbacks:
        - "degraded" if Ollama is reachable but model is missing.
        - "unhealthy" if network or API call fails.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_HOST}/api/tags")

        if resp.status_code != 200:
            return {"status": "degraded", "ollama": f"error {resp.status_code}"}

        models = resp.json().get("models", [])
        ok = any(m.get("name") == MODEL_ID for m in models)

        return {"status": "healthy" if ok else "degraded", "model": MODEL_ID}

    except Exception as e:
        logger.exception("❌ Ollama health check failed")
        return {"status": "unhealthy", "error": str(e)}
