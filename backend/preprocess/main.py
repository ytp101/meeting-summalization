from fastapi import FastAPI, HTTPException
import uvicorn
import os  
from pydantic import BaseModel 
import asyncio

class FilePath(BaseModel):
    filename: str 

BASE_DIR_MP4 = "/home/user/meeting-summalization/database/mp4/"
BASE_DIR_WAV = "/home/user/meeting-summalization/database/wav/"

app = FastAPI() 

@app.get("/")
def running():
    return {"preprocess service is running"}

@app.post("/preprocess/")
async def preprocess(filepath: FilePath):
    try: 
        result = filepath.model_dump()  
        input_file_name_request = result['filename']
    except Exception: 
        raise HTTPException(status_code=500, detail="Something is wrong")
    
    input_file_name = os.path.join(BASE_DIR_MP4, input_file_name_request + ".mp4")
    output_file_name = os.path.join(BASE_DIR_WAV, input_file_name_request + ".wav")
    # TODO: make service/gateway/main.py to send file path (filename: "test_video")

    command = [
        "ffmpeg", "-i", str(input_file_name),
        "-vn", "-ar", "16000", "-ac", "1",
        "-c:a", "pcm_s16le", "-af", "loudnorm", str(output_file_name)
    ]

    process = await asyncio.create_subprocess_exec(
        *command, 
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0: 
        error_msg = stderr.decode().strip()
        raise HTTPException(status_code=500, detail="FFmpeg processing failed")

    return {"message": f"Sucessful Process {input_file_name} to {output_file_name} with {command}"}


if __name__ == "__main__":
    uvicorn.run(app, port=8001)