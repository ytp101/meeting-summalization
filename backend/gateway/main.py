from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from pathlib import Path
import httpx, uvicorn, os, time, logging
from typing import Any, Dict, List

# ——— Logging & Config ——————————————————————————————————————————————————————————
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR       = Path(os.getenv("BASE_DIR", "/usr/local/app/data/mp4"))
WAV_DIR        = Path(os.getenv("BASE_DIR_WAV", "/usr/local/app/data/wav"))
TXT_DIR        = Path(os.getenv("BASE_DIR_TXT", "/usr/local/app/data/txt"))
PREPROCESS_URL = os.getenv("PREPROCESS_SERVICE_URL", "http://preprocess:8001/preprocess/")
WHISPER_URL    = os.getenv("WHISPER_SERVICE_URL", "http://whisper:8003/whisper/")
SUMMARIZE_URL  = os.getenv("SUMMARIZATION_SERVICE_URL", "http://summarization:8005/summarization/")
DIAR_URL       = os.getenv("DIARIZATION_SERVICE_URL", "http://diarization:8004/diarization/")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 1200))

for d in (BASE_DIR, WAV_DIR, TXT_DIR):
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Meeting Summarization Gateway")

class ServiceStatus(BaseModel):
    service: str
    status:  str
    message: str = ""

# ——— Helpers ——————————————————————————————————————————————————————————————————
async def call_service(
    client: httpx.AsyncClient, 
    name: str, 
    url: str, 
    payload: Dict[str,Any]
) -> Any:
    try:
        logger.info(f"[{name}] → {url} payload={payload}")
        resp = await client.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"[{name}] HTTP {e.response.status_code}: {e.response.text}")
        raise HTTPException(500, f"{name} failed: {e.response.text}")
    except httpx.TimeoutException:
        logger.error(f"[{name}] timed out after {REQUEST_TIMEOUT}s")
        raise HTTPException(504, f"{name} timed out")
    except Exception as e:
        logger.error(f"[{name}] error: {e}")
        raise HTTPException(500, f"{name} error: {e}")

# ——— Healthcheck ——————————————————————————————————————————————————————————————
@app.get("/", response_model=Dict[str,str])
def root():
    return {"status":"gateway running"}

@app.get("/healthcheck", response_model=List[ServiceStatus])
async def healthcheck():
    results: List[ServiceStatus] = []
    services = [
        ("preprocess", PREPROCESS_URL.replace("/preprocess/","/")),
        ("diarization", DIAR_URL.replace("/diarization/","/")),
        ("whisper", WHISPER_URL.replace("/whisper/","/")),
        ("summarization", SUMMARIZE_URL.replace("/summarization/","/")),
    ]
    async with httpx.AsyncClient() as client:
        for name, check_url in services:
            try:
                r = await client.get(check_url, timeout=5.0)
                status = "up" if r.status_code==200 else f"error {r.status_code}"
            except Exception as e:
                status = f"down ({e})"
            results.append(ServiceStatus(service=name, status=status))
    return results

# ——— Upload & Orchestration ——————————————————————————————————————————————————
@app.post("/uploadfile/")
async def upload_and_process(file: UploadFile = File(...)):
    start = time.time()

    # 1) Save MP4
    if not file.filename.lower().endswith(".mp4"):
        raise HTTPException(400, "Only .mp4 supported")
    mp4_path = BASE_DIR / file.filename
    stem = mp4_path.stem
    content = await file.read()
    mp4_path.write_bytes(content)
    logger.info(f"Saved upload → {mp4_path}")

    async with httpx.AsyncClient() as client:
        # 2) Preprocess → wav
        pp = await call_service(client, "preprocess", PREPROCESS_URL, {"filename": stem})
        wav_file = pp[0]["preprocessed_file_path"]

        # 3) Diarization → segments
        diar = await call_service(client, "diarization", DIAR_URL, {"filename": wav_file})
        segments = diar.get("segments", [])

        # 4) Whisper → transcription (+ word-level timestamps)
        wr = await call_service(client, "whisper", WHISPER_URL, {"filename": wav_file})
        transcript_file = wr["transcription_file_path"]
        segments        = wr.get("segments", [])

        # 5) Summarization → final
        sr = await call_service(client, "summarization", SUMMARIZE_URL, {
            "filename": wav_file,
            "segments": segments
        }
        )
        summary_path = sr[0]["summarization_file_path"]

    elapsed = time.time() - start
    logger.info(f"Pipeline done in {elapsed:.1f}s")

    # 6) Read back the summary for user
    summary_file = TXT_DIR / f"{summary_path}"
    if not summary_file.exists():
        raise HTTPException(500, f"Summary file missing: {summary_file}")
    summary_text = summary_file.read_text(encoding="utf-8")

    return {
        "filename": stem,
        "summary": summary_text,
        "processing_time_seconds": round(elapsed,2),
    }

if __name__=="__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT",8000)))
