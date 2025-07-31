"""
healthcheck.py
--------------

This FastAPI router handles the `/healthcheck` endpoint for the summarization service.

It delegates health validation to the `check_model_health()` function, which verifies
the connectivity and availability of the Ollama backend and ensures the target model
is registered and ready.

This endpoint is useful for container orchestration (e.g., readiness probes),
monitoring tools, or health dashboards to ensure model infrastructure is operational.

Route:
    GET /healthcheck  →  Returns model availability status and metadata.

Author:
    yodsran
"""

from fastapi import APIRouter
from summarization.services.ollama_client import health_check

router = APIRouter()

@router.get("/healthcheck", summary="Model health check")
async def healthcheck():
    """
    Check the availability of the configured Ollama model.

    Returns:
        JSON dict with health status (healthy, degraded, or unhealthy),
        and model identifier if applicable.
    """
    return await health_check()
