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
from contextlib import asynccontextmanager

from summarization.routers import root, healthcheck, summarize
from summarization.services.ollama_client import health_check
from summarization.utils.logger import logger

# ─── Lifespan Event ────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI): 
    """
    Startup/shutdown logic for the FastAPI application.

    - Confirms Ollama service is reachable.
    - Logs lifecycle events for observability.
    """
    health = await health_check()
    if health["status"] == "healthy":
        logger.info("✅ Ollama is available and ready.")
    else:
        logger.warning("⚠️ Ollama service issue: %s", health)

    yield

    logger.info("🛑 Shutting down Summarization Service")

# ─── FastAPI App Initialization ────────────────────────────────────────────────
app = FastAPI(
    title="Meeting Summarization Service",
    description="API for generating meeting summaries from transcripts using LLMs.",
    version="1.0.0",
    lifespan=lifespan
)

# ─── Route Registration ────────────────────────────────────────────────────────
app.include_router(root.router)
app.include_router(healthcheck.router)
app.include_router(summarize.router)
