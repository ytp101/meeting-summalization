"""
Module: config/settings.py

Purpose:
Provides configuration constants for the audio preprocessing system. 
Includes timeout settings for external tool execution (e.g., FFmpeg).

Author: yodsran
"""

import os

# Timeout duration (in seconds) for FFmpeg operations.
# Can be overridden via the environment variable 'FFMPEG_TIMEOUT'.
FFMPEG_TIMEOUT = int(os.getenv("FFMPEG_TIMEOUT", 600))
