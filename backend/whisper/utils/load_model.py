from transformers import pipeline, Pipeline as HFPipeline
from whisper.utils.logger import logger
from whisper.config.settings import MODEL_ID, DEVICE, DTYPE, LANGUAGE

_whisper_model: HFPipeline = None

def is_model_loaded() -> bool:
    """
    Check if the Whisper model is already loaded.

    Returns:
        bool: True if loaded, False otherwise.
    """
    return _whisper_model is not None

def get_whisper_model() -> HFPipeline:
    global _whisper_model

    if _whisper_model is None:
        logger.info(f"Loading Whisper model '{MODEL_ID}' on device {str(DEVICE)} dtype {str(DTYPE)}")
        try: 
            _whisper_model = pipeline(
                task="automatic-speech-recognition",
                model=MODEL_ID,
                device=DEVICE,
                torch_dtype=DTYPE,
                return_timestamps=True,
                chunk_length_s=30,
                batch_size=1,
                generate_kwargs={"language": str(LANGUAGE)}
            )
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise RuntimeError("Whisper model loading failed") from e
        logger.info("Whisper model loaded successfully")
    return _whisper_model