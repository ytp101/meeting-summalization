import os
import time
import gc
import logging
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import torch
import torchaudio
from transformers import pipeline, Pipeline as HFPipeline

# ─── Logging & Configuration ─────────────────────────────────────────────────────────
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
logger = logging.getLogger("whisper_service")
logger.info("Starting Whisper Speech-to-Text Service")

# ─── FastAPI Setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title="Whisper Speech-to-Text Service")

# ─── Environment & Directories ──────────────────────────────────────────────────────
HF_HOME      = Path(os.getenv("HF_HOME", "/home/app/.cache"))
HF_HOME.mkdir(parents=True, exist_ok=True)
os.environ["HF_HOME"] = str(HF_HOME)

MODEL_ID        = os.getenv("MODEL_ID", "openai/whisper-large-v3-turbo")
LANGUAGE        = os.getenv("LANGUAGE", "en")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 1200))
PORT            = int(os.getenv("PORT", 8003))

# ─── Pydantic Schemas ───────────────────────────────────────────────────────────────
class DiarSegment(BaseModel):
    start: float
    end: float
    speaker: Optional[str] = None

class TranscribeRequest(BaseModel):
    filename: str                           # WAV filename (without extension)
    output_dir: str                     
    segments: Optional[List[DiarSegment]] = None  # Precomputed diarization segments

class WordSegment(BaseModel):
    start: float
    end: float
    speaker: Optional[str]
    text: str

class TranscriptionResponse(BaseModel):
    transcription_file_path: str

# ─── Model Loader ─────────────────────────────────────────────────────────────────
_whisper_model: HFPipeline = None

def get_whisper_model() -> HFPipeline:
    global _whisper_model
    if _whisper_model is None:
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        dtype  = torch.float16 if torch.cuda.is_available() else torch.float32
        logger.info(f"Loading Whisper model '{MODEL_ID}' on device {device} dtype {dtype}")
        _whisper_model = pipeline(
            task="automatic-speech-recognition",
            model=MODEL_ID,
            device=device,
            torch_dtype=dtype,
            return_timestamps=True,
            chunk_length_s=30,
            batch_size=1,
            generate_kwargs={"language": LANGUAGE}
        )
        logger.info("Whisper model loaded successfully")
    return _whisper_model

# ─── Transcription Logic ───────────────────────────────────────────────────────────
async def transcribe(
    wav_path: Path,
    segments: Optional[List[DiarSegment]]
) -> (List[WordSegment], List[str]):
    
    # 1) Load audio
    waveform, sample_rate = await asyncio.to_thread(torchaudio.load, str(wav_path))

    # 2) Determine diarization segments
    if segments:
        diar_segments = segments
    else:
        total_dur = waveform.shape[1] / sample_rate
        diar_segments = [DiarSegment(start=0.0, end=total_dur)]

    results: List[WordSegment] = []
    lines: List[str] = []
    model = get_whisper_model()

    # 3) Transcribe each segment
    for seg in diar_segments:
        t0, t1 = seg.start, seg.end
        start_frame = int(t0 * sample_rate)
        end_frame   = int(t1 * sample_rate)
        chunk = waveform[:, start_frame:end_frame]

        # run model in background
        audio_np = chunk.mean(dim=0).cpu().numpy()
        out = await asyncio.to_thread(model, audio_np)

        # 3a) word-level chunks
        if isinstance(out, dict) and "chunks" in out:
            for c in out["chunks"]:
                c0, c1 = c.get("timestamp", (None, None))
                text   = c.get("text", "").strip()
                if c0 is None or not text:
                    continue
                c1 = c1 or t1
                ws = WordSegment(start=c0, end=c1, speaker=seg.speaker, text=text)
                results.append(ws)
                lines.append(f"[{c0:.2f}-{c1:.2f}] {seg.speaker or 'Speaker'}: {text}")
        # 3b) chunk-level fallback
        else:
            text = out.get("text", "").strip() if isinstance(out, dict) else ""
            if text:
                ws = WordSegment(start=t0, end=t1, speaker=seg.speaker, text=text)
                results.append(ws)
                lines.append(f"[{t0:.2f}-{t1:.2f}] {seg.speaker or 'Speaker'}: {text}")

    return results, lines

# ─── Routes ───────────────────────────────────────────────────────────────────────
@app.post(
    "/whisper/",
    response_model=TranscriptionResponse,
    summary="Transcribe a WAV file with optional diarization segments"
)
async def whisper_endpoint(req: TranscribeRequest):
    start = time.time()
    # validate paths
    wav_path = Path(req.filename)
    if not wav_path.is_file():
        logger.error(f"WAV not found: {wav_path}")
        raise HTTPException(status_code=404, detail="WAV file not found")

    txt_dir = Path(req.output_dir)
    txt_dir.mkdir(parents=True, exist_ok=True)

    txt_name = wav_path.stem
    txt_file = txt_dir / f"{txt_name}.txt"

    # transcribe
    segments, lines = await transcribe(wav_path, req.segments)

    # write transcript
    await asyncio.to_thread(txt_file.write_text, "\n".join(lines), encoding="utf-8")

    # cleanup GPU
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        gc.collect()

    elapsed = time.time() - start
    logger.info(f"Transcribed '{req.filename}' in {elapsed:.2f}s")

    return JSONResponse({
        "transcription_file_path": f"{txt_file}",
    })

@app.get("/", summary="Service status")
def root():
    return {"status": "running", "model": MODEL_ID}

@app.get("/healthcheck", summary="Healthcheck GPU & Model")
def healthcheck():
    gpu = torch.cuda.is_available()
    return {"model_loaded": _whisper_model is not None, "gpu_available": gpu}

# ─── Entrypoint ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
