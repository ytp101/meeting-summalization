from datetime import datetime, timezone
from uuid import uuid4
import httpx
from fastapi import HTTPException

from gateway.utils.logger import logger
from gateway.config.settings import REQUEST_TIMEOUT

def generate_task_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    uid = uuid4().hex
    return f"{ts}_{uid}"

async def call_service(client: httpx.AsyncClient, name: str, url: str, payload: dict) -> dict:
    try:
        logger.info(f"[{name}] → {url} payload={payload}")
        resp = await client.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"[{name}] HTTP {e.response.status_code}: {e.response.text}")
        raise HTTPException(500, f"{name} failed: {e.response.text}")
    except httpx.TimeoutException:
        logger.error(f"[{name}] timed out after {REQUEST_TIMEOUT}s")
        raise HTTPException(504, f"{name} timed out")
    except Exception as e:
        logger.error(f"[{name}] error: {e}")
        raise HTTPException(500, f"{name} error: {e}")