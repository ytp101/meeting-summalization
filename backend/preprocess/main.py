from fastapi import FastAPI, HTTPException
import uvicorn
import os
import asyncio
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.info("Preprocess service is starting up")

class FilePath(BaseModel):
    filename: str

# Environment variables with defaults
# setup directory for mp4 (access) and wav to get file from 
BASE_DIR_MP4 = os.getenv('BASE_DIR_MP4', '/usr/local/app/data/mp4/')
BASE_DIR_WAV = os.getenv('BASE_DIR_WAV', '/usr/local/app/data/wav/')

# timeout for ffmpeg processing
FFMPEG_TIMEOUT = int(os.getenv('FFMPEG_TIMEOUT', 600)) 

# Create directories if they don't exist
os.makedirs(BASE_DIR_MP4, exist_ok=True)
os.makedirs(BASE_DIR_WAV, exist_ok=True)

# Check if ffmpeg is available (on start)
try:
    ffmpeg_version = asyncio.run(asyncio.create_subprocess_exec(
        "ffmpeg", "-version",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    ))
    logger.info("FFmpeg is available")
except Exception as e:
    logger.error(f"FFmpeg is not available: {e}")
    # We'll continue but log the error

# setup title of the service
app = FastAPI(title="Meeting Audio Preprocessor")

# / (root) for gateway healthcheck 
@app.get("/")
def running():
    return {"status": "Preprocess service is running"}

# in case of individual health check (use to check ffmpeg service)
@app.get("/healthcheck")
async def healthcheck():
    """Check if service dependencies are available"""
    try:
        process = await asyncio.create_subprocess_exec(
            "ffmpeg", "-version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.wait()
        if process.returncode == 0:
            return {"status": "healthy", "ffmpeg": "available"}
        else:
            return {"status": "degraded", "ffmpeg": "error"}
    except Exception as e:
        return {"status": "unhealthy", "ffmpeg": "unavailable", "error": str(e)}

# main purpose of this service recevied mp4 (/mp4) file name then process by ffmpeg and save to .wav (wav)
@app.post("/preprocess/")
async def preprocess(filepath: FilePath):
    """Convert MP4 video to WAV audio format optimized for transcription"""
    logger.info("Received file path request")
    
    try:
        # dump json request
        result = filepath.model_dump()
        request_file_name = result['filename']
        logger.info(f"Processing file: {request_file_name}")
    except Exception as e:
        logger.error(f"Failed to process request: {e}")
        raise HTTPException(status_code=400, detail="Invalid request format")

    # construct input file name and output file name (to use in ffmpeg)
    input_file = Path(BASE_DIR_MP4) / f"{request_file_name}.mp4"
    output_file = Path(BASE_DIR_WAV) / f"{request_file_name}.wav"
    
    # Check if input file exists
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        raise HTTPException(status_code=404, detail="Input file not found")
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare ffmpeg command
    command = [
        "ffmpeg", "-i", str(input_file),
        "-vn",                  # Disable video
        "-ar", "16000",         # Sample rate: 16kHz
        "-ac", "1",             # Mono channel
        "-c:a", "pcm_s16le",    # 16-bit PCM
        "-af", "loudnorm",      # Normalize audio volume
        str(output_file)
    ]
    
    logger.info(f"Running command: {' '.join(command)}")
    
    try:
        # subprocess according to ffmpeg command above
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Create timeout task
        try:
            # wait for process 
            # TODO: understand asyncio and process 
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=FFMPEG_TIMEOUT)
            
            # Log any error output
            if stderr:
                for line in stderr.decode().splitlines():
                    if line.strip():
                        logger.info(f"FFmpeg: {line.strip()}")
            
            if process.returncode != 0:
                logger.error(f"FFmpeg processing failed with code {process.returncode}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"FFmpeg failed: {stderr.decode() if stderr else 'Unknown error'}"
                )
                
        except asyncio.TimeoutError:
            # Kill the process if it times out
            try:
                process.kill()
            except Exception:
                pass
            logger.error(f"FFmpeg process timed out after {FFMPEG_TIMEOUT} seconds")
            raise HTTPException(status_code=504, detail=f"FFmpeg process timed out")
    
    except Exception as e:
        logger.error(f"Error during audio conversion: {e}")
        raise HTTPException(status_code=500, detail=f"Audio conversion failed: {str(e)}")
    
    # Check if output file was created
    if not output_file.exists():
        logger.error("Output file was not created")
        raise HTTPException(status_code=500, detail="Output file was not created")
    
    # Return file path without extension
    filepath_dict = [
        {
            "preprocessd_file_path": request_file_name
        }
    ]
    
    logger.info(f"Preprocessing complete. Output: {output_file}")
    return JSONResponse(content=jsonable_encoder(filepath_dict))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")