"""Cache helpers for the Streamlit application."""

from pathlib import Path
import os
import json
import platform
from typing import Any, Dict
import streamlit as st


@st.cache_resource(show_spinner="Chargement des dépendances...")
def load_workflow_dependencies(domain: str = "personnages"):
    """Charge les dépendances lourdes une seule fois selon le domaine."""
    from workflows.content_workflow import ContentWorkflow
    from agents.writer_agent import WriterConfig

    if domain == "lieux":
        from config.domain_configs.lieux_config import LIEUX_CONFIG

        return ContentWorkflow, WriterConfig, LIEUX_CONFIG

    from config.domain_configs.personnages_config import PERSONNAGES_CONFIG

    return ContentWorkflow, WriterConfig, PERSONNAGES_CONFIG


@st.cache_data(ttl=60)
def get_outputs_count() -> int:
    """Retourne le nombre de fichiers de sortie générés (cache 60s)."""
    outputs_dir = Path("outputs")
    if outputs_dir.exists():
        return len(list(outputs_dir.glob("*.json")))
    return 0


@st.cache_data(ttl=30)
def list_output_files():
    """Retourne la liste triée des fichiers de sortie (cache 30s)."""
    outputs_dir = Path("outputs")
    if not outputs_dir.exists():
        return []

    json_files = sorted(
        outputs_dir.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return [f.stem for f in json_files]


@st.cache_data
def load_result_file(file_stem: str):
    """Charge le fichier de résultat JSON correspondant au préfixe donné."""
    outputs_dir = Path("outputs")
    json_path = outputs_dir / f"{file_stem}.json"

    if not json_path.exists():
        return None

    with open(json_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


# ---------------------------------------------------------------------------
# UI preferences persistence (QoL)
# ---------------------------------------------------------------------------

def _prefs_path() -> Path:
    """Return a cross-platform path for UI preferences file."""
    # Windows: APPDATA/Alteir/ui_prefs.json; others: ~/.alteir/ui_prefs.json
    if platform.system().lower() == "windows":
        base = Path(os.getenv("APPDATA", str(Path.home())))
        return base / "Alteir" / "ui_prefs.json"
    return Path.home() / ".alteir" / "ui_prefs.json"


@st.cache_data
def load_ui_prefs() -> Dict[str, Any]:
    """Load UI preferences; returns empty dict if none.

    Cached to avoid repeated disk access during reruns; invalidated when saving.
    """
    path = _prefs_path()
    try:
        if path.exists():
            with path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
    except Exception:
        pass
    return {}


def save_ui_prefs(prefs: Dict[str, Any]) -> None:
    """Persist UI preferences to disk and clear the cache entry."""
    path = _prefs_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(prefs, fh, ensure_ascii=False, indent=2)
    except Exception:
        # Best-effort: do not crash UI if disk write fails
        return
    # Invalidate cache so next load sees the new data
    load_ui_prefs.clear()
