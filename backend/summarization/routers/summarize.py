"""
summarize.py
------------

This module defines the POST route `/summarization/` for generating summaries
from transcript files using the Ollama LLM backend (e.g., LLaMA 3).

Responsibilities:
- Validates input and transcript file existence.
- Reads and verifies transcript contents.
- Sends the transcript to the Ollama model via `call_ollama()`.
- Writes the returned summary to a `.txt` file in the given output directory.
- Returns a structured JSON response containing the saved summary path.

Intended for internal use in a multi-stage transcription pipeline.

Author:
    yodsran
"""

from fastapi import APIRouter, HTTPException
import time  
from pathlib import Path

from summarization.utils.logger import logger
from summarization.models.summarize_schema import SummarizeRequest, SummarizeResponse
from summarization.services.ollama_client import call_ollama

router = APIRouter()

@router.post(
    "/summarization/",
    response_model=SummarizeResponse,
    summary="Summarize a transcript file"
)
async def summarize(req: SummarizeRequest):
    """
    Summarize a plain-text transcript file using an Ollama-hosted LLM.

    Steps:
    1. Validate transcript path and content.
    2. Generate summary from model.
    3. Write summary to disk with `_summary.txt` suffix.

    Args:
        req (SummarizeRequest): Contains `transcript_path` and `output_dir`.

    Returns:
        SummarizeResponse: Path to the saved `.txt` summary.

    Raises:
        HTTPException: For file not found, empty content, or model errors.
    """
    start = time.time()
    input_file = Path(req.transcript_path)
    if not input_file.exists():
        logger.error("Transcript not found: %s", input_file)
        raise HTTPException(status_code=404, detail="Transcript file not found")

    transcript = input_file.read_text(encoding="utf-8").strip()
    if not transcript:
        logger.error("Transcript is empty: %s", input_file)
        raise HTTPException(status_code=400, detail="Transcript is empty")

    # Step 1: Call Ollama model
    summary_text = await call_ollama(transcript)
    if not summary_text.strip():
        logger.error("Empty summary returned")
        raise HTTPException(status_code=500, detail="Empty summary from model")

    # Step 2: Write to output directory
    out_dir = Path(req.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_file = f"{input_file.stem}_summary.txt"
    summary_path = out_dir / summary_file
    summary_path.write_text(summary_text, encoding="utf-8")
    logger.info("✅ Wrote summary: %s", summary_path)

    elapsed = time.time() - start
    logger.info("⏱️ Summarization completed in %.2fs", elapsed)
    return SummarizeResponse(summary_path=str(summary_path))
