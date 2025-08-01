"""
File Path Utilities
-------------------

This module contains utility functions for locating and generating paths
for meeting-related files, such as source audio, converted `.wav`, transcripts, and summaries.

The structure assumes a base `DATA_ROOT` like:

    /data/
      └── <work_id>/
           ├── raw/
           │     └── original_file.mp3
           ├── converted/
           │     └── original_file.wav
           ├── transcript/
           │     └── original_file.txt
           └── summary/
                 └── original_file_summary.txt

These helpers abstract the file discovery and path construction logic to
ensure consistent access patterns across services.

Author: yodsran
"""

from pathlib import Path

# Root path to mounted volume (should be overridden in tests)
DATA_ROOT = Path("/data")


def find_source_filename(work_id: str) -> str:
    """
    Searches the raw/ directory for the first supported audio file.

    Args:
        work_id (str): The work identifier (used as the folder name).

    Returns:
        str: The filename of the discovered source file.

    Raises:
        FileNotFoundError: If no supported source file is found.
    """
    raw_folder = DATA_ROOT / work_id / "raw"
    allowed_exts = [".mp3", ".mp4", ".m4a", ".mov"]
    
    for ext in allowed_exts:
        matches = list(raw_folder.glob(f"*{ext}"))
        if matches:
            return matches[0].name
    raise FileNotFoundError(f"No raw file found for work_id: {work_id}")


def generate_paths(work_id: str) -> dict:
    """
    Generates a dictionary of file paths for a given work ID, based on the discovered source filename.

    Args:
        work_id (str): The work identifier (used as the folder name).

    Returns:
        dict: A dictionary with keys: source, wav, transcript, summary,
              each mapped to their expected full Path object.
    """
    source_filename = find_source_filename(work_id)
    stem = Path(source_filename).stem
    return {
        "source": DATA_ROOT / work_id / "raw" / source_filename,
        "wav": DATA_ROOT / work_id / "converted" / f"{stem}.wav",
        "transcript": DATA_ROOT / work_id / "transcript" / f"{stem}.txt",
        "summary": DATA_ROOT / work_id / "summary" / f"{stem}_summary.txt",
    }
