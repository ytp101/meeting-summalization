"""
Whisper Transcription Endpoint.

POST /whisper/
Transcribes an audio file and saves the output to a .txt file.
Supports optional diarization segments.

Request: TranscribeRequest
Response: TranscriptionResponse
"""

from fastapi import APIRouter, HTTPException
import time     
from pathlib import Path
import asyncio
import gc
import torch
from fastapi.responses import JSONResponse
import json

from whisper.services.transcribe import transcribe
from whisper.utils.logger import logger
from whisper.models.whisper_request import TranscribeRequest
from whisper.models.whisper_response import TranscriptionResponse
from whisper.utils.merger_ws import words_to_utterances_from_ws

router = APIRouter()

def _ensure_under_base(p: Path, base: Path = Path("/data")) -> None:
    try:
        rp = p.resolve()
        basep = base.resolve()
        rp.relative_to(basep)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Path must be under {base}")

# ─── Routes ───────────────────────────────────────────────────────────────────────
@router.post(
    "/whisper/",
    response_model=TranscriptionResponse,
    summary="Transcribe an audio file with optional diarization segments"
)
async def whisper_endpoint(req: TranscribeRequest):
    start = time.time()

    # validate paths
    audio_path = Path(req.filename)
    _ensure_under_base(audio_path)
    if not audio_path.is_file():
        logger.error(f"Audio file not found: {audio_path}")
        raise HTTPException(status_code=404, detail="Audio file not found")

    out_dir = Path(req.output_dir)
    _ensure_under_base(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = audio_path.stem 
    txt_file = out_dir / f"{stem}.txt"
    word_json = out_dir / f"{stem}.word_segments.json"
    utt_json  = out_dir / f"{stem}.utterances.json"

    # 1) transcribe -> returns (List[WordSegment], List[str])
    # segments come from diarization step
    word_segments, lines = await transcribe(
        audio_path,
        req.segments,
        task_id=req.task_id,
        progress_url=req.progress_url,
        progress_min=req.progress_min,
        progress_max=req.progress_max,
    )

    # 2) render human transcript
    await asyncio.to_thread(txt_file.write_text, "\n".join(lines), encoding="utf-8")

    # 3) write machine JSON: word_segments
    word_payload = {
        "schema_version": "v1",
        "segments": [ws.model_dump() for ws in word_segments],
    }
    await asyncio.to_thread(
        word_json.write_text, json.dumps(word_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 4) write machine JSON: utterances (speaker-merged)
    utterances = words_to_utterances_from_ws(word_segments, max_gap_s=0.6)
    await asyncio.to_thread(
        utt_json.write_text, json.dumps(utterances, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # cleanup GPU
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        gc.collect()

    elapsed = time.time() - start
    logger.info(f"Transcribed '{req.filename}' in {elapsed:.2f}s")

    # Return paths (validated by response_model)
    return TranscriptionResponse(
        transcription_file_path=str(txt_file),
        word_segments_path=str(word_json),
        utterances_path=str(utt_json),
    )
