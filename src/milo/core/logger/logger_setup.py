"""
Centralized logging configuration for the application.

This module provides a standardized logging setup using loguru. It configures:
1. File logging with daily rotation (no color)
2. Console logging with colored output
3. Consistent log format across all handlers
4. Debug level logging for comprehensive tracing

Example:
    >>> from milo.core.logger.logger_setup import loguru_setup
    >>> logger = loguru_setup()
    >>> logger.info("Starting application")
"""

from __future__ import annotations
import sys
from loguru import logger
from milo.core.config import settings


def loguru_setup(
    logfile: str = "logfile_{time:YYYY-MM-DD}.log",
    rotation: str = "12:00",
):
    settings.log_dir.mkdir(parents=True, exist_ok=True)

    # Ensure logfile is stored in log_dir
    logfile_path = str(settings.log_dir / logfile)

    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} | {line} | {message}"
    )
    console_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} | {line} | {message}"
    )

    logger.remove()

    logger.add(
        logfile_path,
        format=file_format,
        level="DEBUG",
        rotation=rotation,
        colorize=False,
        enqueue=True,
    )
    logger.add(
        sys.stderr,
        format=console_format,
        level="DEBUG",
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    return logger
