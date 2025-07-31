# 🔊 Speaker Diarization Service

A FastAPI-based microservice for speaker diarization using the [`pyannote-audio`](https://github.com/pyannote/pyannote-audio) pipeline.  
Given a WAV audio file, the service detects and segments individual speaker turns.
<!-- TODO: write new docker -->
---

## 🚀 Features

- 🧠 Hugging Face model integration (`pyannote/speaker-diarization-3.1`)
- 🎯 Accurate speaker segmentation from WAV files
- ⚡ Lazy-loaded pipeline (loads only when needed)
- ✅ RESTful endpoints with OpenAPI docs
- 🧪 Mockable, testable, and ready for CI/CD

---

## 📦 Tech Stack

- [FastAPI](https://fastapi.tiangolo.com/)
- [PyAnnote-Audio](https://github.com/pyannote/pyannote-audio)
- [Torch + torchaudio](https://pytorch.org/)
- Pydantic, Uvicorn, HTTPX (for testing)

---

## 🧩 API Endpoints

| Method | Endpoint           | Description                            |
|--------|--------------------|----------------------------------------|
| `GET`  | `/`                | Liveness probe                         |
| `GET`  | `/healthcheck`     | Load model if not yet loaded, return status |
| `POST` | `/diarization/`    | Process audio file and return speaker segments |

### 📥 Diarization Request

```json
POST /diarization/
Content-Type: application/json

{
  "audio_path": "/path/to/audio.wav"
}

// ~/meeting-summalization/backend$ PYTHONPATH=. pytest diarization/tests