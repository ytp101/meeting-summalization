"""
diarization.utils.load_model

Implements lazy-loading for the diarization model using a singleton pattern.
This ensures the model is only loaded once and reused across the app.
"""

from typing import Optional
from pyannote.audio import Pipeline
from diarization.config.settings import DIARIZATION_MODEL, DEVICE, HF_TOKEN
from diarization.utils.logger import logger

# Global singleton instance
_diarization_pipeline: Optional[Pipeline] = None

def is_model_loaded() -> bool:
    """
    Check if the diarization model is already loaded.

    Returns:
        bool: True if loaded, False otherwise.
    """
    return _diarization_pipeline is not None

def get_diarization_pipeline() -> Pipeline:
    """
    Lazily load and return the diarization pipeline.
    Loads the model only once and reuses it for all future calls.

    Returns:
        Pipeline: Loaded diarization pipeline instance.

    Raises:
        RuntimeError: If loading fails due to invalid token, network error, etc.
    """
    global _diarization_pipeline

    if _diarization_pipeline is None:
        logger.info(f"Lazy loading diarization model '{DIARIZATION_MODEL}' on {DEVICE}")
        try:
            _diarization_pipeline = Pipeline.from_pretrained(
                DIARIZATION_MODEL,
                use_auth_token=HF_TOKEN
            )
            _diarization_pipeline.to(DEVICE)
            logger.info("Diarization model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load diarization model: {e}")
            raise RuntimeError("Diarization model loading failed") from e

    return _diarization_pipeline
