"""High level orchestration for the Streamlit application."""

import streamlit as st

from .creation import render_creation_tab
from .graph import render_graph_tab
from .layout import (
    apply_page_config,
    inject_css,
    render_context_banner,
    render_header,
    render_sidebar,
)
from .results import show_results

ABOUT_MARKDOWN = """
### 🎯 Système Multi-Agents GDD Alteir

**Architecture:**
- 4 agents génériques (Writer, Reviewer, Corrector, Validator)
- Configuration par domaine (Personnages, Lieux, etc.)
- LangGraph pour orchestration
- GPT-5-nano pour génération

**Workflow:**
1. **Writer** → Génère le contenu initial
2. **Reviewer** → Analyse la cohérence narrative
3. **Corrector** → Corrige la forme
4. **Validator** → Validation finale

**Principes Narratifs (Personnages):**
- Orthogonalité rôle ↔ profondeur
- Structure Surface / Profondeur / Monde
- Temporalité IS / WAS / COULD-HAVE-BEEN
- Show > Tell
- Relations concrètes (prix, dette, délai, tabou)

**Outputs:**
- JSON complet avec métadonnées
- Markdown formaté pour lecture
- Scores de qualité (cohérence, complétude, qualité)
"""


def run_app() -> None:
    """Entry point for the Streamlit UI."""

    apply_page_config()
    inject_css()
    render_header()

    selected_model, model_info, domain = render_sidebar()
    render_context_banner(domain, selected_model, model_info)

    tab1, tab2, tab3, tab4 = st.tabs(["✨ Créer", "📂 Résultats", "🕸️ Graphe", "ℹ️ À propos"])

    with tab1:
        render_creation_tab(domain, selected_model, model_info)

    with tab2:
        st.header("Résultats Générés")
        show_results()

    with tab3:
        render_graph_tab()

    with tab4:
        st.header("À propos")
        st.markdown(ABOUT_MARKDOWN)
