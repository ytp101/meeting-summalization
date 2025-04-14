from fastapi import FastAPI, HTTPException
import torch
import uvicorn 
import os 
from transformers import pipeline
from pydantic import BaseModel 
from fastapi.responses import JSONResponse 
from fastapi.encoders import jsonable_encoder
import logging

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logger.info("whisper is set up and running")

class FilePath(BaseModel):
    filename: str 

# Ensure these directories exist and are accessible to the app user
BASE_DIR_WAV = "/usr/local/app/data/wav/"
BASE_DIR_TXT = "/usr/local/app/data/txt/"

# Create directories if they don't exist
os.makedirs(BASE_DIR_WAV, exist_ok=True)
os.makedirs(BASE_DIR_TXT, exist_ok=True)

device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
model_id = "openai/whisper-large-v3-turbo"

whisper = pipeline(
    "automatic-speech-recognition", 
    model=model_id, 
    torch_dtype=torch_dtype,  # Use the correct dtype based on device
    device=device,
    generate_kwargs={"language":"th"}
)

logger.info(f"whisper service running with device: {device} with model: {model_id}")

app = FastAPI() 

@app.get("/")
def running():
    return {"message": "whisper service is running"}

@app.post("/whisper/")
async def transcribe(filepath: FilePath):
    logger.info("try to recevied filepath")
    try:
        result = filepath.model_dump()  
        input_file_name_request = result['filename']
        logger.info(f"got file name: {input_file_name_request}")
    except Exception as e:
        logger.error(f"failed to recevied file: {e}")
        raise HTTPException(status_code=500, detail="Something is wrong")

    input_file_name = os.path.join(BASE_DIR_WAV, input_file_name_request + ".wav")
    output_file_name = os.path.join(BASE_DIR_TXT, input_file_name_request + ".txt")

    logger.info(f"transcripting {input_file_name} with model, will save to {output_file_name}")
    
    # Check if input file exists
    if not os.path.exists(input_file_name):
        logger.error(f"Input file not found: {input_file_name}")
        raise HTTPException(status_code=404, detail="Input file not found")
        
    transcription = whisper(input_file_name)

    with open(output_file_name, "w") as file_output:
        file_output.write(transcription['text'])

    # Return just the filename without path
    filepath_dict = [
        {
            "trancription_file_path": input_file_name_request + ".txt"
        }
    ]

    logger.info(f"sending file path transcription back to gateway: {input_file_name_request + '.txt'}")
    return JSONResponse(content=jsonable_encoder(filepath_dict))

if __name__ == "__main__":
    uvicorn.run(app, port=8002)