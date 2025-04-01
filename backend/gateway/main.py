from fastapi import FastAPI, UploadFile, HTTPException
import uvicorn
import os  
import httpx
from pathlib import Path 

BASE_DIR = "/home/user/meeting-summalization/database/mp4/"

# Service Endpoint 
PREPROCESS_ENDPOINT = "http://127.0.0.1:8001/preprocess/"
WHISPER_ENDPOINT = "http://127.0.0.1:8002/whisper/"
SUMMLIZATION_ENDPOINT = "http://127.0.0.1:8003/summlization/"

app = FastAPI() 

@app.get("/")
def running():
    return {"gateway service is running"}

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    # step 1: gateway accept user uploaded file
    try: 
        contents = await file.read()
        file_path = os.path.join(BASE_DIR, file.filename)
        file_name = str(Path(file_path).stem)
        with open(file_path, "wb") as file_upload:
            file_upload.write(contents)
    except Exception: 
        raise HTTPException(status_code=500, detail="gateway failed to save file")

    # step 2: gateway send file path to preprocess file 
    try:
        async with httpx.AsyncClient() as client: 
            preprocesss_response = await client.post(
                PREPROCESS_ENDPOINT,
                json={"filename": file_name},
                timeout=120
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"preprocess failed: {str(e)}")
    
    # step 3: preprocess send file path (preprocessed back to gateway)
    preprocessed_file_path = preprocesss_response.json()[0]['preprocessd_file_path']

    # step 4: gateway send file path (preprocessed to whisper)
    try:
        async with httpx.AsyncClient() as client: 
            trancription_response = await client.post(
                WHISPER_ENDPOINT,
                json={"filename": preprocessed_file_path},
                timeout=60*20
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"whisper failed: {str(e)}")

    # step 5: whisper send file path (transciption) back to gateway 
    trancription_file_path = trancription_response.json()[0]['trancription_file_path']

    # step 6: gateway send file path (transcription) to summlization 
    try:
        async with httpx.AsyncClient() as client: 
            summalization_response = await client.post(
                SUMMLIZATION_ENDPOINT,
                json={"filename": trancription_file_path},
                timeout=60*20
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"summlization failed: {str(e)}")

    # step 7: summalization send file path (summlized) to gateway 
    summlization_file_path = summalization_response.json()[0]['summalization_file_path']

    # step 8: return summalized back to user 
    return str(summlization_file_path)

if __name__ == "__main__":
    uvicorn.run(app, port=8000)