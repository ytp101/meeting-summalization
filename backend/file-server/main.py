from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI(title="Meeting Summary File Server")

DATA_ROOT = Path("/data")  # This is your Docker bind mount path

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

@app.get("/available/{work_id}")
def check_files(work_id: str):
    try:
        paths = generate_paths(work_id)
        return {
            "source": paths["source"].exists(),
            "wav": paths["wav"].exists(),
            "transcript": paths["transcript"].exists(),
            "summary": paths["summary"].exists()
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Source file not found")


@app.get("/download/{work_id}/{category}")
def download(work_id: str, category: str):
    valid_categories = {"source", "wav", "transcript", "summary"}
    if category not in valid_categories:
        raise HTTPException(status_code=400, detail="Invalid category")

    try:
        paths = generate_paths(work_id)
        path = paths[category]
        if not path.exists():
            raise FileNotFoundError()
        return FileResponse(path=path, filename=path.name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found for work_id={work_id}, category={category}")
