from fastapi import APIRouter, UploadFile, File, HTTPException
import time
from pathlib import Path
import httpx

from gateway.utils.utils import generate_task_id
from gateway.config.settings import DATA_DIR, PREPROCESS_URL, DIAR_URL, SUMMARIZE_URL, WHISPER_URL
from gateway.utils.logger import logger
from gateway.utils.pg import insert_work_id
from gateway.utils.utils import call_service

router = APIRouter()

@router.post("/uploadfile/")
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