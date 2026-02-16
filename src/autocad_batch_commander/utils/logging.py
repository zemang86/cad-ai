"""Loguru configuration."""

from __future__ import annotations

import sys

from loguru import logger

from autocad_batch_commander.config import settings


def setup_logging() -> None:
    """Configure loguru with the application log level."""
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level)
