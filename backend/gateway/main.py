from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import httpx, uvicorn, os, time, logging
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import create_engine, text

# ——— Logging & Config ——————————————————————————————————————————————————————————
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Base Data Directory (Docker volume mount)
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Service endpoints
PREPROCESS_URL = os.getenv("PREPROCESS_SERVICE_URL", "http://preprocess:8001/preprocess/")
DIAR_URL       = os.getenv("DIARIZATION_SERVICE_URL", "http://diarization:8004/diarization/")
WHISPER_URL    = os.getenv("WHISPER_SERVICE_URL", "http://whisper:8003/whisper/")
SUMMARIZE_URL  = os.getenv("SUMMARIZATION_SERVICE_URL", "http://summarization:8005/summarization/")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "1200"))

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@" \
         f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

pg_engine = create_engine(DB_URL)

logger.info(f"DB connected at: {pg_engine} with {DB_URL}")

app = FastAPI(title="Meeting Summarization Gateway")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGINS", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ServiceStatus(BaseModel):
    service: str
    status:  str
    message: str = ""

async def call_service(client: httpx.AsyncClient, name: str, url: str, payload: dict) -> dict:
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

def generate_task_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    uid = uuid4().hex
    return f"{ts}_{uid}"

def insert_work_id(work_id: str):
    with pg_engine.connect() as conn: 
        try: 
            stmt = text("INSERT INTO meeting_summary (work_id) VALUES (:work_id)")
            conn.execute(stmt, {"work_id": str(work_id)})
            conn.commit()
            print(f"[+] Inserted work_id: {work_id} with {conn}")
        except Exception as e:
            print("[-] Error inserting:", e)
 
# ——— Healthcheck ——————————————————————————————————————————————————————————————
@app.get("/", response_model=dict)
def root():
    return {"status": "gateway running"}

@app.get("/healthcheck", response_model=list[ServiceStatus])
async def healthcheck():
    services = [
        ("preprocess", PREPROCESS_URL.replace("/preprocess/", "/")),
        ("diarization", DIAR_URL.replace("/diarization/", "/")),
        ("whisper", WHISPER_URL.replace("/whisper/", "/")),
        ("summarization", SUMMARIZE_URL.replace("/summarization/", "/")),
    ]
    results: list[ServiceStatus] = []
    async with httpx.AsyncClient() as client:
        for name, check_url in services:
            status = "down"
            try:
                r = await client.get(check_url, timeout=5.0)
                status = "up" if r.status_code == 200 else f"error {r.status_code}"
            except Exception as e:
                status = f"down ({e})"
            results.append(ServiceStatus(service=name, status=status))
    return results

# ——— Upload & Orchestration ———————————————————————————————————————————————————
@app.post("/uploadfile/")
async def upload_and_process(file: UploadFile = File(...)):
    # 1) Validate file extension
    allowed_exts = {".mp3", ".mp4", ".m4a", ".wav"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    # 2) Generate task ID and create directories
    task_id = generate_task_id()
    task_dir = DATA_DIR / task_id
    raw_dir       = task_dir / "raw"
    converted_dir = task_dir / "converted"
    transcript_dir= task_dir / "transcript"
    summary_dir   = task_dir / "summary"
    for d in (raw_dir, converted_dir, transcript_dir, summary_dir):
        d.mkdir(parents=True, exist_ok=True)

    # 3) Save raw file
    raw_path = raw_dir / file.filename
    content = await file.read()
    raw_path.write_bytes(content)
    logger.info(f"Saved upload → {raw_path}")

    start = time.time()

    # 4) Preprocess: convert to WAV
    stem = raw_path.stem
    async with httpx.AsyncClient() as client:
        pp = await call_service(client, "preprocess", PREPROCESS_URL, {
            "input_path": str(raw_path),
            "output_dir": str(converted_dir)
        })
        wav_file = pp[0]["preprocessed_file_path"]
        wav_path = Path(wav_file)

        # 5) Diarization
        diar = await call_service(client, "diarization", DIAR_URL, {"audio_path": str(wav_path)})
        segments = diar.get("segments", [])

        # 6) Whisper transcription
        wr = await call_service(client, "whisper", WHISPER_URL, {
            "filename": str(wav_path),
            "output_dir": str(transcript_dir),
            "segments": segments
        })
        transcript_file = wr.get("transcription_file_path")
        transcript_path = Path(transcript_file)

        # 7) Summarization
        sr = await call_service(client, "summarization", SUMMARIZE_URL, {
            "transcript_path": str(transcript_path),
            "output_dir": str(summary_dir)
        })
        summary_path = Path(sr.get("summary_path"))

    elapsed = time.time() - start
    logger.info(f"Pipeline done in {elapsed:.1f}s")

    # 8) Read summary
    if not summary_path.exists():
        raise HTTPException(500, f"Summary file missing: {summary_path}")
    summary_text = summary_path.read_text(encoding="utf-8")

    insert_work_id(str(task_id))

    # return {
    #     "task_id": task_id,
    #     "filename": stem,
    #     "summary": summary_text,
    #     "processing_time_seconds": round(elapsed, 2),
    # }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
