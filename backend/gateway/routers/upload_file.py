"""
Gateway Service Upload & Processing Router Module

This module defines the `/uploadfile/` endpoint for the API Gateway Service.
It manages the full audio processing pipeline, coordinating with downstream microservices:

1. **File Validation**: Ensures uploaded file has an allowed extension (`.mp3`, `.mp4`, `.m4a`, `.wav`).
2. **Task Initialization**: Generates a unique task ID and creates directories for raw, converted, transcript, and summary files.
3. **File Storage**: Saves the raw upload to the designated data directory.
4. **Preprocessing**: Converts the raw audio to Opus (.opus) via the Preprocess service.
5. **Speaker Diarization**: Splits audio into speaker segments via the Diarization service.
6. **Transcription**: Performs ASR using the Whisper service and writes transcripts to disk.
7. **Summarization**: Summarizes the transcript via the Summarization service.
8. **Database Registration**: Inserts the task ID into the PostgreSQL database for tracking.

Utilities and Dependencies:
- `generate_task_id`, `call_service`: from `gateway.utils.utils` for ID generation and service calls.
- `insert_work_id`: from `gateway.utils.pg` for database operations.
- `logger`: from `gateway.utils.logger` for structured logging.
- Configuration constants (`DATA_DIR`, service URLs): from `gateway.config.settings`.

Raises:
    HTTPException: 400 if file type is unsupported.
    HTTPException: 500 if summary file generation fails.

Response:
    Returns a JSON object with the generated `task_id` and the summary text.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
import time
from pathlib import Path
import httpx

from gateway.utils.utils import generate_task_id, call_service
from gateway.config.settings import DATA_DIR, PREPROCESS_URL, DIAR_URL, WHISPER_URL, SUMMARIZE_URL
from gateway.utils.logger import logger
from gateway.utils.pg import insert_work_id
from gateway.services.upload import save_upload_nohash

router = APIRouter()

@router.post("/uploadfile/", response_model=dict)
async def upload_and_process(file: UploadFile = File(...)) -> dict:
    """
    Handle file upload and orchestrate the audio processing pipeline.

    Args:
        file (UploadFile): The uploaded audio file.

    Returns:
        dict: {
            "task_id": str,          # Unique identifier for this processing task
            "summary": str           # Generated summary text
        }

    Raises:
        HTTPException: 400 for unsupported file extensions.
        HTTPException: 500 if the summary file is missing or processing fails.
    """
    # 1) Validate file extension
    allowed_exts = {".mp3", ".mp4", ".m4a", ".wav"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    # 2) Generate task ID and create directories
    task_id = generate_task_id()
    task_dir = DATA_DIR / task_id
    raw_dir = task_dir / "raw"
    converted_dir = task_dir / "converted"
    transcript_dir = task_dir / "transcript"
    summary_dir = task_dir / "summary"
    for d in (raw_dir, converted_dir, transcript_dir, summary_dir):
        d.mkdir(parents=True, exist_ok=True)

    # 3) Save raw file
    raw_path = raw_dir / file.filename
    status = await save_upload_nohash(file, raw_path)
    logger.info(f"Saved upload → {raw_path} with {status}")

    start = time.time()

    # 4-7) Orchestrate preprocessing, diarization, transcription, and summarization
    async with httpx.AsyncClient() as client:
        # 4) Preprocess
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

    # Record task in database
    insert_work_id(str(task_id))

    return {"task_id": task_id, "summary": summary_text}
