import logging

logging.basicConfig(
    # %(asctime)s %(levelname)s %(message)s -> timestamp, log level, message
    format="%(asctime)s %(levelname)s %(message)s",
    # log level -> INFO 
    level=logging.INFO,
    # send log to stdout 
    # TODO: log save to txt file or other. (work_id/log/process) <- backlog
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger("services.gateway")