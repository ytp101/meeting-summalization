from fastapi import APIRouter 

router = APIRouter()

@router.get("/", response_model=dict)
def root():
    return {"status": "gateway running"}