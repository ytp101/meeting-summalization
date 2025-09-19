"""
main.py
-------

Entrypoint for the Meeting Summarization Service.

Responsibilities:
- Initializes the FastAPI app with metadata and startup lifecycle hooks.
- Verifies Ollama backend availability on startup via `health_check()`.
- Registers all API routers: root ("/"), healthcheck ("/healthcheck"), and summarization ("/summarization").

Lifespan:
- On startup: Logs backend model availability.
- On shutdown: Logs service termination.

Author:
    yodsran
"""

from fastapi import FastAPI
from summarization.routers import root, summarize

# ─── FastAPI App Initialization ────────────────────────────────────────────────
app = FastAPI(
    title="Meeting Summarization Service",
    description="API for generating meeting summaries from transcripts using LLMs.",
    version="1.0.0",
)

# ─── Route Registration ────────────────────────────────────────────────────────
app.include_router(root.router)
app.include_router(summarize.router)