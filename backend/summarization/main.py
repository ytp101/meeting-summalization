import os
import time
import logging
from pathlib import Path
from typing import List, Optional

import uvicorn
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ─── CONFIGURATION ────────────────────────────────────────────────────────────

logger = logging.getLogger("summarization")
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO,
)

BASE_DIR_TXT    = Path(os.getenv("BASE_DIR_TXT", "/usr/local/app/data/txt/"))
MODEL_ID        = os.getenv("MODEL_ID", "llama3")
OLLAMA_HOST     = os.getenv("OLLAMA_HOST", "http://localhost:11434")
SYSTEM_PROMPT   = os.getenv(
    "SYSTEM_PROMPT",
    "Summarize the following meeting transcript. "
    "Focus on key decisions, action items, and important discussions. "
    "Make the summary concise yet comprehensive."
)
MAX_TOKENS      = int(os.getenv("MAX_TOKENS", 4096))
TEMPERATURE     = float(os.getenv("TEMPERATURE", 0.2))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 300))  # seconds

BASE_DIR_TXT.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Meeting Summarization Service")


# ─── Pydantic Models ──────────────────────────────────────────────────────────

class Segment(BaseModel):
    start: float
    end:   float
    text:  str

class SummarizationRequest(BaseModel):
    filename: Optional[str] = None
    segments: Optional[List[Segment]] = None

class SummarizationResponse(BaseModel):
    filename: str
    summarization_file_path: str


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _read_file_text(path: Path) -> str:
    if not path.exists():
        logger.error("File not found: %s", path)
        raise HTTPException(status_code=404, detail="File not found")
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        logger.error("File is empty: %s", path)
        raise HTTPException(status_code=400, detail="File is empty")
    return text

def _build_transcript(req: SummarizationRequest) -> (str, str):
    if req.segments:
        transcript = "\n".join(
            f"[{seg.start:.2f}s–{seg.end:.2f}s] {seg.text.strip()}"
            for seg in req.segments
        )
        source_id = req.filename
    elif req.filename:
        file_path = BASE_DIR_TXT / f"{req.filename}.txt"
        transcript = _read_file_text(file_path)
        source_id = req.filename
    else:
        logger.error("No filename or segments provided")
        raise HTTPException(status_code=400, detail="Must supply `filename` or `segments`")
    return transcript, source_id

async def _call_ollama(transcript: str) -> str:
    payload = {
        "model": MODEL_ID,
        "prompt": f"{SYSTEM_PROMPT}\n\n{transcript}",
        "stream": False,
        "options": {
            "num_predict": MAX_TOKENS,
            "temperature": TEMPERATURE,
            "context_window": 8192
        }
    }
    url = f"{OLLAMA_HOST}/api/generate"
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.post(url, json=payload)
    if resp.status_code != 200:
        logger.error("Ollama error %d: %s", resp.status_code, resp.text)
        raise HTTPException(status_code=500, detail="Ollama API error")
    data = resp.json()
    # support both v1 ("response") and v0 ("choices")
    return data.get("response") or (data.get("choices") or [{}])[0].get("text", "")

def _write_text_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    logger.info("Wrote: %s", path)


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "Summarization service is running"}

@app.get("/healthcheck")
async def healthcheck():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_HOST}/api/tags")
        if resp.status_code != 200:
            return {"status": "degraded", "ollama": f"error {resp.status_code}"}
        models = resp.json().get("models", [])
        if any(m["name"] == MODEL_ID for m in models):
            return {"status": "healthy", "ollama": "available", "model": MODEL_ID}
        return {
            "status": "degraded",
            "ollama": "available",
            "model": "not found",
            "available_models": [m["name"] for m in models]
        }
    except Exception as e:
        logger.exception("Healthcheck failed")
        return {"status": "unhealthy", "error": str(e)}

@app.post(
    "/summarization/",
    response_model=List[SummarizationResponse],
    responses={400: {"description": "Bad Request"},
               404: {"description": "Not Found"},
               500: {"description": "Internal Error"},
               504: {"description": "Gateway Timeout"}}
)
async def summarization(req: SummarizationRequest):
    start_time = time.time()
    logger.info("Request: %s", req.json())

    # 1) Build transcript & write inspected copy
    transcript, source_id = _build_transcript(req)
    inspect_path = BASE_DIR_TXT / f"{source_id}_inspected.txt"
    _write_text_file(inspect_path, transcript)

    # 2) Summarize
    summary = await _call_ollama(transcript)
    if not summary.strip():
        logger.error("Empty summary returned")
        raise HTTPException(status_code=500, detail="Empty summary from model")

    # 3) Save summary
    summary_filename = f"{source_id}_summarized.txt"
    summary_path = BASE_DIR_TXT / summary_filename
    _write_text_file(summary_path, summary)

    elapsed = time.time() - start_time
    logger.info("Completed in %.2fs", elapsed)
    return [
        SummarizationResponse(
            filename=source_id,
            summarization_file_path=summary_filename
        )
    ]


# ─── Entrypoint ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8005)))
