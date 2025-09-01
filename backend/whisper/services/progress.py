from __future__ import annotations

__all__ = ["tqdm"]

try:  # Optional tqdm progress bars (no-op fallback if not installed)
    from tqdm.auto import tqdm  # type: ignore
except Exception:  # pragma: no cover - graceful fallback
    def tqdm(x, *args, **kwargs):  # type: ignore
        return x

