"""
🎙️ VAD Inference Router

This module defines the FastAPI router responsible for handling Voice Activity Detection (VAD) inference requests.
It exposes a single POST endpoint at `/vad` which accepts an input file path and returns a list of detected
speech segments.

Key Features:
- Validates input path and checks for file existence
- Executes the VAD pipeline asynchronously using the `run_vad_on_file` service
- Handles exceptions gracefully with meaningful HTTP responses
- Returns a JSON-formatted list of speech chunks (start, end, chunk_id)

Expected Input:
{
    "input_path": "/absolute/path/to/audio.wav"
}

Example Output:
[
    { "chunk_id": 0, "start": 0.0, "end": 1.2 },
    { "chunk_id": 1, "start": 1.5, "end": 3.8 }
]

This router is intended to be used as part of a larger audio analysis microservice.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import logging

from vad.models.vad_request import VADRequest
from vad.services.vad_service import run_vad_on_file

router = APIRouter()

@router.post("/vad", tags=["inference"])
async def vad_segments(req: VADRequest):
    path = Path(req.input_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Audio file not found")

    try:
        result = await run_vad_on_file(str(path))
    except Exception as e:
        logging.exception("VAD inference failed")
        raise HTTPException(status_code=500, detail="VAD failed")

    timeline = result.get_timeline().support()

    # 🧠 Return raw JSON format like in your CLI script
    segments = []
    for i, seg in enumerate(timeline):
        segments.append({
            "chunk_id": i,
            "start": round(seg.start, 3),
            "end": round(seg.end, 3)
        })

    return JSONResponse(content=segments)