# 📝 Meeting Summarization Service

A container-ready FastAPI microservice that takes a transcript and returns a clean summary using an Ollama-hosted LLM (e.g., LLaMA 3).  
This service is designed to be one stage in a larger AI pipeline (Preprocessing → VAD → Diarization → ASR → Summarization).

---

## ⚙️ Features

- 🧠 Summarize `.txt` transcripts via LLaMA 3 (or any Ollama-compatible model)
- ✅ Healthcheck endpoint for model availability
- 📁 Writes clean summaries to disk
- 🧪 Fully tested with mocked LLM calls
- 🐳 Docker-compatible, production-ready layout

---

## 📦 Project Structure
```bash 
+-- summarization/
├── main.py # FastAPI app entrypoint
├── routers/
│ ├── root.py # Root '/' liveness endpoint
│ ├── healthcheck.py # Dependency check (ollama(llama3))
│ └── summarize.py # summarize endpoint
├── services/
│ └── ollama_client.py # ollama call logic & healthcheck
├── models/
│ └── summarize_schema.py # Pydantic request & response model
├── utils/
│ └──  logger.py # Global logger
├── config/
  └── settings.py # Ollama host, Model ID, System prompt, Max Tokens, Temperature, Requst Timeout - Config logic
```

--- 

## 🛠️ API Overview
### `POST /summarization/`
Summarizes a transcript text file.

**Request:**
```json
{
  "transcript_path": "/data/{work_id}/transcript/transcript.txt",
  "output_dir": "/data/{work_id}/summary/"
}
```
**Response** 
```json 
{
  "summary_path": "/data/{work_id}/summary/{file_name}_summary.txt"
}
```

### `GET /healthcheck/`
Return model availability from Ollama.
Example: 
```json 
{
  "status": "healthy",
  "model": "llama3"
}
```

### `GET /`
Simple liveness check.

🌱 Environment Variables
| Variable          | Default                  | Description                              |
| ----------------- | ------------------------ | ---------------------------------------- |
| `OLLAMA_HOST`     | `http://localhost:11434` | Ollama server base URL                   |
| `MODEL_ID`        | `llama3`                 | Model to use (must be pulled on Ollama)  |
| `SYSTEM_PROMPT`   | *default summary prompt* | System instruction for LLM summarization |
| `MAX_TOKENS`      | `4096`                   | Maximum prediction length                |
| `TEMPERATURE`     | `0.2`                    | LLM creativity vs. determinism           |
| `REQUEST_TIMEOUT` | `300`                    | Timeout in seconds for Ollama calls      |

<!-- Test Command -->
<!-- PYTHONPATH=. pytest ./summarization/tests -->