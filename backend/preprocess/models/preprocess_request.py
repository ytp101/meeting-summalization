"""
Module: models/preprocess_request.py

Purpose:
Defines the request schema for the audio preprocessing service. 
Used to validate input data when submitting media conversion tasks 
to the preprocessing endpoint.

Author: yodsran
"""

from pydantic import BaseModel

class PreprocessRequest(BaseModel):
    """
    Request model for preprocessing audio files using FFmpeg.

    Attributes:
        input_path (str): Absolute path to the input media file 
                          (e.g., .mp4, .mkv).
        output_dir (str): Directory path where the converted WAV file 
                          should be stored.
    """
    input_path: str
    output_dir: str
