"""
Module: routers/preprocess.py

Purpose:
Defines the endpoint for audio preprocessing. This route accepts a media file path,
validates its existence, processes the media using FFmpeg, and outputs a 48 kHz mono
Opus file (.opus). It is intended to serve as the second step in the speech 
processing pipeline, following upload and preceding diarization or ASR.

Author: yodsran
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path 
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from preprocess.models.preprocess_request import PreprocessRequest
from preprocess.utils.logger import logger
from preprocess.services.audio_preprocessor import preprocess as run_preprocess

router = APIRouter()

def _ensure_under_base(p: Path, base: Path = Path("/data")) -> None:
    try:
        rp = p.resolve()
        basep = base.resolve()
        rp.relative_to(basep)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Path must be under {base}")

@router.post("/preprocess/", summary="Convert audio/video to normalized Opus (.opus)")
async def preprocess(req: PreprocessRequest):
    """
    Converts an input media file to a 48 kHz mono Opus format (.opus).
    
    ### Preprocessing Steps:
    1. Validates the input file path exists.
    2. Ensures the output directory exists or creates it.
    3. Invokes the audio preprocessing service (FFmpeg wrapper).
    4. Returns the path to the generated WAV file if successful.

    Args:
        req (PreprocessRequest): The request body containing input and output paths.

    Raises:
        HTTPException:
            - 404: If the input file does not exist.
            - 500: If the output WAV file is not generated after processing.

    Returns:
        JSONResponse: A JSON object containing the path to the preprocessed .opus file.

    Example Response:
        [
            {
                "preprocessed_file_path": "/path/to/output/audio.opus"
            }
        ]
    """
    input_path = Path(req.input_path)
    _ensure_under_base(input_path)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise HTTPException(404, "Input file not found")

    output_dir = Path(req.output_dir)
    _ensure_under_base(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{input_path.stem}.opus"

    await run_preprocess(input_path, output_file)

    if not output_file.exists():
        logger.error(f"Opus file not produced: {output_file}")
        raise HTTPException(500, "Failed to produce Opus file")

    logger.info(f"Produced Opus: {output_file}")
    response = [{"preprocessed_file_path": str(output_file)}]
    return JSONResponse(content=jsonable_encoder(response))
