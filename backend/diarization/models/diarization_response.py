from typing import List
from pydantic import BaseModel, Field

class Segment(BaseModel):
    """
    Represents a speaker-labeled segment of the audio.

    Attributes:
        start (float): Start time of the segment in seconds.
        end (float): End time of the segment in seconds.
        speaker (str): Speaker label or identifier (e.g., 'SPEAKER_00').
    """
    start: float = Field(..., example=0.0, description="Start time in seconds")
    end: float = Field(..., example=3.25, description="End time in seconds")
    speaker: str = Field(..., example="SPEAKER_01", description="Speaker label")

class DiarizationResponse(BaseModel):
    """
    Response schema containing the list of speaker segments extracted from the audio.

    Attributes:
        segments (List[Segment]): A list of time-stamped speaker-labeled segments.
    """
    segments: List[Segment] = Field(..., description="List of detected speaker segments")
