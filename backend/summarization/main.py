import os
import time
import logging
import asyncio
from pathlib import Path
from typing import List, Dict

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ─── Logging & Config ──────────────────────────────────────────────────────────
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
logger = logging.getLogger("summarization_service")
logger.info("Starting Summarization Service")

# ─── FastAPI setup ─────────────────────────────────────────────────────────────
app = FastAPI(title="Meeting Summarization Service")

# ─── Environment & Model Config ─────────────────────────────────────────────────
OLLAMA_HOST    = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_ID       = os.getenv("MODEL_ID", "llama3")
SYSTEM_PROMPT  = os.getenv("SYSTEM_PROMPT", "Summarize the following transcript in a concise, structured format.")
MAX_TOKENS     = int(os.getenv("MAX_TOKENS", 4096))
TEMPERATURE    = float(os.getenv("TEMPERATURE", 0.2))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 300))

# ─── Pydantic Schemas ───────────────────────────────────────────────────────────
class SummarizeRequest(BaseModel):
    transcript_path: str        # full path to transcript .txt file
    output_dir: str

class SummarizeResponse(BaseModel):
    summary_path: str      # filename of summary file (in output_dir)

# ─── Helpers ───────────────────────────────────────────────────────────────────
async def call_ollama(transcript: str) -> str:
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
    return data.get("response") or (data.get("choices") or [{}])[0].get("text", "")

# ─── Routes ────────────────────────────────────────────────────────────────────
@app.get("/", summary="Liveness check")
def root():
    return {"status": "summarization running", "model": MODEL_ID}

@app.get("/healthcheck", summary="Model health check")
async def healthcheck():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_HOST}/api/tags")
        if resp.status_code != 200:
            return {"status": "degraded", "ollama": f"error {resp.status_code}"}
        models = resp.json().get("models", [])
        ok = any(m.get("name") == MODEL_ID for m in models)
        return {"status": "healthy" if ok else "degraded", "model": MODEL_ID}
    except Exception as e:
        logger.exception("Healthcheck failed")
        return {"status": "unhealthy", "error": str(e)}

@app.post(
    "/summarization/",
    response_model=SummarizeResponse,
    summary="Summarize a transcript file"
)
async def summarize(req: SummarizeRequest):
    start = time.time()
    input_file = Path(req.transcript_path)
    if not input_file.exists():
        logger.error("Transcript not found: %s", input_file)
        raise HTTPException(status_code=404, detail="Transcript file not found")

    transcript = input_file.read_text(encoding="utf-8").strip()
    if not transcript:
        logger.error("Transcript is empty: %s", input_file)
        raise HTTPException(status_code=400, detail="Transcript is empty")

    # 1) Generate summary via Ollama
    summary_text = await call_ollama(transcript)
    if not summary_text.strip():
        logger.error("Empty summary returned")
        raise HTTPException(status_code=500, detail="Empty summary from model")

    # 2) Write summary file
    out_dir = Path(req.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_file = f"{input_file.stem}_summary.txt"
    summary_path = out_dir / summary_file
    summary_path.write_text(summary_text, encoding="utf-8")
    logger.info("Wrote summary: %s", summary_path)

    elapsed = time.time() - start
    logger.info("Summarization completed in %.2fs", elapsed)
    return SummarizeResponse(summary_path=str(summary_path))

# ─── Entrypoint ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8005)), log_level="info")
