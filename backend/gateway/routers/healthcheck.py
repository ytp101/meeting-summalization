"""
Gateway Service Healthcheck Router Module

This module defines the `/healthcheck` endpoint for the API Gateway Service.
It performs runtime checks against downstream microservices to determine their availability.

Responsibilities:
- Define the FastAPI router for healthcheck operations.
- Aggregate status results of the following services:
  - Preprocessing
  - Speaker Diarization
  - Whisper ASR
  - Summarization
- Serialize responses using the ServiceStatus Pydantic model.

Usage:
Import the router into the main application to include the healthcheck endpoint:

```python
from gateway.routers.healthcheck import router as health_router
app.include_router(health_router)
```

Environment Variables:
Service base URLs and timeout values are managed in `gateway.config.settings`.
"""
from fastapi import APIRouter
import httpx

from gateway.models.service_status import ServiceStatus
from gateway.config.settings import (
    PREPROCESS_URL,
    DIAR_URL,
    WHISPER_URL,
    SUMMARIZE_URL,
    REQUEST_TIMEOUT,
)

router = APIRouter()

@router.get("/healthcheck", response_model=list[ServiceStatus])
async def healthcheck() -> list[ServiceStatus]:
    """
    Healthcheck endpoint for downstream microservices.

    Iterates through each configured service URL, issues a GET request,
    and interprets the response status.

    Returns:
        List[ServiceStatus]: A list of service status objects indicating:
            - `service`: microservice name.
            - `status`: "up" if HTTP 200, otherwise "down" or error code.
            - `message`: Optional detail on failures.
    """
    services = [
        ("preprocess", PREPROCESS_URL.replace("/preprocess/", "/")),
        ("diarization", DIAR_URL.replace("/diarization/", "/")),
        ("whisper", WHISPER_URL.replace("/whisper/", "/")),
        ("summarization", SUMMARIZE_URL.replace("/summarization/", "/")),
    ]
    results: list[ServiceStatus] = []

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        for name, check_url in services:
            status = "down"
            message = ""
            try:
                response = await client.get(check_url)
                if response.status_code == 200:
                    status = "up"
                else:
                    status = f"error {response.status_code}"
                    message = response.text
            except Exception as e:
                status = "down"
                message = str(e)

            results.append(
                ServiceStatus(service=name, status=status, message=message)
            )

    return results
