"""
Gateway Service Logger Configuration Module

This module configures and exposes a standardized logger for the API Gateway Service.

Configuration:
- **Format**: Logs include timestamp, log level, and message.
- **Level**: Default log level is INFO, capturing informational messages and above.
- **Handlers**:
  - StreamHandler: Outputs logs to stdout.

Usage:
Import `logger` from this module and use it throughout the gateway codebase for consistent logging:

```python
from gateway.utils.logger import logger

logger.info("Service started successfully")
```

TODO:
- Persist logs to files under `work_id/log/process` or integrate with external log management.
"""
import logging

# Configure root logger for the gateway service
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",  # Timestamp, level, and message
    level=logging.INFO,                                # Log INFO and above by default
    handlers=[logging.StreamHandler()],                # Output to stdout
)

# Create a named logger for the gateway service
logger = logging.getLogger("services.file-server")
