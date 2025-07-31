"""
Gateway Service Root Router Module

This module defines the root endpoint for the API Gateway Service.
It provides a simple health indicator for the gateway itself.

Endpoints:
- GET `/`: Returns a JSON object indicating that the gateway service is running.

Usage:
Import the router into the main application to include the root endpoint:

```python
from gateway.routers.root import router as root_router
app.include_router(root_router)
```

Response Model:
- `status` (str): Always returns "gateway running" to confirm service availability.
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/", response_model=dict)
def root() -> dict:
    """
    Root endpoint for the API Gateway Service.

    Returns:
        dict: {"status": "gateway running"}
    """
    return {"status": "gateway running"}
