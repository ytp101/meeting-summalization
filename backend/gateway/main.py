"""
Gateway Service Main Application Module

This module initializes the FastAPI application for the Meeting Summarization Gateway.
It configures middleware, registers routers, and sets application metadata.

Responsibilities:
- Create and configure the FastAPI app with a descriptive title.
- Apply CORS middleware using origins defined via environment variables.
- Include routers for:
    - Root endpoint (`root.router`)
    - Healthcheck endpoint (`healthcheck.router`)
    - File upload and processing endpoint (`upload_file.router`)

Environment Variables:
- `FRONTEND_ORIGINS`: Comma-separated list of allowed CORS origins (default: `*`).

Usage:
Start the service with Uvicorn:

```bash
uvicorn gateway.main:app --host 0.0.0.0 --port 8000
```

TODO:
- Refine CORS configuration for production environments.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from contextlib import asynccontextmanager

from gateway.routers import root, healthcheck, upload_file, progress
from gateway.config.settings import ensure_data_dir
from gateway.utils.logger import logger

@asynccontextmanager 
async def lifespan(app: FastAPI):
    ensure_data_dir()

    yield

    logger.info("Data Directory Created")

# Initialize FastAPI application
app = FastAPI(title="Meeting Summarization Gateway")

# Configure CORS middleware
frontend_origins = os.getenv("FRONTEND_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(root.router)
app.include_router(healthcheck.router)
app.include_router(upload_file.router)
app.include_router(progress.router)
