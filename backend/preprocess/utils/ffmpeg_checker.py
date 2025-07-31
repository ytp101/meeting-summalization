"""
Module: utils/ffmpeg_checker.py

Purpose:
Provides a utility function to verify whether FFmpeg is installed 
and accessible in the system's environment. This check is used 
during service startup to ensure all required dependencies are available.

Author: yodsran
"""

import asyncio

async def is_ffmpeg_available() -> bool:
    """
    Checks if FFmpeg is installed and accessible in the current environment.

    Executes the command `ffmpeg -version` silently to validate the presence 
    of the FFmpeg binary in the system path.

    Returns:
        bool: True if FFmpeg is available and returns exit code 0; 
              False otherwise.
    """
    test_process = await asyncio.create_subprocess_exec(
        "ffmpeg", "-version",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await test_process.wait()
    return test_process.returncode == 0
