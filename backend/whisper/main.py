from fastapi import FastAPI, HTTPException
import torch
import uvicorn
import os
import gc
from transformers import pipeline
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import logging
from pathlib import Path
import time

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.info("Whisper service is starting up")

class FilePath(BaseModel):
    filename: str

# Environment variables with defaults
BASE_DIR_WAV = os.getenv('BASE_DIR_WAV', '/usr/local/app/data/wav/')
BASE_DIR_TXT = os.getenv('BASE_DIR_TXT', '/usr/local/app/data/txt/')
MODEL_ID = os.getenv('MODEL_ID', 'openai/whisper-large-v3-turbo')
LANGUAGE = os.getenv('LANGUAGE', 'th')
HF_HOME = os.getenv('HF_HOME', '/home/app/.cache')

# Set HuggingFace cache environment variable
os.environ['HF_HOME'] = HF_HOME

# Create directories if they don't exist
os.makedirs(BASE_DIR_WAV, exist_ok=True)
os.makedirs(BASE_DIR_TXT, exist_ok=True)
os.makedirs(HF_HOME, exist_ok=True)

# Setup device and model
app = FastAPI(title="Whisper Speech-to-Text Service")

# Global variable to hold the model
whisper_model = None

def get_whisper_model():
    """Load the Whisper model if it's not already loaded"""
    global whisper_model
    if whisper_model is None:
        try:
            device = "cuda:0" if torch.cuda.is_available() else "cpu"
            torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
            
            logger.info(f"Loading model {MODEL_ID} on {device} with {torch_dtype}")
            whisper_model = pipeline(
                "automatic-speech-recognition",
                model=MODEL_ID,
                torch_dtype=torch_dtype,
                device=device,
                generate_kwargs={"language": LANGUAGE},
                return_timestamps=True,
                chunk_length_s=30,
                batch_size=1
            )
            logger.info(f"Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise RuntimeError(f"Failed to load Whisper model: {e}")
    return whisper_model

@app.on_event("startup")
async def startup_event():
    """Load model on startup"""
    try:
        get_whisper_model()
    except Exception as e:
        logger.error(f"Failed to load model on startup: {e}")
        # We'll continue but will try again on first request

@app.get("/")
def running():
    """Health check endpoint"""
    return {
        "status": "Whisper service is running",
        "model": MODEL_ID,
        "device": "cuda" if torch.cuda.is_available() else "cpu"
    }

@app.get("/healthcheck")
def healthcheck():
    """Check model and GPU status"""
    gpu_info = {}
    
    if torch.cuda.is_available():
        gpu_info["available"] = True
        gpu_info["device_count"] = torch.cuda.device_count()
        gpu_info["current_device"] = torch.cuda.current_device()
        gpu_info["device_name"] = torch.cuda.get_device_name(0)
        
        # Get memory info if possible
        try:
            gpu_info["memory_allocated"] = f"{torch.cuda.memory_allocated(0) / 1024**3:.2f} GB"
            gpu_info["memory_reserved"] = f"{torch.cuda.memory_reserved(0) / 1024**3:.2f} GB"
        except Exception:
            pass
    else:
        gpu_info["available"] = False
    
    model_loaded = whisper_model is not None
    
    return {
        "status": "healthy" if model_loaded else "initializing",
        "model": MODEL_ID,
        "model_loaded": model_loaded,
        "gpu": gpu_info,
    }

@app.post("/whisper/")
async def transcribe(filepath: FilePath):
    """Transcribe audio file using Whisper"""
    start_time = time.time()
    logger.info("Received transcription request")
    
    try:
        result = filepath.model_dump()
        input_file_name_request = result['filename']
        logger.info(f"Processing file: {input_file_name_request}")
    except Exception as e:
        logger.error(f"Failed to process request: {e}")
        raise HTTPException(status_code=400, detail="Invalid request format")
    
    input_file = Path(BASE_DIR_WAV) / f"{input_file_name_request}.wav"
    output_file = Path(BASE_DIR_TXT) / f"{input_file_name_request}.txt"
    
    # Check if input file exists
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        raise HTTPException(status_code=404, detail="Input file not found")
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Get or load the model
    try:
        model = get_whisper_model()
    except Exception as e:
        logger.error(f"Failed to initialize model: {e}")
        raise HTTPException(status_code=500, detail=f"Model initialization failed: {str(e)}")
    
    # Perform transcription
    try:
        logger.info(f"Starting transcription of {input_file}")
        transcription = model(str(input_file))
        
        with open(output_file, "w", encoding="utf-8") as file_output:
            # Handle both timestamped and non-timestamped outputs
            if isinstance(transcription, dict) and 'chunks' in transcription:
                # For timestamped output
                full_text = ""
                for chunk in transcription['chunks']:
                    full_text += chunk['text'] + " "
                file_output.write(full_text.strip())
            else:
                # For regular output
                file_output.write(transcription['text'])
        
        elapsed_time = time.time() - start_time
        logger.info(f"Transcription completed in {elapsed_time:.2f} seconds")
        
        # Clean up GPU memory if using CUDA
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            gc.collect()
            
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    
    # Return the filename without path or extension
    filepath_dict = [
        {
            "trancription_file_path": input_file_name_request
        }
    ]
    
    return JSONResponse(content=jsonable_encoder(filepath_dict))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")