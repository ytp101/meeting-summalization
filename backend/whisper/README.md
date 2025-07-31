# Whisper Speech-to-Text Service

A high-performance, modular FastAPI microservice that leverages OpenAI's Whisper model for robust automatic speech recognition (ASR) with optional speaker diarization support. Designed for seamless integration, scalability, and easy deployment in production environments.

---

## 🚀 Features

* **ASR Engine**: Utilizes the Whisper model (`openai/whisper-large-v3-turbo`) for high-accuracy transcriptions.
* **Speaker Diarization**: Accepts precomputed diarization segments to attribute transcriptions to individual speakers.
* **Flexible Configuration**: Environment-driven parameters for model selection, language, cache directory, and request timeouts.
* **Health & Status Endpoints**: Built-in `/healthcheck` and `/` routes for quick operational checks.
* **Async Processing**: Fully asynchronous design with GPU-aware optimizations and automatic GPU memory cleanup.
* **Extensible Architecture**: Clear separation of routers, models, services, and utility modules for maintainability.

---

## 📦 Prerequisites

* Python 3.10+
* CUDA-enabled GPU (optional, falls back to CPU)
* [torchaudio](https://github.com/pytorch/audio)
* [FastAPI](https://fastapi.tiangolo.com/)
* [Uvicorn](https://www.uvicorn.org/)
* [PyTorch](https://pytorch.org/)

---x

## 🔧 Configuration

| Variable          | Default                         | Description                                   |
| ----------------- | ------------------------------- | --------------------------------------------- |
| `HF_HOME`         | `$HOME/.cache/huggingface`      | Cache directory for Hugging Face models       |
| `MODEL_ID`        | `openai/whisper-large-v3-turbo` | Whisper model identifier                      |
| `LANGUAGE`        | `en`                            | Default transcription language                |
| `REQUEST_TIMEOUT` | `1200`                          | Timeout in seconds for transcription requests |

Export variables in your shell or add to a `.env` file:

```bash
export HF_HOME="/path/to/cache"
export MODEL_ID="openai/whisper-large-v3-turbo"
export LANGUAGE="en"
export REQUEST_TIMEOUT=1200
```

## 🛠️ API Reference

### 1. Service Status

* **Endpoint**: `GET /`
* **Response**:

  ```json
  {
    "status": "running",
    "model": "openai/whisper-large-v3-turbo"
  }
  ```

### 2. Healthcheck

* **Endpoint**: `GET /healthcheck`
* **Response**:

  ```json
  {
    "model_loaded": true,
    "gpu_available": "cuda:0"
  }
  ```

### 3. Transcription

* **Endpoint**: `POST /whisper/`
* **Request Body** (`application/json`):

  ```json
  {
    "filename": "path/to/audio.wav",
    "output_dir": "path/to/output",
    "segments": [
      { "start": 0.0, "end": 5.2, "speaker": "A" },
      { "start": 5.2, "end": 10.0, "speaker": "B" }
    ]
  }
  ```
* **Response**:

  ```json
  {
    "transcription_file_path": "path/to/output/audio.txt"
  }
  ```

---

## 🔄 Testing

Mock-based, lightweight tests using `pytest` and `httpx`:

```bash
# Ensure HF_HOME is writable for tests
export HF_HOME="/tmp/huggingface"

# Run tests
pytest tests/
```

<!-- HF_HOME=/tmp/huggingface PYTHONPATH=. pytest whisper/tests -->