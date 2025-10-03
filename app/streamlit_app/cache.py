"""Cache helpers for the Streamlit application."""

from pathlib import Path
import json
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
