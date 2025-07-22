from pathlib import Path

DATA_ROOT = Path("/data")

def find_source_filename(work_id: str) -> str:
    raw_folder = DATA_ROOT / work_id / "raw"
    allowed_exts = [".mp3", ".mp4", ".m4a", ".mov"]
    
    for ext in allowed_exts:
        matches = list(raw_folder.glob(f"*{ext}"))
        if matches:
            return matches[0].name
    raise FileNotFoundError(f"No raw file found for work_id: {work_id}")

def generate_paths(work_id: str) -> dict:
    source_filename = find_source_filename(work_id)
    stem = Path(source_filename).stem
    return {
        "source": DATA_ROOT / work_id / "raw" / source_filename,
        "wav": DATA_ROOT / work_id / "converted" / f"{stem}.wav",
        "transcript": DATA_ROOT / work_id / "transcript" / f"{stem}.txt",
        "summary": DATA_ROOT / work_id / "summary" / f"{stem}_summary.txt",
    }
