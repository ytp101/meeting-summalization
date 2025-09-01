from __future__ import annotations

import asyncio
import inspect
import os
from typing import Any, Dict, List, Tuple

import numpy as _np
import torch as _t
import soundfile as _sf

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

def _load_audio(path: str) -> Tuple[_np.ndarray, int]:
    """Read audio file at native rate -> mono float32 numpy array, sampling_rate."""
    audio, sr = _sf.read(path, always_2d=False)
    if audio.ndim == 2:  # stereo -> mono
        audio = _np.mean(audio, axis=1)
    # cast to float32 in [-1, 1]
    if audio.dtype != _np.float32:
        audio = audio.astype(_np.float32, copy=False)
    return audio, int(sr)

def _dict_get(d: Dict[str, Any], *names, default=None):
    for n in names:
        if n in d and d[n] is not None:
            return d[n]
    return default

def _coerce_one_to_hf(item: Any, default_sr: int | None) -> Dict[str, Any]:
    """
    Normalize various input shapes to HF-required {"raw": np/torch, "sampling_rate": int}.
    Supported:
      - str/Path -> load file
      - torch.Tensor / np.ndarray (requires default_sr)
      - dict with variants: {"raw", "sampling_rate"} (pass-through),
        or {"array"/"audio"/"waveform": ..., "sr"/"rate"/"sampling_rate": ...},
        or {"path": ...} / {"file": ...}
    """
    # Already correct shape
    if isinstance(item, dict) and "raw" in item and "sampling_rate" in item:
        return {"raw": item["raw"], "sampling_rate": int(item["sampling_rate"])}

    # File-like inputs
    if isinstance(item, (str, os.PathLike)):
        raw, sr = _load_audio(str(item))
        return {"raw": raw, "sampling_rate": sr}

    if isinstance(item, dict):
        # file path inside dict
        path = _dict_get(item, "path", "file", "filename")
        if path:
            raw, sr = _load_audio(str(path))
            return {"raw": raw, "sampling_rate": sr}

        # waveform + sr variants
        raw = _dict_get(item, "array", "audio", "waveform", "raw")
        sr = _dict_get(item, "sr", "rate", "sampling_rate")
        if raw is not None and sr is not None:
            # ensure correct dtype/shape
            if isinstance(raw, _t.Tensor):
                raw = raw.detach().cpu().numpy()
            raw = _np.asarray(raw)
            if raw.ndim == 2:
                raw = raw.mean(axis=1).astype(_np.float32, copy=False)
            elif raw.dtype != _np.float32:
                raw = raw.astype(_np.float32, copy=False)
            return {"raw": raw, "sampling_rate": int(sr)}

    # Raw arrays/tensors (needs a sampling rate)
    if isinstance(item, _t.Tensor):
        if default_sr is None:
            raise ValueError("Tensor provided without sampling_rate; set default_sr.")
        return {"raw": item.detach().cpu().numpy().astype(_np.float32, copy=False), "sampling_rate": int(default_sr)}

    if isinstance(item, _np.ndarray):
        if default_sr is None:
            raise ValueError("ndarray provided without sampling_rate; set default_sr.")
        raw = item
        if raw.ndim == 2:
            raw = raw.mean(axis=1)
        if raw.dtype != _np.float32:
            raw = raw.astype(_np.float32, copy=False)
        return {"raw": raw, "sampling_rate": int(default_sr)}

    raise TypeError(f"Unsupported ASR input type: {type(item)!r}")

def _infer_default_sr(model) -> int | None:
    # Try to get the model’s preferred sampling rate (if available)
    for attr in ("feature_extractor", "processor"):
        obj = getattr(model, attr, None)
        if obj is not None:
            sr = getattr(obj, "sampling_rate", None)
            if isinstance(sr, int):
                return sr
    return None

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

async def asr_with_policy_ladder(model, batched: List[Any], base_kwargs: Dict[str, Any]) -> List[dict]:
    """Run the ASR pipeline using a VRAM-friendly policy ladder with fallbacks."""
    # Normalize inputs to {"raw": np/torch, "sampling_rate": int}
    default_sr = _infer_default_sr(model)
    batched = [_coerce_one_to_hf(x, default_sr) for x in batched]

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