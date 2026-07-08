"""
logger.py
=========
Centralised logging configuration for the Agentic Career Counseling Companion.

All modules obtain their logger via:
    from logger import get_logger
    log = get_logger(__name__)

This guarantees:
- Consistent format across all modules
- Log level controlled by a single env variable (LOG_LEVEL)
- Timestamps in ISO 8601 format
- Module names included in every log line for traceability
"""

import logging
import sys
from typing import Optional


# ---------------------------------------------------------------------------
# Formatter — applied to all handlers
# ---------------------------------------------------------------------------
_FORMATTER = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)


def _build_root_logger(level: str) -> None:
    """Configure the root logger once. Subsequent calls are no-ops."""
    root = logging.getLogger()
    if root.handlers:
        # Already configured — prevent duplicate handlers on Flask reloads
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_FORMATTER)
    root.addHandler(handler)
    root.setLevel(getattr(logging, level, logging.INFO))


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Return a named logger.

    Parameters
    ----------
    name : str, optional
        Typically ``__name__`` of the calling module.
        Falls back to the root logger if None.

    Returns
    -------
    logging.Logger
    """
    # Import here to avoid circular imports during early startup
    try:
        from config import config
        _build_root_logger(config.LOG_LEVEL)
    except Exception:
        # Config not yet available (e.g., during testing without .env)
        _build_root_logger("INFO")

    return logging.getLogger(name)
