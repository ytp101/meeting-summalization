import logging

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",  # e.g., 2025-07-17 14:35:21 INFO Starting service...
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()  # Logs to stdout (Docker/K8s compatible)
    ]
)

# TODO: Implement file logging to ./logs/{service}/{process}.log if needed
logger = logging.getLogger("services.whisper")