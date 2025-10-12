#!/usr/bin/env python3
"""Interface Streamlit pour le système multi-agents GDD Alteir."""

import sys
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
