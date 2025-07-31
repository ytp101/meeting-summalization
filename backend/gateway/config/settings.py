import os 
from pathlib import Path 

DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Service endpoints
PREPROCESS_URL = os.getenv("PREPROCESS_SERVICE_URL", "http://preprocess:8001/preprocess/")
DIAR_URL       = os.getenv("DIARIZATION_SERVICE_URL", "http://diarization:8004/diarization/")
WHISPER_URL    = os.getenv("WHISPER_SERVICE_URL", "http://whisper:8003/whisper/")
SUMMARIZE_URL  = os.getenv("SUMMARIZATION_SERVICE_URL", "http://summarization:8005/summarization/")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "1200"))

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@" \
         f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"