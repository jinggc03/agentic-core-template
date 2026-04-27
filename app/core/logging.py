"""Logging configuration."""

import logging
import logging.config
import sys
from typing import Any

from app.core.config import settings


def configure_logging() -> None:
    """Configure application logging."""
    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG" if settings.APP_DEBUG else "INFO",
                "formatter": "detailed" if settings.APP_DEBUG else "default",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": "DEBUG" if settings.APP_DEBUG else "INFO",
            "handlers": ["console"],
        },
    }

    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
