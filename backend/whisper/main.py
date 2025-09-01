"""
Main Application Entry Point.

Initializes the FastAPI app and includes all service routers:
- /             → Service status and metadata
- /healthcheck  → Model and GPU readiness probe
- /whisper      → Transcription endpoint for audio files

Routers:
- root        : Basic service status
- healthcheck : Model & hardware status
- whisper     : Transcription logic with optional diarization
"""

from fastapi import FastAPI 

from whisper.routers import root, healthcheck, whisper

# ─── FastAPI Setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title="Whisper Speech-to-Text Service")

app.include_router(root.router)
app.include_router(healthcheck.router)
app.include_router(whisper.router)

