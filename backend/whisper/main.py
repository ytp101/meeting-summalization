import os
import time
import gc
import logging
import requests

from pathlib import Path
from typing import List, Literal

import torch
import torchaudio
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from transformers import pipeline, Pipeline as HFPipeline

# ─── Logging & Env Setup ─────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("whisper_service")

# Directories from env
BASE_DIR_WAV = Path(os.getenv("BASE_DIR_WAV", "/usr/local/app/data/wav/"))
BASE_DIR_TXT = Path(os.getenv("BASE_DIR_TXT", "/usr/local/app/data/txt/"))
HF_HOME       = Path(os.getenv("HF_HOME", "/home/app/.cache"))
VAD_URL       = os.getenv("VAD_URL", "http://vad:8002/vad/")
MODEL_ID      = os.getenv("MODEL_ID", "openai/whisper-large-v3-turbo")
LANGUAGE      = os.getenv("LANGUAGE", "th")
PORT          = int(os.getenv("PORT", 8003))

# Ensure directories exist
for d in (BASE_DIR_WAV, BASE_DIR_TXT, HF_HOME):
    d.mkdir(parents=True, exist_ok=True)
os.environ["HF_HOME"] = str(HF_HOME)

# ─── FastAPI App ─────────────────────────────────────────────────────────────────
app = FastAPI(title="Whisper Speech-to-Text Service")

# ─── Pydantic Models ─────────────────────────────────────────────────────────────
class FilePath(BaseModel):
    filename: str = Field(..., description="Name of the WAV file (without extension)")

class Segment(BaseModel):
    start: float
    end: float
    text: str

class TranscriptionResponse(BaseModel):
    transcription_file_path: str
    segments: List[Segment]

# ─── Model Loader ────────────────────────────────────────────────────────────────
_whisper_model: HFPipeline = None

def get_whisper_model() -> HFPipeline:
    global _whisper_model
    if _whisper_model is None:
        device   = "cuda:0" if torch.cuda.is_available() else "cpu"
        dtype    = torch.float16 if torch.cuda.is_available() else torch.float32
        logger.info(f"Loading Whisper model '{MODEL_ID}' on {device} ({dtype})")
        _whisper_model = pipeline(
            "automatic-speech-recognition",
            model=MODEL_ID,
            device=device,
            torch_dtype=dtype,
            return_timestamps=True,
            chunk_length_s=30,
            batch_size=1,
            generate_kwargs={"language": LANGUAGE},
        )
        logger.info("Model loaded successfully")
    return _whisper_model

# ─── VAD Helper ─────────────────────────────────────────────────────────────────
def fetch_vad_segments(filename: str) -> List[dict]:
    """
    Call the VAD service to get speech segments for 'filename'.
    Expects JSON: { "segments": [ { "start": float, "end": float }, … ] }
    """
    try:
        resp = requests.post(VAD_URL, json={"filename": filename}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("segments", [])
    except Exception as e:
        logger.error(f"VAD request failed: {e}")
        raise HTTPException(502, "Failed to fetch VAD segments")

# ─── Transcription Logic ─────────────────────────────────────────────────────────
def transcribe_file(
    wav_path: Path,
    out_path: Path,
    model: HFPipeline
) -> List[Segment]:
    """
    1. Load waveform
    2. Fetch VAD segments
    3. For each segment, run Whisper
    4. Collect timestamped words (or per-segment text)
    5. Write human-readable .txt
    6. Return list of Segment(start, end, text)
    """
    waveform, sr = torchaudio.load(str(wav_path))
    base_name    = wav_path.stem

    # 1) VAD
    vad_segs = fetch_vad_segments(base_name)
    if not vad_segs:
        raise HTTPException(422, "No speech segments detected")

    segments: List[Segment] = []
    lines: List[str]      = []

    # 2) Transcribe each segment
    for seg in vad_segs:
        t0, t1 = seg["start"], seg["end"]
        start_idx = int(t0 * sr)
        end_idx   = int(t1 * sr)
        chunk_wf  = waveform[:, start_idx:end_idx].mean(dim=0).numpy()

        result = model(chunk_wf)

        # 3a) If word-level timestamps available
        if isinstance(result, dict) and result.get("chunks"):
            for c in result["chunks"]:
                c0, c1 = c["timestamp"]
                text   = c["text"].strip()
                if not text: 
                    continue

                if c0 is None: 
                    continue 
                if c1 is None: 
                    c1 = t1

                segments.append(Segment(start=c0, end=c1, text=text))
                lines.append(f"[{c0:.2f}s - {c1:.2f}s] {text}")
        # 3b) else per-segment
        else:
            text = result.get("text", "").strip()
            if text:
                segments.append(Segment(start=t0, end=t1, text=text))
                lines.append(f"[{t0:.2f}s - {t1:.2f}s] {text}")

    # 4) Write .txt for humans
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return segments

# ─── Startup & Health ────────────────────────────────────────────────────────────
@app.on_event("startup")
def load_model_on_startup():
    try:
        get_whisper_model()
    except Exception:
        logger.exception("Failed to load model at startup")

@app.get("/", summary="Service status")
def root():
    return {
        "status": "running",
        "model": MODEL_ID,
        "device": "cuda" if torch.cuda.is_available() else "cpu"
    }

@app.get("/healthcheck", summary="Check GPU & model")
def healthcheck():
    gpu_info = {}
    if torch.cuda.is_available():
        gpu_info = {
            "available":      True,
            "device_count":   torch.cuda.device_count(),
            "current_device": torch.cuda.current_device(),
            "device_name":    torch.cuda.get_device_name(0),
            "memory_alloc":   f"{torch.cuda.memory_allocated(0)/2**30:.2f} GB",
            "memory_reserved":f"{torch.cuda.memory_reserved(0)/2**30:.2f} GB",
        }
    return {
        "model_loaded": _whisper_model is not None,
        "gpu": gpu_info
    }

# ─── Transcription Endpoint ──────────────────────────────────────────────────────
@app.post(
    "/whisper/",
    response_model=TranscriptionResponse,
    summary="Transcribe a WAV file with Whisper + VAD"
)
def transcribe_endpoint(fp: FilePath):
    start_time = time.time()
    fname      = fp.filename
    wav_path   = BASE_DIR_WAV / f"{fname}.wav"
    txt_path   = BASE_DIR_TXT / f"{fname}.txt"

    if not wav_path.exists():
        raise HTTPException(404, f"WAV file not found: {wav_path}")

    model = get_whisper_model()

    try:
        segments = transcribe_file(wav_path, txt_path, model)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error during transcription")
        raise HTTPException(500, "Transcription failed") from e

    # free GPU memory if needed
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        gc.collect()

    elapsed = time.time() - start_time
    logger.info(f"Transcribed '{fname}' in {elapsed:.2f}s, saved to {txt_path}")

    return JSONResponse(
        status_code=200,
        content=TranscriptionResponse(
            transcription_file_path=fname,
            segments=segments
        ).dict()
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
