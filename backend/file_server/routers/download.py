"""
Download Endpoint Router
------------------------

This module provides the `/download/{work_id}/{category}` endpoint for serving 
meeting-related files from a structured directory.

Supported categories:
- `source`: original uploaded file (e.g., .mp3, .mp4)
- `opus`: converted .opus audio
- `transcript`: raw transcript text
- `summary`: LLM-generated summary

Behavior:
- Validates category.
- Dynamically resolves file paths using `generate_paths`.
- Returns a `FileResponse` if the file exists.
- Returns appropriate 400/404 errors for invalid categories or missing files.

This router is intended to be mounted on the main FastAPI app and assumes 
a predefined directory structure rooted in `DATA_ROOT`.

Example usage:
GET /download/test123/transcript

Author: yodsran
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from utils.files import generate_paths
from utils.logger import logger 

router = APIRouter()

@router.get("/download/{work_id}/{category}")
def download(work_id: str, category: str):
    valid_categories = {"source", "opus", "transcript", "summary"}
    if category not in valid_categories:
        raise HTTPException(status_code=400, detail="Invalid category")

    try:
        paths = generate_paths(work_id)
        path = paths[category]
        logger.info(f"File path {path}")
        if not path.exists():
            raise FileNotFoundError()
        return FileResponse(path=path, filename=path.name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found for work_id={work_id}, category={category}")
