#!/usr/bin/env python3
"""Interface Streamlit pour le système multi-agents GDD Alteir."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.streamlit_app.app import run_app


def main() -> None:
    """Lance l'application Streamlit."""

    run_app()


if __name__ == "__main__":
    main()
