"""
Healthcheck Endpoint
--------------------

This module provides a lightweight `/health` route used for liveness and readiness checks.

It is designed for:
- Monitoring probes (e.g., uptime checkers, Docker/Kubernetes health checks)
- CI/CD sanity validation
- General system diagnostics

The endpoint returns HTTP 200 with a simple JSON payload when the server is responsive.

Example response:
    {
        "status": "ok"
    }

Author: yodsran
"""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])

@router.get("/health")
def healthcheck():
    """
    Healthcheck endpoint to verify the service is alive.

    Returns:
        dict: {"status": "ok"} if service is reachable.
    """
    return {"status": "ok"}
