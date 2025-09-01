from __future__ import annotations

import asyncio
import inspect
import os
from typing import Any, Dict, List, Tuple

import numpy as _np
import torch as _t
import soundfile as _sf

from .progress import tqdm as _tqdm
from ..utils.logger import logger

__all__ = [
    "POLICIES",
    "build_hf_asr_kwargs",
    "safe_asr_call",
    "asr_with_policy_ladder",
]

# -------------------------
# Memory policy ladder
#   Tip: keep batch_size=1 while stabilizing schema; raise later if needed.
# -------------------------
POLICIES: Dict[str, Dict[str, Any]] = {
    "standard": {"batch_size": 1, "chunk_length_s": 20, "stride_length_s": (5.0, 5.0)},
    "tight":    {"batch_size": 1, "chunk_length_s": 10, "stride_length_s": (2.0, 2.0)},
    "ultra":    {"batch_size": 1, "chunk_length_s": 6,  "stride_length_s": (1.5, 1.5), "return_timestamps": True},
}

def _merge_kwargs(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    out.update(overrides)
    return out

# -------------------------
# I/O normalization helpers
# -------------------------
def _load_audio(path: str) -> Tuple[_np.ndarray, int]:
    """Read audio file -> mono float32 np.ndarray in [-1,1], and its sampling_rate."""
    audio, sr = _sf.read(path, always_2d=False)
    if getattr(audio, "ndim", 1) == 2:
        audio = _np.mean(audio, axis=1)
    if getattr(audio, "dtype", None) != _np.float32:
        audio = _np.asarray(audio, dtype=_np.float32)
    return audio, int(sr)

def _dict_get(d: Dict[str, Any], *names, default=None):
    for n in names:
        if n in d and d[n] is not None:
            return d[n]
    return default

def _finalize_raw_sr(raw: Any, sr: Any) -> Dict[str, Any]:
    """Return EXACT schema HF expects: {'raw': float32 mono np.ndarray, 'sampling_rate': int}."""
    if isinstance(raw, _t.Tensor):
        raw = raw.detach().cpu().numpy()
    raw = _np.asarray(raw)
    if getattr(raw, "ndim", 1) == 2:
        raw = raw.mean(axis=1)
    if raw.dtype != _np.float32:
        raw = raw.astype(_np.float32, copy=False)
    return {"raw": raw, "sampling_rate": int(sr)}

def _coerce_one_to_hf(item: Any, default_sr: int | None) -> Dict[str, Any]:
    """
    Normalize supported inputs into {'raw': np.float32 1D, 'sampling_rate': int}.
    Supports:
      - str/Path -> file load
      - torch.Tensor / np.ndarray / list -> needs default_sr
      - dict variants:
          * {'raw','sampling_rate'} (pass-through normalized)
          * {'array'/'audio'/'waveform','sr'/'rate'/'sampling_rate'}
          * {'path'/'file'/'filename'} -> load
          * shallow wrappers are handled by caller before passing here
    """
    # Already canonical
    if isinstance(item, dict) and "raw" in item and "sampling_rate" in item:
        return _finalize_raw_sr(item["raw"], item["sampling_rate"])

    # File path
    if isinstance(item, (str, os.PathLike)):
        raw, sr = _load_audio(str(item))
        return _finalize_raw_sr(raw, sr)

    # Dict variants
    if isinstance(item, dict):
        path = _dict_get(item, "path", "file", "filename")
        if path:
            raw, sr = _load_audio(str(path))
            return _finalize_raw_sr(raw, sr)

        raw = _dict_get(item, "raw", "array", "audio", "waveform", "values")
        sr  = _dict_get(item, "sampling_rate", "sr", "rate", "fs")
        if raw is not None and sr is not None:
            return _finalize_raw_sr(raw, sr)

    # Bare arrays/tensors/lists
    if isinstance(item, (_t.Tensor, _np.ndarray, list)):
        if default_sr is None:
            raise ValueError("Tensor/ndarray/list provided without sampling_rate; set default_sr.")
        return _finalize_raw_sr(item, default_sr)

    raise TypeError(f"Unsupported ASR input type: {type(item)!r}")

def _infer_default_sr(model) -> int | None:
    """Try to get pipeline's preferred sampling rate."""
    for attr in ("feature_extractor", "processor"):
        obj = getattr(model, attr, None)
        if obj is not None:
            sr = getattr(obj, "sampling_rate", None)
            if isinstance(sr, int):
                return sr
    return None

def _freeze_payload(canon: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Build the final, HF-proof payload with EXACT keys:
      [{'raw': np.float32 1D, 'sampling_rate': int}, ...]
    """
    return [_finalize_raw_sr(d["raw"], d["sampling_rate"]) for d in canon]

def _assert_payload(payload: List[Dict[str, Any]]) -> None:
    """Fail fast with actionable message if anything is malformed."""
    for i, it in enumerate(payload):
        if not isinstance(it, dict):
            raise ValueError(f"ASR payload[{i}] not a dict: {type(it).__name__}")
        keys = sorted(it.keys())
        if keys != ["raw", "sampling_rate"]:
            raise ValueError(f"ASR payload[{i}] keys={keys}, expected ['raw','sampling_rate']")
        raw = it["raw"]
        sr  = it["sampling_rate"]
        if not hasattr(raw, "__len__") or len(raw) == 0:
            raise ValueError(f"ASR payload[{i}] raw is empty")
        if not isinstance(sr, (int, _np.integer)):
            raise ValueError(f"ASR payload[{i}] sampling_rate type={type(sr).__name__}, expected int")

def _schema_summary(batch) -> str:
    """Compact log of what we are sending into HF."""
    if not isinstance(batch, list):
        return f"type={type(batch).__name__}"
    parts = []
    for i, x in enumerate(batch[:3]):
        if isinstance(x, dict):
            parts.append(
                f"[{i}] keys={sorted(list(x.keys()))} "
                f"raw={type(x.get('raw')).__name__}/"
                f"{getattr(x.get('raw'), 'dtype', None)} "
                f"sr={type(x.get('sampling_rate')).__name__}:{x.get('sampling_rate')}"
            )
        else:
            parts.append(f"[{i}] {type(x).__name__}")
    return "; ".join(parts)

# -------------------------
# HF pipeline call wrapper
# -------------------------
async def safe_asr_call(model, batched: List[dict], call_kwargs: Dict[str, Any]):
    """
    Call HF ASR with:
      - strict preflight logging
      - auto-isolation when HF raises the dict-schema ValueError
      - kwarg compatibility fallbacks
    """
    logger.info("ASR preflight -> %s", _schema_summary(batched))
    try:
        # IMPORTANT: positional call to avoid internal 'inputs=' wrapping
        return await asyncio.to_thread(model, batched, **call_kwargs)

    except TypeError as e:
        msg = str(e)
        if "condition_on_prev_text" in msg:
            k = dict(call_kwargs); k.pop("condition_on_prev_text", None)
            return await asyncio.to_thread(model, batched, **k)
        if "return_timestamps" in msg and call_kwargs.get("return_timestamps") == "word":
            k = dict(call_kwargs); k["return_timestamps"] = True
            return await asyncio.to_thread(model, batched, **k)
        raise

    except ValueError as e:
        # Hugging Face schema error path: auto-isolate the offending element
        msg = str(e)
        need = ("\"raw\" key" in msg) and ("sampling_rate" in msg)
        if need and isinstance(batched, list) and len(batched) > 1:
            logger.error("HF schema error; isolating offending item...")
            for idx, sample in enumerate(batched):
                try:
                    _ = model([sample], **call_kwargs)  # sync probe for this sample
                except Exception as ee:
                    keys = list(sample.keys()) if isinstance(sample, dict) else None
                    raw = sample.get("raw") if isinstance(sample, dict) else None
                    sr  = sample.get("sampling_rate") if isinstance(sample, dict) else None
                    logger.error(
                        "Offending item idx=%s type=%s keys=%s raw_type=%s raw_dtype=%s sr=%s",
                        idx, type(sample).__name__, keys,
                        type(raw).__name__ if raw is not None else None,
                        getattr(raw, "dtype", None) if raw is not None else None,
                        sr,
                    )
                    break
        raise

def _as_arrays_and_sr(payload: List[Dict[str, Any]]) -> Tuple[List[_np.ndarray], int | None]:
    """Extract list of raw arrays and the unique sampling rate if consistent (for fallback)."""
    arrays: List[_np.ndarray] = []
    srs: List[int] = []
    for it in payload:
        if isinstance(it, dict) and "raw" in it and "sampling_rate" in it:
            raw = it["raw"]
            if isinstance(raw, _t.Tensor):
                raw = raw.detach().cpu().numpy()
            arrays.append(_np.asarray(raw, dtype=_np.float32))
            srs.append(int(it["sampling_rate"]))
        else:
            arrays.append(_np.asarray(it, dtype=_np.float32))
    uniq = sorted(set(srs))
    return arrays, (uniq[0] if len(uniq) == 1 else None)

# -------------------------
# Public API
# -------------------------
def build_hf_asr_kwargs(model, batch_len: int, language: str | None = "th") -> Dict[str, Any]:
    """
    Build kwargs for transformers.AutomaticSpeechRecognitionPipeline with feature-gating
    for args that may not exist in older versions.
    """
    ck: Dict[str, Any] = {
        "return_timestamps": "word",            # falls back to True if unsupported
        "chunk_length_s": 20,
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

async def asr_with_policy_ladder(model, batched: List[Any], base_kwargs: Dict[str, Any]) -> List[dict]:
    """Run the ASR pipeline using a VRAM-friendly policy ladder with fallbacks."""
    # --- Normalize inputs and FREEZE the final payload ---
    default_sr = _infer_default_sr(model)

    # If a single dict sneaks in as the 'batch', wrap it; also materialize generators
    if isinstance(batched, dict):
        batched = [batched]
    else:
        batched = list(batched)

    canonical = [_coerce_one_to_hf(x, default_sr) for x in batched]
    payload   = _freeze_payload(canonical)
    _assert_payload(payload)  # cannot pass if malformed

    # 0) Standard
    try:
        kw = _merge_kwargs(base_kwargs, POLICIES["standard"])
        outs = await safe_asr_call(model, payload, kw)
        return outs if isinstance(outs, list) else [outs]
    except ValueError as ve:
        # HF dict schema refusal: retry with arrays (+ optional sampling_rate)
        if "AutomaticSpeechRecognitionPipeline" in str(ve) and "raw" in str(ve):
            arrays, sr = _as_arrays_and_sr(payload)
            kw = _merge_kwargs(base_kwargs, POLICIES["standard"])
            if sr is not None:
                kw = dict(kw, sampling_rate=int(sr))
            logger.info("ASR fallback -> arrays + sampling_rate=%s", sr)
            outs = await asyncio.to_thread(model, arrays, **kw)
            return outs if isinstance(outs, list) else [outs]
        else:
            raise
    except _t.cuda.OutOfMemoryError:
        _t.cuda.empty_cache()

    # 1) Tight
    try:
        kw = _merge_kwargs(base_kwargs, POLICIES["tight"])
        outs = await safe_asr_call(model, payload, kw)
        return outs if isinstance(outs, list) else [outs]
    except ValueError as ve:
        if "AutomaticSpeechRecognitionPipeline" in str(ve) and "raw" in str(ve):
            arrays, sr = _as_arrays_and_sr(payload)
            kw = _merge_kwargs(base_kwargs, POLICIES["tight"])
            if sr is not None:
                kw = dict(kw, sampling_rate=int(sr))
            logger.info("ASR fallback (tight) -> arrays + sampling_rate=%s", sr)
            outs = await asyncio.to_thread(model, arrays, **kw)
            return outs if isinstance(outs, list) else [outs]
        else:
            raise
    except _t.cuda.OutOfMemoryError:
        _t.cuda.empty_cache()

    # 2) Ultra
    try:
        kw = _merge_kwargs(base_kwargs, POLICIES["ultra"])
        outs = await safe_asr_call(model, payload, kw)
        return outs if isinstance(outs, list) else [outs]
    except ValueError as ve:
        if "AutomaticSpeechRecognitionPipeline" in str(ve) and "raw" in str(ve):
            arrays, sr = _as_arrays_and_sr(payload)
            kw = _merge_kwargs(base_kwargs, POLICIES["ultra"])
            if sr is not None:
                kw = dict(kw, sampling_rate=int(sr))
            logger.info("ASR fallback (ultra) -> arrays + sampling_rate=%s", sr)
            outs = await asyncio.to_thread(model, arrays, **kw)
            return outs if isinstance(outs, list) else [outs]
        else:
            raise
    except _t.cuda.OutOfMemoryError:
        _t.cuda.empty_cache()

    # 3) Sequential ultra (last resort)
    results: List[dict] = []
    kw = _merge_kwargs(base_kwargs, POLICIES["ultra"])
    for i in _tqdm(range(len(payload)), desc="ASR ultra seq", unit="seg"):
        try:
            out_i = await safe_asr_call(model, [payload[i]], kw)
            results.extend(out_i if isinstance(out_i, list) else [out_i])
        except ValueError as ve:
            if "AutomaticSpeechRecognitionPipeline" in str(ve) and "raw" in str(ve):
                arrays, sr = _as_arrays_and_sr([payload[i]])
                kw_i = dict(kw)
                if sr is not None:
                    kw_i["sampling_rate"] = int(sr)
                logger.info("ASR fallback (ultra seq) -> arrays + sampling_rate=%s", sr)
                out_i = await asyncio.to_thread(model, arrays, **kw_i)
                results.extend(out_i if isinstance(out_i, list) else [out_i])
            else:
                raise
        except _t.cuda.OutOfMemoryError:
            _t.cuda.empty_cache()
            safer = dict(kw, chunk_length_s=5, stride_length_s=(1.0, 1.0))
            try:
                out_i = await safe_asr_call(model, [payload[i]], safer)
            except ValueError as ve2:
                if "AutomaticSpeechRecognitionPipeline" in str(ve2) and "raw" in str(ve2):
                    arrays, sr = _as_arrays_and_sr([payload[i]])
                    safer_i = dict(safer)
                    if sr is not None:
                        safer_i["sampling_rate"] = int(sr)
                    logger.info("ASR fallback (ultra seq safer) -> arrays + sampling_rate=%s", sr)
                    out_i = await asyncio.to_thread(model, arrays, **safer_i)
                else:
                    raise
            results.extend(out_i if isinstance(out_i, list) else [out_i])
    return results