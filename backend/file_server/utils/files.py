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
    Dynamically finds the first file in each category folder for a given work ID.
    Returns a dict of Paths (never None). If nothing is found for a category,
    returns a placeholder Path inside the correct folder so callers can safely
    call .exists() and turn that into a 404.
    """
    # Map API categories to on-disk directories
    dir_map = {
        "source": "raw",
        "opus": "converted",
        "transcript": "transcript",
        "summary": "summary",
    }

    # Optional: narrow patterns per category (kept broad but reasonable)
    glob_map = {
        "source": "*.*",       # mp3/mp4/m4a/mov live here
        "opus": "*.opus",
        "transcript": "*.txt",
        "summary": "*.txt",
    }

    paths: dict[str, Path] = {}

    for category, folder_name in dir_map.items():
        folder = DATA_ROOT / work_id / folder_name
        pattern = glob_map.get(category, "*.*")
        matches = list(folder.glob(pattern))

        if matches:
            paths[category] = matches[0]
        else:
            # Return a placeholder path to avoid None → .exists() crash.
            # Router will do path.exists() → False → 404 (as intended).
            placeholder_name = {
                "source": ".missing_source",
                "opus": ".missing_audio.wav",
                "transcript": ".missing_transcript.txt",
                "summary": ".missing_summary.txt",
            }.get(category, ".missing")
            paths[category] = folder / placeholder_name

    return paths
