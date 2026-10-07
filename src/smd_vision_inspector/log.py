"""Structured JSON logging."""

import logging
import sys
from typing import TextIO

import structlog

__all__ = ["configure_logging"]


def configure_logging(level: int = logging.INFO, stream: TextIO = sys.stderr) -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(file=stream),
        cache_logger_on_first_use=False,
    )
