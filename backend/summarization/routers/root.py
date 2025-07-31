"""
root.py
-------

This module provides the base route (`/`) for the summarization microservice.

Purpose:
- Acts as a liveness probe for infrastructure and sanity checks.
- Confirms the service is running and shows the active model in use.

This is typically used by load balancers, orchestrators (e.g., Kubernetes),
or humans checking service availability.

Route:
    GET /  →  Returns service status and model ID.

Author:
    yodsran
"""

from fastapi import APIRouter
from summarization.config.settings import MODEL_ID

router = APIRouter()

@router.get("/", summary="Liveness check")
def root():
    """
    Basic liveness endpoint to confirm service is running.

    Returns:
        dict: Contains service status and currently active model ID.
    """
    return {"status": "summarization running", "model": MODEL_ID}
