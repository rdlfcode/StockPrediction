import json
import logging
import logging.config
import os
import sys
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the log record.
    """
    def __init__(self, service_name):
        self.service_name = service_name
        super().__init__()

    def format(self, record):
        logobj = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.service_name,
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        
        # Add exception info if available
        if record.exc_info:
            logobj["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ["args", "asctime", "created", "exc_info", "exc_text", "filename",
                         "funcName", "id", "levelname", "levelno", "lineno", "module",
                         "msecs", "message", "msg", "name", "pathname", "process",
                         "processName", "relativeCreated", "stack_info", "thread", "threadName"]:
                logobj[key] = value
        
        return json.dumps(logobj)

def configure_logging(service_name, log_level=None):
    """
    Configure logging for the application.
    """
    if not log_level:
        log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    
    # Configure root logger
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JSONFormatter,
                "service_name": service_name
            },
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json" if os.environ.get("LOG_FORMAT", "").lower() == "json" else "standard",
                "stream": sys.stdout
            }
        },
        "loggers": {
            "": {
                "handlers": ["console"],
                "level": log_level
            }
        }
    })