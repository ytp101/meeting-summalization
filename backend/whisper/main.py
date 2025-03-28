from fastapi import FastAPI, HTTPException
import torch
import uvicorn 
import os 
from transformers import pipeline
from pydantic import BaseModel 

class FilePath(BaseModel):
    filename: str 

BASE_DIR_WAV = "/home/user/meeting-summalization/database/wav/"
BASE_DIR_TXT = "/home/user/meeting-summalization/database/txt/"

device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
model_id = "openai/whisper-large-v3-turbo"

whisper = pipeline(
    "automatic-speech-recognition", 
    model=model_id, 
    torch_dtype=torch.float16, 
    device=device,
    generate_kwargs={"language":"th"}
)

app = FastAPI() 

@app.get("/")
def running():
    return {"message": "whisper service is running"}

@app.post("/whisper/")
async def transcribe(filepath: FilePath):
    try:
        input_file_name_request = filepath.filename
    except Exception:
        print(Exception)
        raise HTTPException(status_code=500, detail="Something is wrong")

    input_file_name = os.path.join(BASE_DIR_WAV, input_file_name_request + ".wav")
    output_file_name = os.path.join(BASE_DIR_TXT, input_file_name_request + ".txt")

    transcription = whisper(input_file_name)

    with open(output_file_name, "w") as file_output:
        file_output.write(transcription['text'])
    
    return {"message": f"Successsful transcribe {input_file_name} to {output_file_name} with {model_id}"}

if __name__ == "__main__":
    uvicorn.run(app, port=8002)