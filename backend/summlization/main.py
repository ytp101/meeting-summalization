from fastapi import FastAPI, HTTPException
import uvicorn
import os
from pydantic import BaseModel
import httpx
from pathlib import Path
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import logging
import time
import json

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.info("Summarization service is starting up")

class FilePath(BaseModel):
    filename: str

# Environment variables with defaults
BASE_DIR_TXT = os.getenv('BASE_DIR_TXT', '/usr/local/app/data/txt/')
MODEL_ID = os.getenv('MODEL_ID', 'llama3')
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
SYSTEM_PROMPT = os.getenv('SYSTEM_PROMPT', 'Summarize the following meeting transcript. Focus on key decisions, action items, and important discussions. Make the summary concise yet comprehensive.')
MAX_TOKENS = int(os.getenv('MAX_TOKENS', 4096))
TEMPERATURE = float(os.getenv('TEMPERATURE', 0.2))
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 300))  # 5 minutes default

# Create directories if they don't exist
os.makedirs(BASE_DIR_TXT, exist_ok=True)

app = FastAPI(title="Meeting Summarization Service")

@app.get("/")
def running():
    return {"status": "Summarization service is running"}

@app.get("/healthcheck")
async def healthcheck():
    """Check if Ollama service is accessible"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OLLAMA_HOST}/api/tags",
                timeout=5.0
            )
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_available = any(model["name"] == MODEL_ID for model in models)
                
                if model_available:
                    return {"status": "healthy", "ollama": "available", "model": MODEL_ID}
                else:
                    return {
                        "status": "degraded", 
                        "ollama": "available", 
                        "model": "not found",
                        "available_models": [m["name"] for m in models]
                    }
            else:
                return {"status": "degraded", "ollama": f"error {response.status_code}"}
    except Exception as e:
        return {"status": "unhealthy", "ollama": "unavailable", "error": str(e)}

@app.post("/summlization/")
async def summarization(filepath: FilePath):
    """Generate summary of transcription using Ollama"""
    start_time = time.time()
    logger.info("Received summarization request")
    
    try:
        result = filepath.model_dump()
        input_file_name_request = result['filename']
        logger.info(f"Processing file: {input_file_name_request}")
    except Exception as e:
        logger.error(f"Failed to process request: {e}")
        raise HTTPException(status_code=400, detail="Invalid request format")
    
    input_file = Path(BASE_DIR_TXT) / f"{input_file_name_request}.txt"
    output_file = Path(BASE_DIR_TXT) / f"{input_file_name_request}_summarized.txt"
    
    # Check if input file exists
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        raise HTTPException(status_code=404, detail="Input file not found")
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Read input file
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            input_data = f.read()
        
        if not input_data.strip():
            logger.error("Input file is empty")
            raise HTTPException(status_code=400, detail="Input file is empty")
            
        logger.info(f"Input file loaded: {len(input_data)} characters")
    except Exception as e:
        logger.error(f"Failed to read input file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read input file: {str(e)}")
    
    # Prepare request for Ollama
    request_data = {
        "model": MODEL_ID,
        "messages": [
            {
                "role": "system", 
                "content": "You are a meeting summarization assistant. Create a concise and structured summary of the meeting transcript."
            },
            {
                "role": "user", 
                "content": f"Summarize this meeting transcript in Thai language:\n\n{input_data}"
            }
        ],
        "options": {
            "num_predict": int(MAX_TOKENS),
            "temperature": float(TEMPERATURE),
            "context_window": 8192
        }
    }
    
    # Call Ollama API
    try:
        logger.info(f"Sending request to Ollama API at {OLLAMA_HOST}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_HOST}/api/chat",
                json=request_data,
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama API returned status {response.status_code}: {response.text}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Ollama API error: {response.text}"
                )
                
            result = response.json()
            
            if "message" not in result or "content" not in result["message"]:
                logger.error(f"Unexpected response format from Ollama: {result}")
                raise HTTPException(
                    status_code=500,
                    detail="Unexpected response format from Ollama"
                )
                
            summary = result["message"]["content"]
            
    except httpx.TimeoutException:
        logger.error(f"Ollama API request timed out after {REQUEST_TIMEOUT} seconds")
        raise HTTPException(status_code=504, detail="Summarization timed out")
    except Exception as e:
        logger.error(f"Failed to call Ollama API: {e}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")
    
    # Write the summary to output file
    try:
        with open(output_file, "w", encoding="utf-8") as file_output:
            file_output.write(summary)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Summarization completed in {elapsed_time:.2f} seconds. Output: {output_file}")
    except Exception as e:
        logger.error(f"Failed to write output file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to write output file: {str(e)}")
    
    # Return the output filename
    output_filename = f"{input_file_name_request}_summarized"
    filepath_dict = [
        {
            "summalization_file_path": output_filename
        }
    ]
    
    return JSONResponse(content=jsonable_encoder(filepath_dict))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")