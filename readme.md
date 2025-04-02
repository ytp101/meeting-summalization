<!-- <img src="./images/logo.sample.png" alt="Logo of the project" align="right"> -->

# Meeting Summarization &middot;

<!-- [![Build Status](https://img.shields.io/travis/npm/npm/latest.svg?style=flat-square)](https://travis-ci.org/npm/npm) [![npm](https://img.shields.io/npm/v/npm.svg?style=flat-square)](https://www.npmjs.com/package/npm) [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com) [![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](https://github.com/your/your-project/blob/master/LICENSE) -->

> Automatically summarize meeting recordings from `.mp4` or `.mp3` into concise text using Whisper and LLMs.

---

## 🧩 Features

- Accepts `.mp4` or `.mp3` input files
- Extracts audio and converts it to `.wav` using FFmpeg
- Transcribes using `Whisper` (supports Thai and multilingual)
- Summarizes transcripts using an LLM
- FastAPI microservice architecture
- Designed for real-time meeting analytics

---

## 🚀 Getting Started

### 📦 Clone the repository

```bash
git clone https://github.com/ytp101/meeting-summalization.git
cd meeting-summalization/
```

## 🛠 Development
### ⚙️ Prerequisites
* Python 3.10+
* FFmpeg installed and in your PATH
* Node.js (for frontend, optional)

### 📦 Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

### 💻 Frontend Setup
```bash
cd frontend/meeting-summalization
npm install
```

## 🧪 Running the Services
### Gateway Service 
```bash
python /backend/gateway/main.py
```

### 🔊 Preprocess Service (FFmpeg audio extractor)
```bash
python /backend/preprocess/main.py
```

### 🗣 Whisper Service (Transcriber)
```bash
python /backend/whisper/main.py
```

### 🧠 Summarizer Service (LLM-based)
```bash
python /backend/summalization/main.py
```

You can call them in order via API Gateway or manually.

## 🔐 API Reference
| Endpoint      | Method        | Description                           |
| ------------- | ------------- | ------------------------------------- |
| /gateway/     | POST          | Received mp4 or mp3 from user         |
| /preprocess/  | POST          | Extract .wav from video               |
| /whisper/     | POST          | Transcribe audio using Whisper        |
| /summarize/   | POST          | Generate text summary from transcript |

## 🗃 Database
No persistent database yet — results are stored as .wav, .txt, and .json in the database/ folder.

## 📄 License
MIT License. See LICENSE file for more info.