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
    try: 
        contents = file.file.read()
        file_path = os.path.join(BASE_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception: 
        raise HTTPException(status_code=500, detail="Something is wrong")
    finally:
        file.file.close()
    return {"message": f"Successfully uploaded {file.filename}, filepath: {file_path}"}

if __name__ == "__main__":
    uvicorn.run(app, port=8000)