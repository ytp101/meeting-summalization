from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from file_server.utils.files import generate_paths

router = APIRouter()

@router.get("/download/{work_id}/{category}")
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
