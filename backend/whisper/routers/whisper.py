"""
Whisper Transcription Endpoint.

POST /whisper/
Transcribes a WAV file and saves the output to a .txt file.
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
from tqdm.auto import tqdm  # <-- add this

from whisper.services.transcribe import transcribe
from whisper.utils.logger import logger
from whisper.models.whisper_request import TranscribeRequest
from whisper.models.whisper_response import TranscriptionResponse
from whisper.utils.merger_ws import words_to_utterances_from_ws

router = APIRouter()

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

    out_dir = Path(req.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = wav_path.stem
    txt_file = out_dir / f"{stem}.txt"
    word_json = out_dir / f"{stem}.word_segments.json"
    utt_json  = out_dir / f"{stem}.utterances.json"

    # --- tqdm progress bar (server console) ---
    bar = None
    def on_progress(job_id: str, done_sec: float, total_sec: float):
        nonlocal bar
        total = max(1.0, float(total_sec or 0.0))
        if bar is None:
            bar = tqdm(total=total, unit="s", desc=f"ASR {job_id}", dynamic_ncols=True)
        # advance to 'done_sec'
        cur = float(done_sec or 0.0)
        delta = max(0.0, cur - bar.n)
        if delta:
            bar.update(delta)
            pct = (cur / total * 100.0) if total > 0 else 0.0
            bar.set_postfix_str(f"{pct:.1f}%")

    try:
        # 1) transcribe -> returns (List[WordSegment], List[str])
        word_segments, lines = await transcribe(
            wav_path,
            req.segments,
            job_id=stem,
            on_progress=on_progress,  # <-- hook in
        )
    finally:
        if bar is not None:
            bar.close()

    # 2) render human transcript
    await asyncio.to_thread(txt_file.write_text, "\n".join(lines), encoding="utf-8")

    # 3) write machine JSON: word_segments
    word_payload = {
        "schema_version": "v1",
        "segments": [ws.model_dump() for ws in word_segments],
    }
    await asyncio.to_thread(
        word_json.write_text,
        json.dumps(word_payload, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # 4) write machine JSON: utterances (speaker-merged)
    utterances = words_to_utterances_from_ws(word_segments, max_gap_s=0.6)
    await asyncio.to_thread(
        utt_json.write_text,
        json.dumps(utterances, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # cleanup GPU
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        gc.collect()

    elapsed = time.time() - start
    logger.info(f"Transcribed '{req.filename}' in {elapsed:.2f}s")

    return JSONResponse({
        "transcription_file_path": str(txt_file),
        "word_segments_path": str(word_json),
        "utterances_path": str(utt_json),
    })
