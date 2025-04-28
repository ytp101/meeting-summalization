# Meeting Summarization <img src="./images/logo.svg" alt="Logo of the project" height=35 width=35>

> Automatically summarize meeting recordings from `.mp4` or `.mp3` into concise text using Whisper and LLMs.

---

## 🧩 Features

- Accepts `.mp4` or `.mp3` input files
- Extracts audio and converts it to `.wav` using FFmpeg
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
| /preprocess/  | POST          | Convert .mp4 to .wav audio             |
| /whisper/     | POST          | Transcribe .wav to .txt      |
| /summarize/   | POST          | 	Summarize transcription text |
| /healthcheck/ | GET | 	Health status for each service |

## 🗃 Storage
* Persistent Docker volumes are used to store:
    * Uploaded videos (mp4/)
    * Extracted audio (wav/)
    * Transcriptions and summaries (txt/)

📄 License
MIT License — See the LICENSE file for more information.

📈 Future Improvements
- [ ] .mp3 input support
- [ ] Frontend dashboard for upload and summaries
- [ ] Realtime meeting summarization
- [ ] User authentication and management
- [ ] Full Kubernetes deployment templates