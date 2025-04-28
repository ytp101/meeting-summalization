"""
Gateway Service for Meeting Summarization Pipeline
---------------------------------------------------

This FastAPI service acts as a gateway that orchestrates a multi-stage pipeline for meeting summarization, 
handling file uploads, preprocessing, transcription, and summarization by communicating with dedicated microservices.

Main Responsibilities:
- Accept `.mp4` meeting recordings via `/uploadfile/`.
- Forward the recording filename to the Preprocessing service (`/preprocess/`) to extract and normalize audio.
- Send preprocessed audio to the Whisper service (`/whisper/`) for transcription.
- Pass transcription text to the Summarization service (`/summarization/`) for summarizing the content.
- Return the final summarized text along with the original filename and processing time to the user.

Supporting Features:
- `/` (root endpoint): Basic "service is alive" check.
- `/healthcheck`: Verifies health of all dependent services (preprocess, whisper, summarization).
- Structured logging for each critical step.
- Automatic directory creation for uploaded files.
- Timeout and error handling for external service calls.
- Environment variables allow flexible endpoint and timeout configuration.

Environment Variables:
- `BASE_DIR`: Base directory to save uploaded `.mp4` files (default: `/usr/local/app/data/mp4/`).
- `PREPROCESS_SERVICE_URL`: URL for the preprocessing service.
- `WHISPER_SERVICE_URL`: URL for the whisper transcription service.
- `SUMMARIZATION_SERVICE_URL`: URL for the summarization service.
- `REQUEST_TIMEOUT`: Timeout for requests to external services (default: 1200 seconds / 20 minutes).
- `PORT`: Port to serve the FastAPI app (default: 8000).

Requirements:
- Python 3.8+
- FastAPI
- Uvicorn
- httpx
- pydantic

Notes:
- Only `.mp4` uploads are currently supported (future enhancement: support `.mp3` too).
- Services are expected to be accessible via Docker DNS naming.

---
Written with care. Powered by FastAPI, caffeine, and a healthy fear of missing a timeout.
"""


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

# due to dns (docker bridge network) i will auto assign dns by service name
# endpoint of each service 
PREPROCESS_ENDPOINT = os.getenv('PREPROCESS_SERVICE_URL', 'http://preprocess:8001/preprocess/')
WHISPER_ENDPOINT = os.getenv('WHISPER_SERVICE_URL', 'http://whisper:8002/whisper/')
SUMMARIZATION_ENDPOINT = os.getenv('SUMMARIZATION_SERVICE_URL', 'http://summarization:8003/summarization/')

# default request timeout (20mins)
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 1200))

# Create directories if they don't exist (directory for store mp4)
os.makedirs(BASE_DIR, exist_ok=True)

# Setup FastAPI service
app = FastAPI(title="Meeting Summarization Gateway")

# define object model for each service status 
class ServiceStatus(BaseModel):
    service: str
    status: str
    message: Optional[str] = None

# /(root) for peace of mind 
@app.get("/")
def running():
    return {"status": "Gateway service is running"}

# /healthcheck endpoint of checking all service (preprocess, whisper, summarization) by each /(root) of each service 
@app.get("/healthcheck")
async def healthcheck():
    """Check if all services are available"""
    results = []
    
    async with httpx.AsyncClient() as client:
        for service, url in [
            # replace endpoint Ex: /preprocess with / for check runing of each service 
            ("preprocess", PREPROCESS_ENDPOINT.replace("/preprocess/", "/")),
            ("whisper", WHISPER_ENDPOINT.replace("/whisper/", "/")),
            ("summarization", SUMMARIZATION_ENDPOINT.replace("/summarization/", "/"))
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

# main purpose of this code /uploadfile/
@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    """Process an uploaded meeting recording"""
    # time the process 
    start_time = time.time()

    # logging file name 
    logger.info(f"Received file: {file.filename}")
    
    # Validate file type (from now support only mp4) 
    # TODO: make code support mp3 
    if not file.filename.lower().endswith('.mp4'):
        logger.error(f"Invalid file type: {file.filename}")
        raise HTTPException(status_code=400, detail="Only MP4 files are supported")
    
    # Step 1: Save uploaded file
    try:
        file_path = Path(BASE_DIR) / file.filename
        
        # .stem is like get the last part of file path above so it is a [filename.extension]
        file_name = file_path.stem
        
        # save file
        with open(file_path, "wb") as file_upload:
            contents = await file.read()
            file_upload.write(contents)
        logger.info(f"File saved to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(status_code=500, detail=f"Gateway failed to save file: {str(e)}")
    
    # Step 2: Send to preprocess service (it will access file from /mp4 and save to /wav)
    # TODO: remodular code to function based

    # logging file name 
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
    
    # Step 4: Send to whisper service (it will get file from /wav and save to /txt)
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
    
    # Step 6: Send to summarization service (it will get /txt and save to /txt but with _summalized)
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
    
    # Step 8: Read the summary file content (to preprare to send to user)
    try:
        summary_file = Path('/usr/local/app/data/txt/') / f"{summarization_file_path}.txt"
        with open(summary_file, "r", encoding="utf-8") as f:
            summary_content = f.read()
        logger.info(f"Successfully read summary content ({len(summary_content)} characters)")
    except Exception as e:
        logger.error(f"Failed to read summary file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read summary file: {str(e)}")
    
    # Step 9: Return result(filename, summary, precessing_time in second) to user
    return {
        "filename": str(summarization_file_path),
        "summary": summary_content,
        "processing_time_seconds": round(elapsed_time, 2)
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")