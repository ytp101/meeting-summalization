import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

# ─── Configure Logging ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("file_server")

# ─── FastAPI App ───────────────────────────────────────────────────────────────────
app = FastAPI()
DATA_ROOT = Path("/data")  # Bound volume

# ─── Routes ────────────────────────────────────────────────────────────────────────
@app.get("/")
def read_root():
    logger.info("Root endpoint hit")
    return {"status": "Server is running."}

@app.get("/download/{work_id}/{category}/{filename}")
def download_file(work_id: str, category: str, filename: str):
    logger.info(f"Download request: work_id={work_id}, category={category}, filename={filename}")
    
    valid_categories = {"raw", "converted", "transcript", "summary"}
    if category not in valid_categories:
        logger.warning(f"Invalid category requested: {category}")
        raise HTTPException(status_code=400, detail="Invalid category")

    file_path = DATA_ROOT / work_id / category / filename

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise HTTPException(status_code=404, detail="File not found")

    logger.info(f"Serving file: {file_path}")
    return FileResponse(path=file_path, filename=filename)
