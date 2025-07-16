# 🎧 Audio Preprocessor Service

## Overview

This microservice converts input audio/video files into normalized 16-bit PCM mono WAV format using FFmpeg. It is designed as the **second stage** in an audio processing pipeline—executed before **Diarization** and **ASR** (e.g., Whisper).

---

## ✨ Features

- 🔁 Converts multi-format media (MP4, MKV, etc.) to `.wav`
- 🎚️ Applies loudness normalization (`loudnorm`)
- 🎵 Outputs 16 kHz, mono, 16-bit PCM WAV format
- 🚥 Includes healthcheck and service liveness endpoints
- 🧠 Designed for container-based pipelines (Docker)
- 🛡️ Planned support for internal-only API access (secure-by-design)

---

## 📦 Project Structure
```bash
+-- preprocess/
├── main.py # FastAPI app entrypoint
├── routers/
│ ├── root.py # Root '/' liveness endpoint
│ ├── healthcheck.py # Dependency check (FFmpeg)
│ └── preprocess.py # Preprocess endpoint
├── services/
│ └── audio_preprocessor.py # FFmpeg call logic
├── models/
│ └── preprocess_request.py # Pydantic request model
├── utils/
│ ├── logger.py # Global logger
│ └── ffmpeg_checker.py # FFmpeg availability check
├── config/
  └── settings.py # Timeout config
```

---

## 🚀 API Endpoints

| Method | Route              | Description                        |
|--------|-------------------|------------------------------------|
| `GET`  | `/`               | Service liveness check             |
| `GET`  | `/healthcheck`    | FFmpeg dependency health check     |
| `POST` | `/preprocess/`    | Convert media to normalized `.wav` |

---

## 🔧 Preprocessing Details

- Input: Video/audio file path
- Output: WAV file written to target directory
- Internal call:
  ```bash
  ffmpeg -y -i input.mp4 -vn -ar 16000 -ac 1 -c:a pcm_s16le -af loudnorm output.wav

### 🛠 Startup Behavior
On service startup, the application performs a dependency check to ensure FFmpeg is available:

```python
@asynccontextmanager
async def lifespan(app: FastAPI): 
    if await is_ffmpeg_available():
        logger.info("FFmpeg is available")
    else:
        logger.error("FFmpeg is not installed. Please install it first.")
    
    yield

    logger.info("Shutting down Audio Preprocessor")
```


### 📥 Example Request
POST (`/prepocess`)
```json
{
    "input_path": "/data/upload/video.mp4",
    "output_dir": "/data/output/"
}
```

Response: 
```json 
[
    {
        "preprocessed_file_path": "/data/output/video.wav"
    }
]
```

### TODO
- [ ] Add security/auth middleware
- [x] Write unit tests for core services 
- [ ] Rewrite Dockerfile for production 
- [ ] Enable logging to file per process 

### 📄 Requirements 
- Python 3.11+
- FastAPI
- FFmpeg (must be installed in runtime environment)

### 🧑‍💻 Author
- yodsran 

### 📌 Note
This service is intended to run internally as part of a multi-stage AI pipeline and is not exposed to the public internet.

<!-- Test command -->
<!-- ~/meeting-summalization/backend$ PYTHONPATH=. pytest ./preprocess/tests -->