from __future__ import annotations

import asyncio
import inspect
from typing import Any, Dict, List

from .progress import tqdm as _tqdm

__all__ = [
    "POLICIES",
    "build_hf_asr_kwargs",
    "safe_asr_call",
    "asr_with_policy_ladder",
]


# Memory policy ladder (keeps model loaded; trades throughput for VRAM)
POLICIES: Dict[str, Dict[str, Any]] = {
    "standard": {"batch_size": 2, "chunk_length_s": 20, "stride_length_s": (5.0, 5.0)},
    "tight":    {"batch_size": 1, "chunk_length_s": 10, "stride_length_s": (2.0, 2.0)},
    "ultra":    {"batch_size": 1, "chunk_length_s": 6,  "stride_length_s": (1.5, 1.5), "return_timestamps": True},
}


def _merge_kwargs(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    out.update(overrides)
    return out


def build_hf_asr_kwargs(model, batch_len: int, language: str | None = "th") -> Dict[str, Any]:
    """
    Build kwargs for transformers.AutomaticSpeechRecognitionPipeline with feature-gating
    for args that may not exist in older versions.
    """
    ck: Dict[str, Any] = {
        "return_timestamps": "word",            # falls back to True if unsupported
        "chunk_length_s": 20,                   # 15–30 works well
        "stride_length_s": (5.0, 5.0),
        "batch_size": max(1, min(8, batch_len)),
        "generate_kwargs": {
            "language": str(language) if language else None,  # None => auto-detect
            "task": "transcribe",
            "temperature": 0.0,
        },
    }
    try:
        sig = inspect.signature(model.__call__)
        if "condition_on_prev_text" in sig.parameters:
            ck["condition_on_prev_text"] = False
    except Exception:
        pass
    return ck


async def safe_asr_call(model, batched: List[dict], call_kwargs: Dict[str, Any]):
    """
    Robustly call the HF ASR pipeline:
      • If TypeError mentions an unexpected kwarg, drop it and retry.
      • Fallback 'return_timestamps'='word' -> True on older versions.
    """
    try:
        return await asyncio.to_thread(model, batched, **call_kwargs)
    except TypeError as e:
        msg = str(e)
        if "condition_on_prev_text" in msg:
            call_kwargs = dict(call_kwargs)
            call_kwargs.pop("condition_on_prev_text", None)
            return await asyncio.to_thread(model, batched, **call_kwargs)
        if "return_timestamps" in msg and call_kwargs.get("return_timestamps") == "word":
            call_kwargs = dict(call_kwargs)
            call_kwargs["return_timestamps"] = True
            return await asyncio.to_thread(model, batched, **call_kwargs)
        raise


async def asr_with_policy_ladder(model, batched: List[dict], base_kwargs: Dict[str, Any]) -> List[dict]:
    """Run the ASR pipeline using a VRAM-friendly policy ladder with fallbacks."""
    import torch as _t
    # 0) Standard
    try:
        kw = _merge_kwargs(base_kwargs, POLICIES["standard"])
        outs = await safe_asr_call(model, batched, kw)
        return outs if isinstance(outs, list) else [outs]
    except _t.cuda.OutOfMemoryError:
        _t.cuda.empty_cache()
    # 1) Tight
    try:
        kw = _merge_kwargs(base_kwargs, POLICIES["tight"])
        outs = await safe_asr_call(model, batched, kw)
        return outs if isinstance(outs, list) else [outs]
    except _t.cuda.OutOfMemoryError:
        _t.cuda.empty_cache()
    # 2) Ultra
    try:
        kw = _merge_kwargs(base_kwargs, POLICIES["ultra"])
        outs = await safe_asr_call(model, batched, kw)
        return outs if isinstance(outs, list) else [outs]
    except _t.cuda.OutOfMemoryError:
        _t.cuda.empty_cache()
    # 3) Sequentialized ultra (last resort)
    results: List[dict] = []
    kw = _merge_kwargs(base_kwargs, POLICIES["ultra"])
    for item in _tqdm(batched, desc="ASR ultra seq", unit="seg"):
        try:
            out_i = await safe_asr_call(model, [item], kw)
            results.extend(out_i if isinstance(out_i, list) else [out_i])
        except _t.cuda.OutOfMemoryError:
            _t.cuda.empty_cache()
            safer = dict(kw, chunk_length_s=5, stride_length_s=(1.0, 1.0))
            out_i = await safe_asr_call(model, [item], safer)
            results.extend(out_i if isinstance(out_i, list) else [out_i])
    return results

