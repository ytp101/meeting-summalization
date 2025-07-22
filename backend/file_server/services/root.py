from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def root():
    return {"message": "Meeting Summary File Server is live"}
