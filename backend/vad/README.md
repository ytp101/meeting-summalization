# VAD (Voice Activity Detection) Service 

## Overview 

This microservice analyzes audio files to detect **speech segments** using a VAD model (e.g., Silero VAD). It is designed as the **third stage** in an audio processing pipeline—executed **after preprocessing and before speaker diarization or ASR (Whisper).**

---

## ✨ Features

- 🎵 Outputs 16 kHz, mono, 16-bit PCM WAV format
- 🪚 Splits long audio into speech-only chunks
- 🎯 Outputs timestamps (start, end) of speech regions
- 🪵 Optional: Save audio chunks to disk
- 🚥 Healthcheck and service liveness endpoints included
- 🛡️ Designed for internal secure microservice pipelines (Docker-ready)

---

## 📦 Project Structure
```bash 
+-- vad/
├── main.py # FastAPI app entrypoint
├── routers/
│ ├── root.py # Root '/' liveness endpoint
│ ├── healthcheck.py # Dependency check (FFmpeg)
│ └── vad.py # VAD endpoint
├── services/
│ └── vad_service.py # FFmpeg call logic
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
|--------|-------------------|-------------------------------------|
| `GET`  | `/`               | Service liveness check              |
| `GET`  | `/healthcheck`    | Dependency check (model)            |
| `POST` | `/vad/`           | Perform VAD on WAV input            |

---

##  🧪 VAD Behavior

- Input: WAV audio file path
- Output: 
    - JSON list of speech segments 
    - (Optional) saved `wav` chunks for each segment
- Internal logic:
  ```python
  await asyncio.to_thread(vad_pipeline, file_path)
- Process waveform
- Predict voice probabilities 
- Return regions with speech (thresholded)

### 🛠 Startup Behavior
On service startup, the application performs a dependency check to ensure VAD model is available:

```python
@asynccontextmanager
async def lifespan(app: FastAPI): 
    logger.info("🚀 Loading VAD model...")
    await load_vad_model()
    logger.info("✅ VAD model ready")
    yield
```

### 📥 Example Request
POST (`/vad/`)
<!-- TODO: implement chunk folder chunk logic -->
```json
{
    "input_path": "/data/{work_id}/converted/video.mp4",
    "output_dir": "/data/{work_id}/chunk/"
}
```

Response: 
```json 
[
    {
        "start": 3.12, 
        "end": 7.85, 
        "segment_path": "/data/{work_id}/chunk/audio_000.wav"
    },
    {
        "start": 12.01, 
        "end": 17.49, 
        "segment_path": "data/{work_id}/chunk/audio_001.wav"
    }
]
```

🧪 Optional Enhancements
<!-- TODO: must do -->
- [ ] Write new docker image
 <!--  -->
- [ ] Optional: make VAD log to file
- [ ] Make VAD Output as Chunk
- [ ] Add `min_speech_sec` and `min_silence_sec` params
- [ ] Support batch mode
- [ ] Model selection via config
- [x] Unit tests for segment logic

### 📄 Requirements 
- Python 3.11+
- FastAPI
- pyannote.audio

### 🧑‍💻 Author
- yodsran 

### 📌 Note
This service is intended to run internally as part of a multi-stage AI pipeline and is not exposed to the public internet.

<!-- Test command -->
<!-- ~/meeting-summalization/backend$ PYTHONPATH=. pytest ./vad/tests -->