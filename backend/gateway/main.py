from fastapi import FastAPI, UploadFile, HTTPException
import uvicorn
import os  

BASE_DIR = "/home/user/meeting-summalization/database/mp4/"

app = FastAPI() 

@app.get("/")
def running():
    return {"gateway service is running"}

@app.post("/uploadfile/")
def create_upload_file(file: UploadFile):
    # step 1: gateway accept user uploaded file
    try: 
        contents = file.file.read()
        file_path = os.path.join(BASE_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception: 
        raise HTTPException(status_code=500, detail="Something is wrong")
    finally:
        file.file.close()
    # step 2: gateway send file path to preprocess file 

    # step 3: preprocess send file path (preprocessed back to gateway)

    # step 4: gateway send file path (preprocessed to whisper)

    # step 5: whisper send file path (transciption) back to gateway 

    # step 6: gateway send file path (transcription) to summlization 

    # step 7: summalization send file path (summlizaed) to gateway 

    # step 8: return summalized back to user 

if __name__ == "__main__":
    uvicorn.run(app, port=8000)