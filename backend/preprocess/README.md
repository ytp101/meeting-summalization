# 🔊 Speaker Diarization Service

A FastAPI-based microservice for speaker diarization using the [`pyannote-audio`](https://github.com/pyannote/pyannote-audio) pipeline.  
Given a WAV audio file, the service detects and segments individual speaker turns.

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

diarization/
├── config/        # Settings & environment
├── routers/       # API routes
├── services/      # Model logic & inference
├── models/        # Pydantic request/response schemas
├── utils/         # Logging, model loader
├── tests/         # Pytest + mock-based integration tests
└── main.py        # FastAPI app entrypoint


### 📥 Diarization Request
POST /diarization/
```json
{
  "audio_path": "/path/to/audio.wav"
}
```

#### 📤 Response
```json 
{
  "segments": [
    {
      "start": 0.0,
      "end": 2.45,
      "speaker": "SPEAKER_00"
    },
    ...
  ]
}
```

## ⚙️ Environment Variables
Set these before running the service:
| Variable            | Description                                               |
| ------------------- | --------------------------------------------------------- |
| `HF_TOKEN`          | Hugging Face access token (required)                      |
| `DIARIZATION_MODEL` | HF model ID (default: `pyannote/speaker-diarization-3.1`) |                  |
| `DEVICE`            | `cuda` or `cpu` (auto-detected if unset)                  |

Create a .env file:
```env 
HF_TOKEN=hf_xxx
DIARIZATION_MODEL=pyannote/speaker-diarization-3.1
PORT=8004
DEVICE=cuda
```

💡 Roadmap / Backlog
- [ ]: Support UploadFile via /diarization/upload

- [ ]: Return confidence scores (if model supports it)

- [ ]: Diarization summary (total speakers, duration)

- [ ]: Dockerization for deployment

- [ ]: CI/CD integration

- [ ]: Speaker embedding comparison (advanced)