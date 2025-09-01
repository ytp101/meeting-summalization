from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from gateway.utils.progress import publish, stream

router = APIRouter()


@router.get("/progress/stream/{task_id}")
async def progress_stream(task_id: str):
    return StreamingResponse(stream(task_id), media_type="text/event-stream")


@router.post("/progress/{task_id}")
async def progress_post(task_id: str, req: Request):
    payload = await req.json()
    await publish(task_id, payload)
    return {"ok": True}

