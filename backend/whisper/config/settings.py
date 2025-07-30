from pathlib import Path 
import os 
import torch

# hf
HF_HOME      = Path(os.getenv("HF_HOME", "/home/app/.cache"))
HF_HOME.mkdir(parents=True, exist_ok=True)
os.environ["HF_HOME"] = str(HF_HOME)

# model
MODEL_ID        = os.getenv("MODEL_ID", "openai/whisper-large-v3-turbo")
LANGUAGE        = os.getenv("LANGUAGE", "en")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 1200))

# 
DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"
DTYPE  = torch.float16 if torch.cuda.is_available() else torch.float32