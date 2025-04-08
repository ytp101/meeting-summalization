from fastapi import FastAPI, HTTPException
import uvicorn
import os  
from pydantic import BaseModel 
import asyncio
from fastapi.responses import JSONResponse 
from fastapi.encoders import jsonable_encoder
import logging 

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.info("preprocess is setup and running")

class FilePath(BaseModel):
    filename: str 
    ext: str

BASE_DIR = "/home/user/meeting-summalization/database/input/"
BASE_DIR_WAV = "/home/user/meeting-summalization/database/wav/"

app = FastAPI() 

@app.get("/")
def running():
    return {"preprocess service is running"}

@app.post("/preprocess/")
async def preprocess(filepath: FilePath):
    logging.info("try to recevied filepath")
    try: 
        result = filepath.model_dump()  
        input_file_name_request = result['filename']
        ext = str(result["ext"])
        logger.info(f"got file name: {input_file_name_request} with ext: {ext}")
    except Exception as e: 
        logger.error(f"failed to recevied file: {e}")
        raise HTTPException(status_code=500, detail="Something is wrong")
    
    input_file_name = os.path.join(BASE_DIR, input_file_name_request + ext)
    output_file_name = os.path.join(BASE_DIR_WAV, input_file_name_request + ".wav")

    command = [
        "ffmpeg", "-i", str(input_file_name),
        "-vn", "-ar", "16000", "-ac", "1",
        "-c:a", "pcm_s16le", "-af", "loudnorm", str(output_file_name)
    ]

    logger.info(f"preprocessing {input_file_name} with {command} save to {output_file_name}")
    
    process = await asyncio.create_subprocess_exec(
        *command, 
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    assert process.stderr is not None 
    while True: 
        line = await process.stderr.readline()
        if not line: 
            break 
        logger.info(line.decode().strip())
    
    await process.wait()

    if process.returncode != 0: 
        logger.error("ffmpeg processing failed")
        raise HTTPException(status_code=500, detail="FFmpeg processing failed")
    
    preprocess_file_path = os.path.join(input_file_name_request)
    filepath_dict = [
        {
            "preprocessd_file_path": str(preprocess_file_path)
        }
    ]

    logging.info(f"sending file path back to gateway with: {preprocess_file_path}")

    return JSONResponse(content=jsonable_encoder(filepath_dict))


if __name__ == "__main__":
    uvicorn.run(app, port=8001)