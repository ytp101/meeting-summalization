# 📁 Meeting Summary File Server

This FastAPI microservice provides secure file access for audio, transcript, and summary files used in AI-based meeting processing pipelines.

---

## 🚀 Features

- 🔍 Download original audio files, `.wav`, transcript `.txt`, and generated summaries
- ✅ Healthcheck and root endpoints for monitoring and uptime verification
- 📦 Modular architecture with clean routing and utilities
- 🧪 Fully tested with `pytest` and `httpx`

---

## 📁 Project Structure
```bash
+-- file_server/
├── main.py # FastAPI app entrypoint
├── routers/
  ├── root.py # Root '/' liveness endpoint
  ├── healthcheck.py # '/health' healthcheck
  └── dowload.py # Dowload File endpoint
```

---

### File Structure
```bash 
/data/
  └── <work_id>/
       ├── raw/
       ├── converted/
       ├── transcript/
       └── summary/
```

---

## 🚀 API Endpoints

| Method | Route              | Description                        |
|--------|-------------------|------------------------------------|
| `GET`  | `/`               | Root status message            |
| `GET`  | `/health`    | Healthcheck status     |
| `POST` | `/download/{work_id}/{category}`    | Download file by category |

---

### TODO
- [ ] Add security/auth middleware
- [x] Write unit tests for core services 
- [ ] Rewrite Dockerfile for production 
- [ ] Enable logging to file per process 

### 📄 Requirements 
- Python 3.11+
- FastAPI

### 🧑‍💻 Author
- yodsran 

<!-- Test command -->
<!-- ~/meeting-summalization/backend$ PYTHONPATH=. pytest file_server/tests -->