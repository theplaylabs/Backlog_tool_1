"""Application configuration and logging helpers.

Configuration values are sourced from environment variables with sensible
fallbacks so that the CLI works out-of-the-box but can be customised.

Configuration:
    - BACKLOG_MODEL: OpenAI model to use (default: gpt-4o-mini)
    - BACKLOG_LOG_DIR: Directory for log files (default: %USERPROFILE%\.bckl)
    - BACKLOG_LOG_LEVEL: Logging level (default: INFO)

Logging is set up once via :func:`setup_logging`, writing to a rotating file in
``%USERPROFILE%\.bckl\bckl.log`` (override with ``BACKLOG_LOG_DIR``).
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Final

__all__ = ["Config", "load_config", "setup_logging", "get_logger"]

_DEFAULT_MODEL: Final = "gpt-4o-mini"
_LOG_FILE_NAME: Final = "bckl.log"
_MAX_BYTES: Final = 512_000  # 0.5 MB per file
_BACKUP_COUNT: Final = 3


@dataclass(slots=True, frozen=True)
class Config:  # noqa: D401
    """Runtime configuration (immutable)."""

    model: str
    log_dir: Path
    log_level: str


def _resolve_log_dir() -> Path:
    """Determine the log directory based on environment or default.
    
    Returns:
        Path: The resolved log directory path
    """
    log_dir = os.getenv("BACKLOG_LOG_DIR")
    if log_dir:
        return Path(log_dir).expanduser()
    return Path(os.environ.get("USERPROFILE", Path.cwd())) / ".bckl"


def load_config() -> Config:
    """Load configuration from environment with defaults."""
    model = os.getenv("BACKLOG_MODEL", _DEFAULT_MODEL)
    log_level = os.getenv("BACKLOG_LOG_LEVEL", "INFO").upper()
    log_dir = _resolve_log_dir()
    return Config(model=model, log_dir=log_dir, log_level=log_level)


_CONFIG: Config | None = None
_LOGGING_CONFIGURED = False


def setup_logging(cfg: Config | None = None) -> None:
    """Initialise rotating-file logging once (idempotent).
    
    Args:
        cfg: Optional configuration object. If not provided, one will be loaded.
    """
    global _LOGGING_CONFIGURED  # noqa: PLW0603
    if _LOGGING_CONFIGURED:
        return

    cfg = cfg or load_config()
    
    # Ensure log directory exists
    cfg.log_dir.mkdir(parents=True, exist_ok=True)
    log_path = cfg.log_dir / _LOG_FILE_NAME

    # Configure rotating file handler
    handler = RotatingFileHandler(
        log_path,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(cfg.log_level)
    root_logger.addHandler(handler)

    _LOGGING_CONFIGURED = True


def get_logger(name: str | None = None) -> logging.Logger:  # noqa: D401
    """Return a logger, ensuring logging is configured.
    
    Args:
        name: Logger name (typically __name__ from the calling module)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    if not _LOGGING_CONFIGURED:
        setup_logging()
    return logging.getLogger(name)

