#!/usr/bin/env python3
"""Interface Streamlit pour le système multi-agents GDD Alteir."""

import sys
from pathlib import Path

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
