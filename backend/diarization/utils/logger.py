"""
diarization.utils.logger

Centralized logging configuration for the diarization service.
Logs are currently streamed to stdout; future plans include persistent log files per process.
"""

import logging
import sys

# Configure the root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # log to stdout
        # TODO: Add FileHandler later (e.g., work_id/logs/diarization.log)
    ],
)

# Custom module-level logger
logger = logging.getLogger("services.diarization_service")
