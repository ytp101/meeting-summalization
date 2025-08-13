"""
Module: services/audio_preprocessor.py

Purpose:
Provides the core logic for audio preprocessing using FFmpeg. 
This service converts input media files into normalized 16-bit mono WAV format, 
suitable for downstream tasks such as diarization or automatic speech recognition (ASR).

The function is designed to run asynchronously and handles both processing failures 
and timeout scenarios gracefully.

Author: yodsran
"""

from pathlib import Path 
import asyncio
from fastapi import HTTPException

from preprocess.utils.logger import logger
from preprocess.config.settings import FFMPEG_TIMEOUT

async def preprocess(input_file: Path, output_file: Path) -> None:
    """
    Converts a media file to normalized 16-bit PCM mono WAV format using FFmpeg.

    The conversion process:
        - Removes any video stream
        - Downsamples the audio to 16 kHz
        - Converts audio to mono channel
        - Applies loudness normalization
        - Outputs as PCM 16-bit `.wav`

    Args:
        input_file (Path): Absolute path to the input media file.
        output_file (Path): Destination path for the output WAV file.

    Raises:
        HTTPException:
            - 500: If FFmpeg execution fails (e.g., unsupported format, file error).
            - 504: If FFmpeg execution exceeds the configured timeout duration.

    Logging:
        - Logs the command being executed.
        - Logs error messages and timeout issues for troubleshooting.
    """
    cmd = [
        "ffmpeg", "-y", "-i", str(input_file),
        "-vn",                # Disable video stream
        "-ar", "16000",       # Sample rate: 16 kHz
        "-ac", "1",           # Mono channel
        "-c:a", "pcm_s16le",  # 16-bit PCM encoding
        "-af", "highpass=f=100,arnndn=m=rnnoise,dynaudnorm=f=150:g=15,loudnorm",
        str(output_file)
    ]

    logger.info(f"Running FFmpeg: {' '.join(cmd)}")

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=FFMPEG_TIMEOUT
        )
        if proc.returncode != 0:
            error_msg = stderr.decode(errors="ignore").strip().splitlines()[-1]
            logger.error(f"FFmpeg error [{proc.returncode}]: {error_msg}")
            raise HTTPException(500, f"FFmpeg failed: {error_msg}")
    except asyncio.TimeoutError:
        logger.error(f"FFmpeg timed out after {FFMPEG_TIMEOUT}s")
        proc.kill()
        raise HTTPException(504, f"FFmpeg timed out after {FFMPEG_TIMEOUT}s")
