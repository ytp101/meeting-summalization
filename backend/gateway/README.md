# Meeting Summarization Gateway

> An API Gateway orchestrating preprocessing, diarization, transcription, and summarization microservices for efficient meeting intelligence.

## 🚀 Overview

This service aggregates downstream AI-powered components into a unified, scalable pipeline:

1. **Preprocessing** – Converts raw audio into a canonical format (WAV).
2. **Speaker Diarization** – Segments audio by speaker using a dedicated microservice.
3. **ASR (Whisper)** – Transcribes segmented audio into text.
4. **Summarization** – Extracts concise meeting summaries and action items.

The Gateway centralizes authentication, routing, error handling, logging, and persistence of task metadata.

---

## 🎯 Prerequisites

* **Python** 3.11+ (tested on 3.12)
* **PostgreSQL** database (v12+)
* **Docker** (optional, for local microservices)

Ensure downstream services are accessible at the configured URLs or via Docker Compose.

---

## 🔧 Configuration

All settings are managed via environment variables or sensible defaults in `gateway/config/settings.py`.

| Variable                       | Description                                       | Default                                    |
| ------------------------------ | ------------------------------------------------- | ------------------------------------------ |
| `DATA_DIR`                     | Base directory for temporary storage              | `/data`                                    |
| `PREPROCESS_SERVICE_URL`       | URL for audio preprocessing microservice          | `http://preprocess:8001/preprocess/`       |
| `DIARIZATION_SERVICE_URL`      | URL for speaker diarization microservice          | `http://diarization:8004/diarization/`     |
| `WHISPER_SERVICE_URL`          | URL for ASR microservice (Whisper)                | `http://whisper:8003/whisper/`             |
| `SUMMARIZATION_SERVICE_URL`    | URL for summarization microservice                | `http://summarization:8005/summarization/` |
| `REQUEST_TIMEOUT`              | Timeout for HTTP calls (seconds)                  | `1200`                                     |
| `DB_USER`, `DB_PASSWORD`, etc. | Credentials and connection details for PostgreSQL | —                                          |
| `FRONTEND_ORIGINS`             | Comma-separated CORS origins                      | `*`                                        |

---

## 📡 API Endpoints

### 1. **Root**

```http
GET /
```

**Response** 200 OK

```json
{ "status": "gateway running" }
```

### 2. **Healthcheck**

```http
GET /healthcheck
```

**Response** 200 OK

```json
[
  { "service": "preprocess", "status": "up", "message": "" },
  { "service": "diarization", "status": "up", "message": "" },
  { "service": "whisper", "status": "up", "message": "" },
  { "service": "summarization", "status": "up", "message": "" }
]
```

### 3. **Upload & Process**

```http
POST /uploadfile/
Content-Type: multipart/form-data
```

**Form Data**

* `file`: Audio file (`.mp3`, `.m4a`, `.wav`, `.mp4`)

**Response** 200 OK

```json
{
  "task_id": "20250731123045_abcd1234...",
  "summary": "Key takeaways and action items from the meeting..."
}
```

---

## 📈 Logging & Monitoring

* **Logger**: Configured via `gateway/utils/logger.py`, emits timestamped INFO logs to stdout.