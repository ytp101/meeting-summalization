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
import json
from typing import List 

from summarization.utils.logger import logger
from summarization.models.two_pass_model import (
    MeetingDoc,
    ChunkSummary, 
    FinalSummary, 
    Utterance
)
from summarization.utils.normalizer import normalize_utterances 
from summarization.utils.window import build_windows_by_chars 
from summarization.utils import prompts 
from summarization.services.ollama_client import OllamaChat 
from summarization.config import settings
from summarization.utils.text_renderer import _format_final_text

router = APIRouter()

@router.post(
    "/summarization/",
    summary="Summarize a transcript file (two-pass, Ollama)",
)
async def summarize(req: dict): 
    """
    Accepts either:
    - {"transcript_path": str, "output_dir": str}
    - {"meeting": MeetingDoc, "output_dir": str}
    Reads transcript, builds windows, runs Pass-1 (chunk summaries) with model A,
    then Pass-2 (reducer) with model B, writes final text file, and returns path.
    """
    start = time.time() 

    # 1) Load trancript text 
    meeting: MeetingDoc 
    output_dir: Path 

    if "meeting" in req:
        meeting = MeetingDoc(**req["meeting"])
        output_dir = Path(req["output_dir", "./result"])
    else: 
        # Back-compat: plain text transcript file
        transcript_path = Path(req.get("transcript_path", ""))
        
        output_dir = Path(req.get("output_dir", "./result"))
        if not transcript_path.exists():
            logger.error("Transcript not found: %s", transcript_path)
            raise HTTPException(status_code=404, detail="Transcript file not found")
        transcript = transcript_path.read_text(encoding="utf-8").strip()
        
        if not transcript:
            logger.error("Transcript is empty: %s", transcript_path)
            raise HTTPException(status_code=400, detail="Transcript is empty")
        
        # Wrap plain text as a single-speaker MeetingDoc
        meeting = MeetingDoc(
        meeting_id=transcript_path.stem,
        utterances=[Utterance(speaker="S1", start_ms=0, end_ms=None, text=transcript)]
        )

    # 2) Normalize and window 
    uttrs = normalize_utterances(
        meeting.utterances, 
        gap_merge_sec=settings.GAP_MERGE_SEC,
        max_chars_merge=settings.MAX_CHARS_MERGE 
    )
    windows = build_windows_by_chars(
        uttrs, 
        max_chars=settings.MAX_WINDOW_CHARS,
        overlap_chars=settings.OVERLAP_CHARS, 
    )
    if not windows:
        raise HTTPException(status_code=400, detail="Empty transcript after normalization")
    
    # 3) LLM client (Ollama) 
    c1 = OllamaChat(str(settings.PASS1_BASE_URL), settings.PASS1_MODEL)
    c2 = OllamaChat(str(settings.PASS2_BASE_URL), settings.PASS2_MODEL) 

    # 4) Pass-1 over windows 
    chunk_objects: List[ChunkSummary] = []
    for idx, (win_text, (w_start, w_end)) in enumerate(windows): 
        user = prompts.PASS1_USER_TEMPLATE.format(windows=win_text)
        content = await c1.chat(prompts.PASS1_SYSTEM, user, max_tokens=1300)
        try: 
            obj = json.loads(content) 
        except json.JSONDecodeError: 
            # Fallback: wrap as free-text summary if model ignores JSON mode
            obj = {"summary": content, "decisions": [], "action_items": []}
        chunk_objects.append(ChunkSummary(
            window_index=idx,
            start_ms=w_start,
            end_ms=w_end,
            summary=obj.get("summary", ""),
            decisions=obj.get("decisions", []) or [],
            action_items=obj.get("action_items", []) or [],
        ))

    # 5) Pass-2 reduce 
    jsonl = "".join(json.dumps(cs.model_dump(), ensure_ascii=False) for cs in chunk_objects)
    user2 = prompts.PASS2_USER_TEMPLATE.format(jsonl=jsonl)
    content2 = await c2.chat(prompts.PASS2_SYSTEM, user2, max_tokens=1800)
    # Expect JSON; if not, treat as text
    try:
        final = json.loads(content2)
        final_text = _format_final_text(final)
    except json.JSONDecodeError:
        final_text = content2.strip()

    # 6) Write final text
    output_dir.mkdir(parents=True, exist_ok=True)
    out_name = f"{meeting.meeting_id}_summary.txt"
    out_path = output_dir / out_name
    out_path.write_text(final_text, encoding="utf-8")
    await c1.aclose(); await c2.aclose()
    elapsed = time.time() - start
    logger.info(f"Summarization content: {final_text}")
    logger.info("Meeting %s summarized in %.2fs", meeting.meeting_id, elapsed)
    logger.info("✅ Wrote summary: %s", out_path)
    logger.info("⏱️ Summarization completed in %.2fs", elapsed)
    return {"summary_path": str(out_path)}