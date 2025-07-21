"""
summarize_schema.py
-------------------

This module defines the Pydantic data models for the summarization API request
and response payloads. These models enforce strict input validation and ensure
structured responses for clients of the Summarization microservice.

Schemas:
- SummarizeRequest: Incoming POST body containing paths to the input transcript
  and the desired output directory for the summary result.

- SummarizeResponse: JSON response indicating the saved path of the generated
  summary text file.

These models are used in FastAPI route signatures and OpenAPI schema generation.

Author:
    yodsran
"""

from pydantic import BaseModel

class SummarizeRequest(BaseModel):
    """
    Request payload for the summarization endpoint.

    Attributes:
        transcript_path (str): Absolute path to the input .txt transcript file.
        output_dir (str): Directory where the summary file should be saved.
    """
    transcript_path: str
    output_dir: str

class SummarizeResponse(BaseModel):
    """
    Response payload for a successful summarization.

    Attributes:
        summary_path (str): Full path to the generated summary file.
    """
    summary_path: str 
