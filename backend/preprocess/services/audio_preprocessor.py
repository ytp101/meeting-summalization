"""
Module: services/audio_preprocessor.py

Purpose:
Provides the core logic for audio preprocessing using FFmpeg. 
This service converts input media files into a 48 kHz mono Opus format (.opus), 
suitable for downstream tasks such as diarization or automatic speech recognition (ASR).

The function is designed to run asynchronously and handles both processing failures 
and timeout scenarios gracefully.

Author: yodsran
"""

from pathlib import Path 
import asyncio
from fastapi import HTTPException
import time
from typing import Optional
import httpx

from preprocess.utils.logger import logger
from preprocess.config.settings import FFMPEG_TIMEOUT

async def _probe_duration_seconds(path: Path) -> Optional[float]:
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=nw=1:nk=1",
            str(path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
        if proc.returncode == 0:
            s = out.decode().strip()
            return float(s) if s else None
    except Exception:
        return None
    return None

async def _post(url: Optional[str], payload: dict) -> None:
    if not url:
        return
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, timeout=5.0)
    except Exception:
        pass

async def preprocess(
    input_file: Path,
    output_file: Path,
    *,
    progress_url: Optional[str] = None,
    pmin: Optional[float] = None,
    pmax: Optional[float] = None,
) -> None:
    """
    Converts a media file to 48 kHz mono Opus format using FFmpeg.

    The conversion process:
        - Removes any video stream
        - Converts audio to mono channel
        - Applies loudness normalization
        - Outputs as `.opus` (48 kHz), speech-optimized

    Args:
        input_file (Path): Absolute path to the input media file.
        output_file (Path): Destination path for the output .opus file.

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
        "-hide_banner", "-nostats", "-loglevel", "error",
        "-progress", "pipe:1",
        "-vn",                      # no video
        "-af", "highpass=f=100,dynaudnorm=f=150:g=15,loudnorm",
        "-ar", "48000",             # Opus works natively at 48k
        "-ac", "1",                 # mono (speech)
        "-c:a", "libopus",
        "-b:a", "48k",              # ~30–40 MB for 1 hr
        "-vbr", "on",               # variable bitrate for quality
        "-application", "voip",     # speech-optimized
        str(output_file)            # <-- use .opus extension
    ]


    logger.info(f"Running FFmpeg: {' '.join(cmd)}")

    # Probe duration for progress mapping
    dur_s = await _probe_duration_seconds(input_file)

    # Progress bounds
    has_progress = bool(progress_url and pmin is not None and pmax is not None and dur_s and dur_s > 0)
    last_sent = 0.0
    last_pct = -1.0

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        async def read_progress():
            nonlocal last_sent, last_pct
            if not has_progress:
                return
            await _post(progress_url, {"service": "preprocess", "step": "ffmpeg", "status": "progress", "progress": float(pmin)})
            while True:
                if proc.stdout.at_eof():
                    break
                line = await proc.stdout.readline()
                if not line:
                    await asyncio.sleep(0.05)
                    if proc.returncode is not None:
                        break
                    continue
                try:
                    s = line.decode(errors="ignore").strip()
                except Exception:
                    continue
                # Parse out_time_ms= or out_time=
                if s.startswith("out_time_ms="):
                    try:
                        ms = float(s.split("=", 1)[1])
                        cur_s = ms / 1_000_000.0
                    except Exception:
                        continue
                elif s.startswith("out_time="):
                    # format HH:MM:SS.micro
                    try:
                        t = s.split("=", 1)[1]
                        hh, mm, ss = t.split(":")
                        cur_s = int(hh) * 3600 + int(mm) * 60 + float(ss)
                    except Exception:
                        continue
                else:
                    continue

                pct = max(0.0, min(1.0, cur_s / float(dur_s)))
                mapped = float(pmin) + pct * (float(pmax) - float(pmin))
                now = time.time()
                if mapped - last_pct >= 1.0 or (now - last_sent) > 1.0:
                    last_pct = mapped
                    last_sent = now
                    await _post(progress_url, {
                        "service": "preprocess", "step": "ffmpeg", "status": "progress",
                        "progress": round(mapped, 2),
                    })

        reader = asyncio.create_task(read_progress())
        try:
            await asyncio.wait_for(proc.wait(), timeout=FFMPEG_TIMEOUT)
        except asyncio.TimeoutError:
            proc.kill()
            await reader
            logger.error(f"FFmpeg timed out after {FFMPEG_TIMEOUT}s")
            raise HTTPException(504, f"FFmpeg timed out after {FFMPEG_TIMEOUT}s")
        finally:
            await reader

        if proc.returncode != 0:
            stderr = await proc.stderr.read()
            error_msg = stderr.decode(errors="ignore").strip().splitlines()[-1] if stderr else "ffmpeg failed"
            logger.error(f"FFmpeg error [{proc.returncode}]: {error_msg}")
            raise HTTPException(500, f"FFmpeg failed: {error_msg}")
        else:
            if has_progress:
                await _post(progress_url, {"service": "preprocess", "step": "ffmpeg", "status": "completed", "progress": float(pmax)})
    except asyncio.TimeoutError:
        logger.error(f"FFmpeg timed out after {FFMPEG_TIMEOUT}s")
        proc.kill()
        raise HTTPException(504, f"FFmpeg timed out after {FFMPEG_TIMEOUT}s")
