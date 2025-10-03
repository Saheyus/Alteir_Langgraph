"""Utilities for configuring application-wide logging."""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

DEFAULT_APP_NAME = "alteir"
DEFAULT_LOG_DIR = "logs"
DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_ENV_LOG_LEVEL = "ALTEIR_LOG_LEVEL"
_ENV_LOG_DIR = "ALTEIR_LOG_DIR"
_ENV_LOG_FILE = "ALTEIR_LOG_FILE"

_CONFIGURED = False


def _resolve_level(level: Optional[str | int]) -> int:
    """Resolve a logging level coming from configuration or environment."""

    if isinstance(level, int):
        return level

    if isinstance(level, str):
        resolved = logging.getLevelName(level.upper())
        return resolved if isinstance(resolved, int) else logging.INFO

    env_level = os.getenv(_ENV_LOG_LEVEL)
    if env_level:
        resolved = logging.getLevelName(env_level.upper())
        return resolved if isinstance(resolved, int) else logging.INFO

    return logging.INFO


def _get_log_file_path(
    log_dir: Optional[os.PathLike[str] | str],
    log_file: Optional[os.PathLike[str] | str],
    app_name: str,
) -> Path:
    """Compute the log file path and ensure its parent directory exists."""

    directory = Path(log_dir or os.getenv(_ENV_LOG_DIR, DEFAULT_LOG_DIR)).expanduser()
    directory.mkdir(parents=True, exist_ok=True)

    file_path = log_file or os.getenv(_ENV_LOG_FILE)
    if file_path:
        explicit_path = Path(file_path).expanduser()
        explicit_path.parent.mkdir(parents=True, exist_ok=True)
        return explicit_path

    return directory / f"{app_name}.log"


def _clear_existing_handlers(logger: logging.Logger) -> None:
    """Remove previously registered handlers to prevent duplicate logs."""

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def setup_logging(
    *,
    log_level: Optional[str | int] = None,
    log_dir: Optional[os.PathLike[str] | str] = None,
    log_file: Optional[os.PathLike[str] | str] = None,
    app_name: str = DEFAULT_APP_NAME,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    force: bool = False,
) -> logging.Logger:
    """Configure root logging for the application.

    Args:
        log_level: Desired logging level (name or numeric). If omitted, the
            ``ALTEIR_LOG_LEVEL`` environment variable is used.
        log_dir: Directory that will receive rotating log files.
        log_file: Explicit log file path. Overrides ``log_dir`` when provided.
        app_name: Base logger name used for children loggers.
        max_bytes: Maximum size of each rotating log file.
        backup_count: Number of rotated files to keep.
        force: When ``True`` the logging configuration is rebuilt even if it was
            already initialised.

    Returns:
        The configured application logger.
    """

    global _CONFIGURED

    root_logger = logging.getLogger()
    if _CONFIGURED and not force and root_logger.handlers:
        return logging.getLogger(app_name)

    _clear_existing_handlers(root_logger)

    level = _resolve_level(log_level)
    root_logger.setLevel(level)

    formatter = logging.Formatter(fmt=DEFAULT_FORMAT, datefmt=DEFAULT_DATE_FORMAT)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    file_path = _get_log_file_path(log_dir, log_file, app_name)
    file_handler = RotatingFileHandler(
        file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    logging.captureWarnings(True)

    _CONFIGURED = True
    return logging.getLogger(app_name)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a logger configured for the application.

    If ``setup_logging`` has not been called yet it will be initialised with
    default parameters before returning the logger.
    """

    global _CONFIGURED

    if not _CONFIGURED:
        setup_logging()

    if not name:
        return logging.getLogger(DEFAULT_APP_NAME)

    return logging.getLogger(name)


def reset_logging() -> None:
    """Reset logging configuration (mainly for tests)."""

    global _CONFIGURED

    _clear_existing_handlers(logging.getLogger())
    _CONFIGURED = False
