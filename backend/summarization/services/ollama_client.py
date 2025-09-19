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
from summarization.config.settings import (
    TEMPERATURE,
    REQUEST_TIMEOUT
)

class OllamaChat: 
    def __init__(self, base_url: str, model: str): 
        self.base_url = base_url.rstrip('/')
        self.model = model
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=REQUEST_TIMEOUT)

    async def chat(self, system: str, user: str, max_tokens: int = 1024) -> str:
        """
        Send a chat message to the Ollama model and return the response.

        Args:
            system (str): System prompt for the model.
            user (str): User input message.
            max_tokens (int): Maximum tokens for the response.

        Returns:
            str: Model's response text.
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "options": {
                "temperature": TEMPERATURE,
                "top_p": 0.9,
                "num_predict": max_tokens,
            },
            "stream": False
        }
        resp = await self._client.post("/api/chat", json=payload) 
        resp.raise_for_status()  # Raise for HTTP errors
        data = resp.json() 
        return data.get("message", {}).get("content", "").strip()
    
    async def aclose(self):
        await self._client.aclose()