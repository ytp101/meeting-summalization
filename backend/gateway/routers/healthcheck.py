from fastapi import APIRouter 
import httpx

from gateway.models.service_status import ServiceStatus
from gateway.config.settings import PREPROCESS_URL, DIAR_URL, WHISPER_URL, SUMMARIZE_URL

router = APIRouter() 

@router.get("/healthcheck", response_model=list[ServiceStatus])
async def healthcheck():
    services = [
        ("preprocess", PREPROCESS_URL.replace("/preprocess/", "/")),
        ("diarization", DIAR_URL.replace("/diarization/", "/")),
        ("whisper", WHISPER_URL.replace("/whisper/", "/")),
        ("summarization", SUMMARIZE_URL.replace("/summarization/", "/")),
    ]
    results: list[ServiceStatus] = []
    async with httpx.AsyncClient() as client:
        for name, check_url in services:
            status = "down"
            try:
                r = await client.get(check_url, timeout=5.0)
                status = "up" if r.status_code == 200 else f"error {r.status_code}"
            except Exception as e:
                status = f"down ({e})"
            results.append(ServiceStatus(service=name, status=status))
    return results