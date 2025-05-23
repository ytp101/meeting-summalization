"""
Summarization Service for Meeting Summarization Pipeline
---------------------------------------------------------

This FastAPI service generates concise summaries from meeting transcription text files 
by utilizing an LLM model (such as Llama3) via the Ollama API.

Main Responsibilities:
- Accept a `.txt` filename via `/summarization/` endpoint.
- Read the corresponding transcription file.
- Send the transcription to an Ollama LLM endpoint with a summarization prompt.
- Save the generated summary to a new `_summarized.txt` file.
- Return the output filename (without extension) for downstream usage or client retrieval.

Supporting Features:
- `/` (root endpoint): Basic service healthcheck.
- `/healthcheck`: Verify Ollama API availability and confirm the presence of the target model.
- Structured logging at every important step of the flow.
- Timeout handling for Ollama API calls to prevent long hangs.
- Dynamic request construction with configurable system prompts, token limits, and temperature settings.

Environment Variables:
- `BASE_DIR_TXT`: Directory path for input and output `.txt` files (default: `/usr/local/app/data/txt/`).
- `MODEL_ID`: Target LLM model ID hosted by Ollama (default: `llama3`).
- `OLLAMA_HOST`: Host URL for the Ollama API (default: `http://localhost:11434`).
- `SYSTEM_PROMPT`: Instruction prompt sent to guide the summarization output.
- `MAX_TOKENS`: Maximum number of tokens allowed in the model prediction (default: 4096).
- `TEMPERATURE`: Sampling temperature for model creativity (default: 0.2).
- `REQUEST_TIMEOUT`: Timeout for API requests to Ollama (default: 300 seconds).
- `PORT`: Port to serve the FastAPI app (default: 8003).

Requirements:
- Python 3.8+
- FastAPI
- Uvicorn
- httpx

Notes:
- Input `.txt` transcription files must already exist.
- Ollama service must be accessible and have the required model loaded.

---
Fueled by FastAPI, Ollama, and the existential dread of listening to 3-hour meetings in real-time.
"""

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

# 5mins timeout 
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 300)) 

# Create directories if they don't exist
os.makedirs(BASE_DIR_TXT, exist_ok=True)

app = FastAPI(title="Meeting Summarization Service")

# / (root) for gateway healthcheck 
@app.get("/")
def running():
    return {"status": "Summarization service is running"}

# for individual healthcheck 
@app.get("/healthcheck")
async def healthcheck():
    """Check if Ollama service is accessible"""
    try:
        async with httpx.AsyncClient() as client:
            # send request to ollama endpoint 
            response = await client.get(
                f"{OLLAMA_HOST}/api/tags",
                timeout=5.0
            )
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                
                # check if MODEL_ID is had been in ollama service 
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

# main part of this service (read txt send to ollama service and save to txt file)
@app.post("/summarization/")
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
    
    logger.info(f"Content: {input_data}")
    # Prepare request for Ollama
    request_data = {
        "model": MODEL_ID,
        "prompt": f"summalize this transcription: {input_data}",
        "stream": False,
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
                # f"{OLLAMA_HOST}/api/chat",
                f"{OLLAMA_HOST}/api/generate",
                json=request_data,
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama API returned status {response.status_code}: {response.text}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Ollama API error: {response.text}"
                )
        
        # read response status code 
        logger.info(f"Response status: {response.status_code}")
        
        # parse json response 
        response_json = response.json()
        
        logger.info(f"Response Json: {response_json}")
        
        # extract text
        summary = response_json.get("response")
        logger.info(summary)
            
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
            "summarization_file_path": output_filename
        }
    ]
    
    return JSONResponse(content=jsonable_encoder(filepath_dict))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")