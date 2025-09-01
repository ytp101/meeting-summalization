"""
Main Application Entrypoint
---------------------------

This file initializes the FastAPI app for the Meeting Summary File Server.

Routers:
- `/`           → Root status endpoint
- `/health`     → Healthcheck for monitoring and uptime checks
- `/download`   → Download endpoints for audio, transcript, and summary files

Author: yodsran
"""

from fastapi import FastAPI
from routers import download, root, healthcheck

app = FastAPI(title="Meeting Summary File Server")

# Register routers in order of importance
app.include_router(root.router)
app.include_router(healthcheck.router)
app.include_router(download.router)
