"""Layout utilities for the Streamlit app."""

import streamlit as st

from .cache import get_outputs_count
from .constants import DOMAIN_ICONS, DOMAIN_HEADERS, MODELS


CUSTOM_CSS = """
<style>
/* Réduire l'espace en haut */
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 0rem;
}

/* En-tête principal avec gradient et design moderne */
.main-header {
    font-size: 2.8rem;
    font-weight: 800;
    text-align: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0.5rem 0 1rem 0;
    padding: 0.5rem 0;
    letter-spacing: -0.02em;
}

.subtitle {
    text-align: center;
    color: #666;
    font-size: 1rem;
    margin-top: -0.5rem;
    margin-bottom: 1.5rem;
}

.header-divider {
    height: 3px;
    background: linear-gradient(90deg, transparent, #667eea, #764ba2, transparent);
    margin: 1rem auto 2rem auto;
    border-radius: 2px;
    max-width: 300px;
}

.metric-box {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}

.success-box {
    background-color: #d4edda;
    border-left: 4px solid #28a745;
    padding: 1rem;
    margin: 1rem 0;
}

.warning-box {
    background-color: #fff3cd;
    border-left: 4px solid #ffc107;
    padding: 1rem;
    margin: 1rem 0;
}

.context-banner {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    padding: 0.85rem 1.2rem;
    margin-bottom: 1.2rem;
    background: linear-gradient(90deg, rgba(102, 126, 234, 0.12), rgba(118, 75, 162, 0.16));
    border: 1px solid rgba(118, 75, 162, 0.2);
    border-radius: 0.8rem;
}

.context-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    font-weight: 600;
    background-color: white;
    color: #4c51bf;
    border: 1px solid rgba(76, 81, 191, 0.2);
    box-shadow: 0 2px 6px rgba(76, 81, 191, 0.08);
}

.context-chip.secondary {
    color: #764ba2;
    border-color: rgba(118, 75, 162, 0.25);
}

.config-summary {
    margin-top: 1rem;
    padding: 0.75rem 1rem;
    border-radius: 0.75rem;
    border: 1px solid rgba(102, 126, 234, 0.18);
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.08), rgba(118, 75, 162, 0.05));
}

.config-summary__title {
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #475569;
    margin-bottom: 0.5rem;
}

.config-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.config-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.3rem 0.65rem;
    border-radius: 999px;
    font-size: 0.85rem;
    background-color: rgba(255, 255, 255, 0.85);
    border: 1px solid rgba(99, 102, 241, 0.2);
    color: #3730a3;
}

.config-badge.modified {
    background-color: rgba(244, 63, 94, 0.12);
    border-color: rgba(244, 63, 94, 0.35);
    color: #be123c;
}

.chip-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 0.75rem;
    margin-top: 0.5rem;
}

.context-card {
    padding: 0.65rem 0.75rem;
    border-radius: 0.65rem;
    border: 1px solid rgba(15, 23, 42, 0.08);
    background: white;
    box-shadow: 0 3px 10px rgba(15, 23, 42, 0.05);
}

.context-card__title {
    font-weight: 600;
    font-size: 0.95rem;
    margin-bottom: 0.25rem;
}

.context-card__meta {
    display: flex;
    justify-content: space-between;
    font-size: 0.75rem;
    color: #475569;
}

.badge-soft {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.2rem 0.5rem;
    border-radius: 0.5rem;
    background-color: rgba(15, 23, 42, 0.06);
    font-size: 0.75rem;
}

.badge-soft.secondary {
    background-color: rgba(118, 75, 162, 0.12);
    border: 1px solid rgba(118, 75, 162, 0.18);
    color: #5b21b6;
}

.run-recap {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    margin-bottom: 0.75rem;
}

.run-recap .badge-soft {
    background-color: rgba(102, 126, 234, 0.12);
    border: 1px solid rgba(102, 126, 234, 0.2);
    color: #3730a3;
}

.run-recap .badge-soft.secondary {
    background-color: rgba(118, 75, 162, 0.12);
    border-color: rgba(118, 75, 162, 0.18);
    color: #5b21b6;
}
</style>
"""


def apply_page_config() -> None:
    """Configure Streamlit page options."""
    st.set_page_config(page_title="GDD Alteir - Multi-Agents", page_icon="🤖", layout="wide")


def inject_css() -> None:
    """Inject custom CSS for the application."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_header() -> None:
    """Display the application header."""
    st.markdown(
        """
    <div style="text-align: center;">
        <h1 class="main-header">🤖 Système Multi-Agents</h1>
        <p class="subtitle">Création collaborative de contenu pour le GDD Alteir</p>
        <div class="header-divider"></div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    """Display sidebar configuration and return selected options."""
    with st.sidebar:
        st.header("⚙️ Configuration")

        st.subheader("Modèle LLM")
        selected_model = st.selectbox(
            "Modèle",
            options=list(MODELS.keys()),
            index=2,
            format_func=lambda key: f"{MODELS[key]['icon']} {key}",
            help="Choisir le modèle LLM pour la génération",
        )

        model_info = MODELS[selected_model]
        st.caption(f"**{model_info['provider']}** • {model_info['description']}")

        st.subheader("Domaine")
        domain = st.selectbox(
            "Domaine",
            ["Personnages", "Lieux"],
            index=0,
            help="Choisir le type de contenu à générer",
        )
        st.caption(f"{DOMAIN_ICONS[domain]} **{domain}**")

        st.subheader("📊 Statistiques")
        nb_files = get_outputs_count()
        st.metric("Générations", nb_files)

    return selected_model, model_info, domain


def get_domain_header(domain: str) -> str:
    """Return the human readable header for a domain."""
    return DOMAIN_HEADERS.get(domain, domain)


def render_context_banner(domain: str, selected_model: str, model_info: dict) -> None:
    """Display a contextual banner highlighting the active domain and model."""

    domain_label = f"{DOMAIN_ICONS[domain]} {domain}"
    model_label = f"{model_info['icon']} {selected_model}"

    st.markdown(
        f"""
        <div class="context-banner">
            <span class="context-chip">{domain_label}</span>
            <span class="context-chip secondary">{model_label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
