# Meeting Summarization <img src="./images/logo.svg" alt="Logo of the project" height=35 width=35>

> Automatically summarize meeting recordings from `.mp4` or `.mp3` into concise text using Whisper and LLMs.

---

## 🧩 Features

- Accepts `.mp4` or `.mp3` input files
- Extracts audio and converts it to `.opus` using FFmpeg
- Transcribes using `Whisper` (supports Thai and multilingual)
- Summarizes transcripts using an LLM
- FastAPI microservice architecture
- Designed for real-time meeting analytics (Later)

---

## 🚀 Getting Started

### 📦 Clone the repository

```bash
git clone https://github.com/ytp101/meeting-summalization.git
cd meeting-summalization/
```

## 🛠 Development Setup
### ⚙️ Prerequisites
* Python 3.10+
* Node.js (optional for frontend)

### 📦 Backend Setup

```bash
cd backend
docker compose up 
```

#### 🐳 Ollama Container Setup
After the container is running, pull the Llama3 model:

```bash
docker exec ollama ollama pull llama3
```

You can then interact with the services via the API Gateway (port 8000) or its API Docs (http://localhost:8000/docs)

### 💻 Frontend Setup
```bash
cd frontend/meeting-summalization
npm install
npm run dev
```

## 🔐 API Reference
| Endpoint      | Method        | Description                           |
| ------------- | ------------- | ------------------------------------- |
| /uploadfile/     | POST          | Upload a .mp4 file and proces       |
| /preprocess/  | POST          | Convert media to .opus audio           |
| /whisper/     | POST          | Transcribe .opus to .txt               |
| /summarize/   | POST          | 	Summarize transcription text |
| /healthcheck/ | GET | 	Health status for each service |

## 🗃 Storage
* Persistent Docker volumes are used to store:
    * Uploaded videos (mp4/)
* Extracted audio (converted/ as .opus)
    * Transcriptions and summaries (txt/)

📄 License
MIT License — See the LICENSE file for more information.

📈 Roadmap
| Version | Focus                                                               |
| ------- | ------------------------------------------------------------------- |
| `v0.3`  | ✅ Frontend feedback loop, 🧪 start VAD prototype                    |
| `v0.4`  | 🧠 VAD integrated, 🪵 service logs, 🧱 backend response unification |
| `v0.5`  | 👤 Auth layer, ☸️ Kubernetes templates ready                        |
| `v1.0`  | 🎥 Real-time summarization, 🔐 Secure multi-user system             |
📈 Roadmap

| Version | Name                        | Key Features                                                                                                                                          | Status     |
| ------- | --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| **v2**  | **Stable Core**             | ✅ Audio Upload<br>✅ Whisper ASR<br>✅ Diarization<br>✅ Summarization via LLaMA<br>✅ Logging & Healthcheck<br>✅ Modular Docker services                 | ✅ Done     |
| **v3**  | **User & Experience Layer** | 🔐 Auth System (Supabase or Auth.js)<br>🎛️ Frontend UI (Upload + Result Viewer)<br>📡 API UX Feedback (Processing, Error states)<br>🧪 Test Coverage | ⏳ Next     |
| **v4**  | **Task Automation Layer**   | 📌 KeyPoint Extraction (Metadata, Content, Action)<br>🧠 Context-Aware Filtering (Only Key Segments)<br>🔄 Integrate Task Assignment System           | Planned    |
| **v5**  | **Real-Time Engine**        | 🌀 Real-Time Input Streaming<br>📤 Partial Output Buffering<br>🧵 Async LLM Streaming (Chunked LLaMA)<br>🚀 GPU Scheduling & Scaling (K8s-ready)      | Planned 🔭 |
