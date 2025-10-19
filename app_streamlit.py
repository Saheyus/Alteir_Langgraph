#!/usr/bin/env python3
"""Interface Streamlit pour le système multi-agents GDD Alteir."""

import sys
import os
from pathlib import Path
from typing import Optional

try:
    # Load environment variables from .env files early
    from dotenv import load_dotenv
    def _load_env_files() -> None:
        try:
            # Load default .env if present
            load_dotenv()
            # Load .env.local to override (if present)
            local_path: Optional[str] = str(Path(".env.local").resolve())
            if Path(local_path).exists():
                load_dotenv(dotenv_path=local_path, override=True)
        except Exception:
            # Non-blocking if dotenv is missing or file unreadable
            pass
    _load_env_files()
except Exception:
    # dotenv not installed; proceed (tests may install it)
    pass

# Attempt to read Streamlit Cloud secrets and export to environment (safe fallback for local)
try:
    import streamlit as st  # type: ignore
    def _export_secrets_to_env() -> None:
        secrets = getattr(st, "secrets", None)
        if not secrets:
            return
        # Only set if not already present in OS env (local .env wins)
        for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "NOTION_TOKEN"):
            try:
                if key in secrets and not os.getenv(key):
                    os.environ[key] = str(secrets[key])
            except Exception:
                # Never fail app startup on secrets export
                pass
    _export_secrets_to_env()
except Exception:
    # streamlit might not be importable in some test contexts; ignore
    pass

from config.logging_config import get_logger, setup_logging

sys.path.append(str(Path(__file__).parent))

from app.streamlit_app.app import run_app


def main() -> None:
    """Lance l'application Streamlit."""

    setup_logging()
    logger = get_logger(__name__)
    logger.info("Démarrage de l'interface Streamlit")

    try:
        run_app()
    except Exception:  # noqa: BLE001 - on reloge l'erreur avant de la relancer
        logger.exception("Erreur inattendue lors de l'exécution de Streamlit")
        raise


if __name__ == "__main__":
    main()
