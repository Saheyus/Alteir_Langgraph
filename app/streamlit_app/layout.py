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
