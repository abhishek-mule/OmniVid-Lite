"""Logging configuration for OmniVid Lite."""
import logging
import sys
from logging.config import dictConfig
from typing import Dict, Any

def setup_logging() -> None:
    """Configure logging for the application."""
    log_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "format": "%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json",
                "filename": "app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            }
        },
        "root": {
            "handlers": ["console", "file"],
            "level": logging.INFO,
        },
    }
    
    dictConfig(log_config)
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")
