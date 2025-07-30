from fastapi import APIRouter, HTTPException
import time     
from pathlib import Path
import asyncio
import gc
import torch
from fastapi.responses import JSONResponse

from whisper.services.transcribe import transcribe
from whisper.utils.logger import logger
from whisper.models.whisper_request import TranscribeRequest
from whisper.models.whisper_response import TranscriptionResponse
router = APIRouter()

# ─── Routes ───────────────────────────────────────────────────────────────────────
@router.post(
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