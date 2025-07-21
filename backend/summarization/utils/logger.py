"""
logger.py
---------

Centralized logging setup for the summarization microservices.

- Uses Python’s built-in `logging` module.
- Configures global format, level, and logger name.
- Intended to be imported across all modules (routers, services, etc.)
  to maintain consistent logging output and format.

Log Format:
    [timestamp] [log level] message

Log Level:
    INFO by default — can be adjusted using `logger.setLevel(...)`

Usage:
    from summarization.utils.logger import logger

Author:
    yodsran
"""

import logging

# ─── Logging Configuration ──────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s", 
    level=logging.INFO
)

# Standardized logger instance for all modules
logger = logging.getLogger("service.summarization_service")
