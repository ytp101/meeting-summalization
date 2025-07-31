"""
Gateway Service Utilities Module

This module provides common utility functions for the API Gateway Service, including:

- **generate_task_id**: Generates a unique identifier for each processing task.
- **call_service**: Sends HTTP POST requests to downstream microservices with structured logging,
  timeout management, and error handling.

Dependencies:
- `REQUEST_TIMEOUT` from gateway.config.settings for HTTP request timeouts.
- `logger` from gateway.utils.logger for consistent logging.

Exceptions:
- Raises `HTTPException` with appropriate status codes on HTTP errors, timeouts, or unexpected failures.
"""
from datetime import datetime, timezone
from uuid import uuid4

import httpx
from fastapi import HTTPException

from gateway.utils.logger import logger
from gateway.config.settings import REQUEST_TIMEOUT


def generate_task_id() -> str:
    """
    Generate a unique task identifier combining a UTC timestamp and a UUID.

    Returns:
        str: A string in the format "YYYYMMDDHHMMSS_<uuidhex>" for tracking tasks.
    """
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    uid = uuid4().hex
    task_id = f"{ts}_{uid}"
    logger.info(f"Generated task_id: {task_id}")
    return task_id


async def call_service(
    client: httpx.AsyncClient,
    name: str,
    url: str,
    payload: dict
) -> dict:
    """
    Invoke a downstream microservice via HTTP POST, with logging and error handling.

    Args:
        client (httpx.AsyncClient): The HTTP client to use for requests.
        name (str): Logical name of the service (for logging).
        url (str): Endpoint URL of the microservice.
        payload (dict): JSON-serializable payload to send in the request body.

    Returns:
        dict: Parsed JSON response from the microservice.

    Raises:
        HTTPException: 500 on HTTP errors or unexpected exceptions.
        HTTPException: 504 on request timeout.
    """
    try:
        logger.info(f"[{name}] POST {url} payload={payload}")
        response = await client.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        logger.info(f"[{name}] Success: received response")
        return data

    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        text = e.response.text
        logger.error(f"[{name}] HTTP {status_code}: {text}")
        raise HTTPException(status_code=500, detail=f"{name} failed: {text}")

    except httpx.TimeoutException:
        logger.error(f"[{name}] timed out after {REQUEST_TIMEOUT}s")
        raise HTTPException(status_code=504, detail=f"{name} timed out")

    except Exception as e:
        logger.error(f"[{name}] unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"{name} error: {e}")
