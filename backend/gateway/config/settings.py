"""
Gateway Service Configuration Module

This module defines configuration settings and constants for the API Gateway Service,
including:

- **DATA_DIR**: Directory for storing data (temporary or persistent).
- **Service Endpoints**: URLs for downstream microservices:
    - Preprocessing
    - Speaker Diarization
    - Whisper ASR
    - Summarization
- **REQUEST_TIMEOUT**: Timeout in seconds for HTTP requests to downstream services.
- **DB_URL**: PostgreSQL database connection URL assembled from environment variables.

Environment Variables:
- `DATA_DIR`: Base directory for data storage (default: `/data`).
- `PREPROCESS_SERVICE_URL`: URL for the Preprocessing service (default: `http://preprocess:8001/preprocess/`).
- `DIARIZATION_SERVICE_URL`: URL for the Speaker Diarization service (default: `http://diarization:8004/diarization/`).
- `WHISPER_SERVICE_URL`: URL for the Whisper ASR service (default: `http://whisper:8003/whisper/`).
- `SUMMARIZATION_SERVICE_URL`: URL for the Summarization service (default: `http://summarization:8005/summarization/`).
- `REQUEST_TIMEOUT`: Timeout for service requests in seconds (default: `1200`).
- `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`: Credentials and host information for the PostgreSQL database.
"""
import os
from pathlib import Path

from gateway.utils.logger import logger

# Create data directory if it does not exist
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))

def ensure_data_dir():
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        logger.warning(f"Permission denied: cannot create DATA_DIR at {DATA_DIR}")
    except Exception as e:
        logger.error(f"Unexpected error creating DATA_DIR: {e}")


# Service endpoints
PREPROCESS_URL = os.getenv(
    "PREPROCESS_SERVICE_URL",
    "http://preprocess:8001/preprocess/"
)
DIAR_URL = os.getenv(
    "DIARIZATION_SERVICE_URL",
    "http://diarization:8004/diarization/"
)
WHISPER_URL = os.getenv(
    "WHISPER_SERVICE_URL",
    "http://whisper:8003/whisper/"
)
SUMMARIZE_URL = os.getenv(
    "SUMMARIZATION_SERVICE_URL",
    "http://summarization:8005/summarization/"
)

# Request timeout for external service calls (in seconds)
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "1200"))

# Database connection URL
DB_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

# Upload env
MAX_BYTES: int = os.getenv("MAX_BYTES", 10 * 1024**3)  # 10 GB
CHUNK_SIZE: int = os.getenv("CHUNK_SIZE", 10 * 1024**2)  # 10 MB
UPLOAD_TIMEOUT: int = os.getenv("UPLOAD_TIMEOUT", 20 * 60) # 20 minutes

# Progress endpoint base (used for microservice hooks)
PROGRESS_BASE = os.getenv("GATEWAY_PROGRESS_URL", "http://gateway:8000/progress")
