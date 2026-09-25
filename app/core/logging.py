"""Structured logging configuration for ArchPilot."""

import logging
import sys
from typing import Optional


class CustomFormatter(logging.Formatter):
    """Clean, structured terminal log formatter with subtle color highlights."""

    grey = "\x1b[38;20m"
    blue = "\x1b[34;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"

    FORMATS = {
        logging.DEBUG: grey + log_format + reset,
        logging.INFO: blue + log_format + reset,
        logging.WARNING: yellow + log_format + reset,
        logging.ERROR: red + log_format + reset,
        logging.CRITICAL: bold_red + log_format + reset,
    }

    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno, self.log_format)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def setup_logging(level: Optional[str] = None) -> logging.Logger:
    """Initialize system-wide logging configuration."""
    log_level = (level or "INFO").upper()

    logger = logging.getLogger("archpilot")
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Avoid duplicate handlers if re-initialized
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, log_level, logging.INFO))
        handler.setFormatter(CustomFormatter())
        logger.addHandler(handler)

    logger.propagate = False
    return logger


logger = setup_logging()
