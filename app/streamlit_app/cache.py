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

    key = (domain or "").lower()
    # Normaliser accents de l'UI vers clés ASCII
    if key in ("espèces",):
        key = "especes"
    if key in ("communautés",):
        key = "communautes"

    if key == "lieux":
        from config.domain_configs.lieux_config import LIEUX_CONFIG

        return ContentWorkflow, WriterConfig, LIEUX_CONFIG
    if key == "especes":
        from config.domain_configs.especes_config import ESPECES_CONFIG

        return ContentWorkflow, WriterConfig, ESPECES_CONFIG
    if key == "communautes":
        from config.domain_configs.communautes_config import COMMUNAUTES_CONFIG

        return ContentWorkflow, WriterConfig, COMMUNAUTES_CONFIG

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
    """Retourne la liste triée des fichiers de sortie valides (cache 30s)."""
    outputs_dir = Path("outputs")
    if not outputs_dir.exists():
        return []

    candidates = sorted(
        outputs_dir.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    valid_stems = []
    for path in candidates:
        try:
            # Skip obviously truncated files without loading full content
            with path.open("r", encoding="utf-8") as fh:
                json.load(fh)
            valid_stems.append(path.stem)
        except Exception:
            # Ignore corrupted JSON
            continue
    return valid_stems


@st.cache_data
def load_result_file(file_stem: str):
    """Charge le fichier de résultat JSON correspondant au préfixe donné."""
    outputs_dir = Path("outputs")
    json_path = outputs_dir / f"{file_stem}.json"

    if not json_path.exists():
        return None

    try:
        with open(json_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        # Skip corrupted/partial files gracefully
        return None


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
