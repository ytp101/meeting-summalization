from fastapi import FastAPI, UploadFile, HTTPException, File
import uvicorn
import os
import httpx
from pathlib import Path
import logging
import time
from typing import List, Optional
import mimetypes
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.info("Gateway service is starting up")

# Environment variables with defaults
BASE_DIR = os.getenv('BASE_DIR', '/usr/local/app/data/mp4/')
PREPROCESS_ENDPOINT = os.getenv('PREPROCESS_SERVICE_URL', 'http://preprocess:8001/preprocess/')
WHISPER_ENDPOINT = os.getenv('WHISPER_SERVICE_URL', 'http://whisper:8002/whisper/')
SUMMARIZATION_ENDPOINT = os.getenv('SUMMARIZATION_SERVICE_URL', 'http://summarization:8003/summarization/')
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 1200))  # 20 minutes default

# Create directories if they don't exist
os.makedirs(BASE_DIR, exist_ok=True)

# Setup FastAPI service
app = FastAPI(title="Meeting Summarization Gateway")

class ServiceStatus(BaseModel):
    service: str
    status: str
    message: Optional[str] = None

@app.get("/")
def running():
    return {"status": "Gateway service is running"}

@app.get("/healthcheck")
async def healthcheck():
    """Check if all services are available"""
    results = []
    
    async with httpx.AsyncClient() as client:
        for service, url in [
            ("preprocess", PREPROCESS_ENDPOINT.replace("/preprocess/", "/")),
            ("whisper", WHISPER_ENDPOINT.replace("/whisper/", "/")),
            ("summarization", SUMMARIZATION_ENDPOINT.replace("/summlization/", "/"))
        ]:
            try:
                response = await client.get(url, timeout=5.0)
                if response.status_code == 200:
                    results.append(ServiceStatus(service=service, status="up"))
                else:
                    results.append(ServiceStatus(
                        service=service, 
                        status="error", 
                        message=f"HTTP {response.status_code}"
                    ))
            except Exception as e:
                results.append(ServiceStatus(
                    service=service, 
                    status="down", 
                    message=str(e)
                ))
    
    return results

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    """Process an uploaded meeting recording"""
    start_time = time.time()
    logger.info(f"Received file: {file.filename}")
    
    # Validate file type
    if not file.filename.lower().endswith('.mp4'):
        logger.error(f"Invalid file type: {file.filename}")
        raise HTTPException(status_code=400, detail="Only MP4 files are supported")
    
    # Step 1: Save uploaded file
    try:
        file_path = Path(BASE_DIR) / file.filename
        file_name = file_path.stem
        
        with open(file_path, "wb") as file_upload:
            contents = await file.read()
            file_upload.write(contents)
        logger.info(f"File saved to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(status_code=500, detail=f"Gateway failed to save file: {str(e)}")
    
    # Step 2: Send to preprocess service
    logger.info(f"Sending file: {file_name} to preprocess service")
    try:
        async with httpx.AsyncClient() as client:
            preprocess_response = await client.post(
                PREPROCESS_ENDPOINT,
                json={"filename": file_name},
                timeout=REQUEST_TIMEOUT
            )
            if preprocess_response.status_code != 200:
                raise Exception(f"Preprocess returned status {preprocess_response.status_code}")
        logger.info("Preprocessing completed")
    except httpx.TimeoutException:
        logger.error("Preprocessing timed out")
        raise HTTPException(status_code=504, detail="Preprocessing timed out")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Preprocess failed: {str(e)}")
    
    # Step 3: Get preprocessed file path
    try:
        preprocessed_file_path = preprocess_response.json()[0]['preprocessd_file_path']
    except (KeyError, IndexError) as e:
        logger.error(f"Invalid preprocess response format: {e}")
        raise HTTPException(status_code=500, detail="Invalid response from preprocess service")
    
    # Step 4: Send to whisper service
    logger.info(f"Sending file: {preprocessed_file_path} to whisper service")
    try:
        async with httpx.AsyncClient() as client:
            transcription_response = await client.post(
                WHISPER_ENDPOINT,
                json={"filename": preprocessed_file_path},
                timeout=REQUEST_TIMEOUT
            )
            if transcription_response.status_code != 200:
                raise Exception(f"Whisper returned status {transcription_response.status_code}")
        logger.info("Transcription completed")
    except httpx.TimeoutException:
        logger.error("Transcription timed out")
        raise HTTPException(status_code=504, detail="Transcription timed out")
    except Exception as e:
        logger.error(f"Whisper failed: {e}")
        raise HTTPException(status_code=500, detail=f"Whisper failed: {str(e)}")
    
    # Step 5: Get transcription file path
    try:
        transcription_file_path = transcription_response.json()[0]['trancription_file_path']
    except (KeyError, IndexError) as e:
        logger.error(f"Invalid whisper response format: {e}")
        raise HTTPException(status_code=500, detail="Invalid response from whisper service")
    
    # Step 6: Send to summarization service
    logger.info(f"Sending file: {transcription_file_path} to summarization service")
    try:
        async with httpx.AsyncClient() as client:
            summarization_response = await client.post(
                SUMMARIZATION_ENDPOINT,
                json={"filename": transcription_file_path},
                timeout=REQUEST_TIMEOUT
            )
            if summarization_response.status_code != 200:
                raise Exception(f"Summarization returned status {summarization_response.status_code}")
        logger.info("Summarization completed")
    except httpx.TimeoutException:
        logger.error("Summarization timed out")
        raise HTTPException(status_code=504, detail="Summarization timed out")
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")
    
    # Step 7: Get summarization file path
    try:
        summarization_file_path = summarization_response.json()[0]['summarization_file_path']
    except (KeyError, IndexError) as e:
        logger.error(f"Invalid summarization response format: {e}")
        raise HTTPException(status_code=500, detail="Invalid response from summarization service")
    
    logger.info(f"Reading summary file: {summarization_file_path}")
    
    # Calculate processing time
    elapsed_time = time.time() - start_time
    logger.info(f"Total processing time: {elapsed_time:.2f} seconds")
    
    # Step 8: Read the summary file content
    try:
        summary_file = Path('/usr/local/app/data/txt/') / f"{summarization_file_path}.txt"
        with open(summary_file, "r", encoding="utf-8") as f:
            summary_content = f.read()
        logger.info(f"Successfully read summary content ({len(summary_content)} characters)")
    except Exception as e:
        logger.error(f"Failed to read summary file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read summary file: {str(e)}")
    
    # Step 9: Return result to user
    return {
        "filename": str(summarization_file_path),
        "summary": summary_content,
        "processing_time_seconds": round(elapsed_time, 2)
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")