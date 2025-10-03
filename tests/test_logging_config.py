"""Tests for the centralized logging configuration."""

from __future__ import annotations

import logging

from config.logging_config import get_logger, reset_logging, setup_logging


def _flush_handlers() -> None:
    """Ensure all attached logging handlers are flushed to disk."""

    for handler in logging.getLogger().handlers:
        handler.flush()


def test_setup_logging_creates_rotating_file(tmp_path):
    """The logging setup should create a rotating file handler and write logs."""

    reset_logging()
    log_dir = tmp_path / "logs"
    logger = setup_logging(force=True, log_dir=log_dir, app_name="test_app", log_level="INFO")

    logger.info("message de test")
    _flush_handlers()

    log_file = log_dir / "test_app.log"
    assert log_file.exists(), "Le fichier de logs devrait être créé"
    assert "message de test" in log_file.read_text(encoding="utf-8")


def test_setup_logging_honors_environment_level(tmp_path, monkeypatch):
    """The ``ALTEIR_LOG_LEVEL`` environment variable should influence the level."""

    reset_logging()
    monkeypatch.setenv("ALTEIR_LOG_LEVEL", "DEBUG")
    setup_logging(force=True, log_dir=tmp_path / "env_logs", app_name="env_test")

    logger = get_logger("env.test")
    assert logger.isEnabledFor(logging.DEBUG)

    logger.debug("debug message")
    _flush_handlers()
