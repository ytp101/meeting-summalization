from __future__ import annotations

import asyncio
import json
import time
from typing import Any, AsyncIterator, Dict

# Simple in-memory progress bus keyed by task_id.
# One consumer per task_id is assumed (frontend page)

_queues: Dict[str, asyncio.Queue] = {}


def _get_queue(task_id: str) -> asyncio.Queue:
    if task_id not in _queues:
        _queues[task_id] = asyncio.Queue()
    return _queues[task_id]


async def publish(task_id: str, event: Dict[str, Any]) -> None:
    ev = dict(event)
    ev.setdefault("task_id", task_id)
    ev.setdefault("ts", time.time())
    await _get_queue(task_id).put(ev)


async def stream(task_id: str) -> AsyncIterator[bytes]:
    """Yield Server-Sent Events for a given task_id.
    Stream terminates only when a final event is received for this task
    (service=='gateway' & step=='done') or when an explicit 'final': True flag is sent.
    """
    q = _get_queue(task_id)
    # Initial hello to open the stream reliably
    yield b":ok\n\n"
    while True:
        ev = await q.get()
        data = json.dumps(ev, ensure_ascii=False)
        yield f"data: {data}\n\n".encode("utf-8")
        # Only end the stream on explicit final events
        if ev.get("final") is True:
            break
        if ev.get("service") == "gateway" and ev.get("step") == "done":
            break


def _reset(task_id: str) -> None:
    # For tests or reuse; not used in app flow.
    try:
        _queues.pop(task_id, None)
    except Exception:
        pass
