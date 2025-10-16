"""High level orchestration for the Streamlit application."""

import streamlit as st

from .creation import render_creation_tab
from .graph import render_graph_tab
from .layout import apply_page_config, inject_css, render_header, render_sidebar
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
    import os

    apply_page_config()
    inject_css()
    render_header()
    
    # Check API keys early and show warnings if missing
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not openai_key or openai_key.startswith("your_") or openai_key.startswith("sk-proj-YOUR"):
        st.warning("⚠️ **OPENAI_API_KEY manquante ou invalide** dans `.env`. Les modèles GPT ne fonctionneront pas.")
    
    if not anthropic_key or anthropic_key.startswith("your_") or anthropic_key.startswith("sk-ant-YOUR"):
        st.warning("⚠️ **ANTHROPIC_API_KEY manquante ou invalide** dans `.env`. Les modèles Claude ne fonctionneront pas.")

    selected_model, model_info, domain = render_sidebar()

    # Global banner: show only if it matches current domain to avoid cross-domain noise
    try:
        last_export = st.session_state.get("_last_export_event")
        current_domain = (domain or "").lower()
        if isinstance(last_export, dict) and last_export.get("domain") == current_domain:
            if last_export.get("success"):
                url = last_export.get("page_url") or "https://www.notion.so"
                st.markdown(
                    f"""
                <div style="background-color:#ecfdf5;border-left:5px solid #10b981;padding:10px 12px;margin:8px 0;border-radius:6px;">
                    ✅ Export confirmé — <a href="{url}" target="_blank" style="color:#047857;text-decoration:underline;font-weight:600;">ouvrir la fiche</a>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            else:
                err = last_export.get("error", "inconnu")
                st.markdown(
                    f"""
                <div style="background-color:#fef2f2;border-left:5px solid #ef4444;padding:10px 12px;margin:8px 0;border-radius:6px;">
                    ❌ Échec export: <code>{err}</code>
                </div>
                """,
                    unsafe_allow_html=True,
                )
    except Exception:
        pass

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
