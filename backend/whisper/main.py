from fastapi import FastAPI 

from whisper.routers import root, healthcheck, whisper

# ─── FastAPI Setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title="Whisper Speech-to-Text Service")

app.include_router(root.router, prefix="/", tags=["root"])
app.include_router(healthcheck.router, prefix="/healthcheck", tags=["healthcheck"])
app.include_router(whisper.router, prefix="/whisper", tags=["whisper"])