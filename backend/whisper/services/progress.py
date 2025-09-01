from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

__all__ = ["tqdm", "post_progress", "map_progress"]

try:  # Optional tqdm progress bars (no-op fallback if not installed)
    from tqdm.auto import tqdm  # type: ignore
except Exception:  # pragma: no cover - graceful fallback
    def tqdm(x, *args, **kwargs):  # type: ignore
        return x

# Lightweight async progress POST using requests in a thread (no httpx dep)
def _post_sync(url: str, payload: Dict[str, Any]) -> None:
    try:
        import requests  # lazy import
        requests.post(url, json=payload, timeout=3.0)
    except Exception:
        pass

async def post_progress(url: Optional[str], payload: Dict[str, Any]) -> None:
    if not url:
        return
    await asyncio.to_thread(_post_sync, url, payload)

def map_progress(done: int, total: int, pmin: float, pmax: float) -> float:
    if total <= 0:
        return float(pmin)
    frac = max(0.0, min(1.0, float(done) / float(total)))
    return float(pmin) + frac * (float(pmax) - float(pmin))
