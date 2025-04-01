from fastapi import FastAPI, HTTPException
import uvicorn
import os 
from pydantic import BaseModel
from ollama import chat 
from ollama import ChatResponse 
from fastapi.responses import JSONResponse 
from fastapi.encoders import jsonable_encoder 

class FilePath(BaseModel):
    filename: str 

BASE_DIR_TXT = "/home/user/meeting-summalization/database/txt/"
MODEL_ID = "llama3"

app = FastAPI()

@app.get("/")
def running():
    return {"message": "summalization service is running"}

@app.post("/summlization/")
async def summlization(filepath: FilePath):
    try:
        result = filepath.model_dump()
        input_file_name_request = result['filename']
    except Exception:
        print(Exception)
        raise HTTPException(status_code=500, detail="Something is wrong")
    
    input_file_name = os.path.join(BASE_DIR_TXT, input_file_name_request + ".txt")
    output_file_name = os.path.join(BASE_DIR_TXT, input_file_name_request + "_summalized" + ".txt")

    input_data = open(input_file_name, "r").read()

    response: ChatResponse = chat(
        model=MODEL_ID, 
        messages=[
            {"role": "system", "content": "Summarize the following text"}, 
            {"role": "user", "content": input_data}
        ],
        options={"temperature": 0.2}
    )

    with open(output_file_name, "w") as file_output:
        file_output.write(response["message"]["content"])
    
    filepath_dict = [
        {
            "summalization_file_path": str(os.path.join(input_file_name_request + "_summalized")),
        }
    ]

    return JSONResponse(content=jsonable_encoder(filepath_dict))

if __name__ == "__main__":
    uvicorn.run(app, port=8003)