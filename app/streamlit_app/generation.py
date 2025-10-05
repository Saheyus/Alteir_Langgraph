"""Content generation helpers for the Streamlit UI."""

from __future__ import annotations

import time
from html import escape
from typing import Any, Dict, Optional

import textwrap

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from agents.notion_context_fetcher import NotionClientUnavailable, NotionContextFetcher
from .cache import load_workflow_dependencies


def create_llm(
    model_name: str,
    model_config: Dict[str, Any],
    creativity: float | None = None,
    reasoning_effort: str | None = None,
    max_tokens: int | None = None,
):
    """Crée une instance LLM selon le modèle choisi."""
    from langchain_openai import ChatOpenAI

    llm_config: Dict[str, Any] = {
        "model": model_config["name"],
        "max_tokens": max_tokens or model_config["max_tokens"],
    }

    if model_config.get("uses_reasoning"):
        llm_config["use_responses_api"] = True
        llm_config["reasoning"] = {
            "effort": reasoning_effort or model_config.get("default_reasoning", "minimal")
        }
    else:
        llm_config["temperature"] = creativity

    return ChatOpenAI(**llm_config)


def _build_context_payload(context_summary: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Fetch full Notion pages for the selected context and format them."""

    if not context_summary or not context_summary.get("selected_ids"):
        st.info("ℹ️ Aucun contexte Notion sélectionné. Génération sans contexte externe.")
        return None

    selected_ids = context_summary.get("selected_ids", [])
    st.info(f"📚 Chargement de {len(selected_ids)} fiche(s) Notion pour le contexte...")

    fetcher = NotionContextFetcher()
    full_pages = []
    preview_map = {item.get("id"): item for item in context_summary.get("previews", [])}

    for page_id in selected_ids:
        preview = preview_map.get(page_id, {})
        domain_hint = preview.get("domain")
        try:
            full_page = fetcher.fetch_page_full(page_id, domain=domain_hint)
            full_pages.append(full_page)
            st.caption(f"  ✓ {full_page.title} ({full_page.domain})")
        except NotionClientUnavailable:
            st.warning("⚠️ Impossible de charger une fiche Notion sélectionnée (mode hors ligne).")
            return None
        except Exception as e:
            st.warning(f"⚠️ Erreur lors du chargement de la fiche {page_id}: {e}")
            continue

    if not full_pages:
        st.warning("⚠️ Aucune fiche n'a pu être chargée. Génération sans contexte.")
        return None

    formatted = fetcher.format_context_for_llm(full_pages)
    total_tokens = sum(page.token_estimate for page in full_pages)
    
    st.success(f"✓ {len(full_pages)} fiche(s) chargée(s) (~{total_tokens} tokens)")
    
    return {
        "selected_ids": list(context_summary["selected_ids"]),
        "pages": [
            {
                "id": page.id,
                "title": page.title,
                "domain": page.domain,
                "summary": page.summary,
                "content": page.content,
                "properties": page.properties,
                "token_estimate": page.token_estimate,
                "last_edited": page.last_edited,
            }
            for page in full_pages
        ],
        "formatted": formatted,
        "token_estimate": total_tokens,
        "previews": context_summary.get("previews", []),
    }


def _ensure_generation_styles() -> None:
    if st.session_state.get("_generation_styles_loaded"):
        return

    st.markdown(
        """
        <style>
        .progress-summary {
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 0.9rem 1.1rem;
            background: #ffffff;
            margin-bottom: 1rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
        }
        .progress-summary__grid {
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
        }
        .progress-summary__item {
            flex: 1 1 160px;
            min-width: 150px;
            padding: 0.45rem 0.65rem;
            border-radius: 10px;
            background: #f3f4f6;
            border: 1px solid #e5e7eb;
        }
        .progress-summary__label {
            display: block;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: #6b7280;
        }
        .progress-summary__value {
            font-weight: 600;
            color: #111827;
            font-size: 0.95rem;
        }
        .progress-summary__brief {
            margin-top: 0.75rem;
            font-size: 0.9rem;
            color: #1f2937;
        }
        .progress-summary__brief span {
            font-weight: 600;
            color: #111827;
            display: block;
            margin-bottom: 0.25rem;
        }
        .progress-summary__brief p {
            margin: 0;
            line-height: 1.5;
        }
        .progress-card {
            text-align: center;
            padding: 0.75rem;
            border-radius: 10px;
            border: 1px solid #e5e7eb;
            background: #f8fafc;
            transition: all 0.2s ease;
        }
        .progress-card__icon {
            font-size: 24px;
        }
        .progress-card__title {
            margin-top: 0.35rem;
            font-weight: 600;
            font-size: 0.85rem;
            color: #111827;
        }
        .progress-card__status {
            margin-top: 0.2rem;
            font-size: 0.75rem;
            color: #6b7280;
        }
        .progress-card--active {
            background: #e0e7ff;
            border-color: #c7d2fe;
        }
        .progress-card--active .progress-card__status {
            color: #1e3a8a;
            font-weight: 600;
        }
        .progress-card--done {
            background: #dcfce7;
            border-color: #bbf7d0;
        }
        .progress-card--done .progress-card__status {
            color: #166534;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state["_generation_styles_loaded"] = True


def _render_step_placeholder(placeholder: DeltaGenerator, step: Dict[str, str], state: str = "idle") -> None:
    _ensure_generation_styles()

    classes = {
        "idle": "progress-card",
        "active": "progress-card progress-card--active",
        "done": "progress-card progress-card--done",
    }
    status_text = {
        "idle": step["desc"],
        "active": "En cours…",
        "done": "Terminé",
    }

    placeholder.markdown(
        """
        <div class="{classes}">
            <div class="progress-card__icon">{icon}</div>
            <div class="progress-card__title">{title}</div>
            <div class="progress-card__status">{status}</div>
        </div>
        """.format(
            classes=classes.get(state, "progress-card"),
            icon=escape(step["icon"]),
            title=escape(step["name"]),
            status=escape(status_text.get(state, step["desc"])),
        ),
        unsafe_allow_html=True,
    )


def _render_progress_summary(
    *,
    brief: str,
    model_name: str,
    model_config: Dict[str, Any],
    domain: str,
    max_tokens: int,
    context_overview: Optional[Dict[str, Any]],
) -> None:
    _ensure_generation_styles()

    icon = model_config.get("icon", "🤖")
    context_ids = context_overview.get("selected_ids", []) if context_overview else []
    token_estimate = context_overview.get("token_estimate", 0) if context_overview else 0
    brief_clean = " ".join(brief.split()) if brief else ""
    brief_preview = textwrap.shorten(brief_clean, width=180, placeholder="…") if brief_clean else "—"
    token_display = f"~{token_estimate:,}".replace(",", "\u202f") if token_estimate else "0"
    max_tokens_display = f"{max_tokens:,}".replace(",", "\u202f")

    st.markdown(
        """
        <div class="progress-summary">
            <div class="progress-summary__grid">
                <div class="progress-summary__item">
                    <span class="progress-summary__label">Modèle</span>
                    <span class="progress-summary__value">{icon} {model}</span>
                </div>
                <div class="progress-summary__item">
                    <span class="progress-summary__label">Domaine</span>
                    <span class="progress-summary__value">{domain}</span>
                </div>
                <div class="progress-summary__item">
                    <span class="progress-summary__label">Contexte</span>
                    <span class="progress-summary__value">{context_count} fiche(s)</span>
                </div>
                <div class="progress-summary__item">
                    <span class="progress-summary__label">Tokens contexte</span>
                    <span class="progress-summary__value">{token_display}</span>
                </div>
                <div class="progress-summary__item">
                    <span class="progress-summary__label">Limite sortie</span>
                    <span class="progress-summary__value">{max_tokens}</span>
                </div>
            </div>
            <div class="progress-summary__brief">
                <span>Brief</span>
                <p>{brief}</p>
            </div>
        </div>
        """.format(
            icon=escape(icon),
            model=escape(model_name),
            domain=escape(domain),
            context_count=len(context_ids),
            token_display=escape(token_display),
            max_tokens=escape(max_tokens_display),
            brief=escape(brief_preview),
        ),
        unsafe_allow_html=True,
    )


def generate_content(
    brief: str,
    intent: str,
    level: str,
    dialogue_mode: str,
    creativity: float,
    reasoning_effort: str | None,
    max_tokens: int,
    model_name: str,
    model_config: Dict[str, Any],
    domain: str,
    context_summary: Optional[Dict[str, Any]] = None,
):
    """Génère du contenu (personnage ou lieu) selon le domaine."""

    ContentWorkflow, WriterConfig, domain_config = load_workflow_dependencies(domain.lower())
    llm = create_llm(
        model_name,
        model_config,
        creativity=creativity,
        reasoning_effort=reasoning_effort,
        max_tokens=max_tokens,
    )

    writer_config = WriterConfig(
        intent=intent,
        level=level,
        dialogue_mode=dialogue_mode,
        creativity=creativity,
    )

    context_payload = _build_context_payload(context_summary)

    workflow = ContentWorkflow(domain_config, llm=llm)

    progress_container = st.container()

    context_overview = context_payload or context_summary or {"selected_ids": [], "token_estimate": 0}

    with progress_container:
        _render_progress_summary(
            brief=brief,
            model_name=model_name,
            model_config=model_config,
            domain=domain,
            max_tokens=max_tokens,
            context_overview=context_overview,
        )

        cols = st.columns(4)
        steps = [
            {"name": "Writer", "icon": "✍️", "desc": "Génération"},
            {"name": "Reviewer", "icon": "🔍", "desc": "Analyse"},
            {"name": "Corrector", "icon": "✏️", "desc": "Correction"},
            {"name": "Validator", "icon": "✅", "desc": "Validation"},
        ]

        step_placeholders: list[DeltaGenerator] = []
        for col, step in zip(cols, steps):
            with col:
                placeholder = st.empty()
                step_placeholders.append(placeholder)
                _render_step_placeholder(placeholder, step, state="idle")

        progress_bar = st.progress(0)
        status_text = st.empty()
        time_estimate = st.empty()
        time_estimate.text("⏱️ Calcul du temps en cours…")

    step_durations: list[float] = []

    try:
        start_time = time.time()

        def record_step_completion(step_index: int) -> None:
            elapsed = time.time() - start_time
            step_duration = elapsed - sum(step_durations)
            if step_duration < 0:
                step_duration = 0.0
            step_durations.append(step_duration)
            remaining_steps = len(steps) - (step_index + 1)
            if remaining_steps > 0:
                average = sum(step_durations) / len(step_durations)
                remaining = max(average * remaining_steps, 0.0)
                time_estimate.text(f"⏱️ {elapsed:.1f}s écoulées · ~{remaining:.1f}s restantes")
            else:
                time_estimate.text(f"⏱️ {elapsed:.1f}s au total")

        _render_step_placeholder(step_placeholders[0], steps[0], state="active")
        status_text.text("✍️ Writer : Génération du contenu initial...")
        progress_bar.progress(10)

        result = workflow.run(brief, writer_config, context=context_payload)

        _render_step_placeholder(step_placeholders[0], steps[0], state="done")
        record_step_completion(0)
        progress_bar.progress(25)

        _render_step_placeholder(step_placeholders[1], steps[1], state="active")
        status_text.text("🔍 Reviewer : Analyse de cohérence narrative...")
        progress_bar.progress(50)

        _render_step_placeholder(step_placeholders[1], steps[1], state="done")
        record_step_completion(1)
        progress_bar.progress(65)

        _render_step_placeholder(step_placeholders[2], steps[2], state="active")
        status_text.text("✏️ Corrector : Correction du style...")
        progress_bar.progress(80)

        _render_step_placeholder(step_placeholders[2], steps[2], state="done")
        record_step_completion(2)
        progress_bar.progress(90)

        _render_step_placeholder(step_placeholders[3], steps[3], state="active")
        status_text.text("✅ Validator : Validation finale...")

        _render_step_placeholder(step_placeholders[3], steps[3], state="done")
        record_step_completion(3)

        elapsed_time = time.time() - start_time
        status_text.text(f"✅ Terminé en {elapsed_time:.1f}s !")
        progress_bar.progress(100)

        result["model_used"] = model_name
        result["model_config"] = model_config
        if context_payload:
            result["context"] = context_payload

        json_file, md_file = workflow.save_results(result)

        success_msg = {
            "personnages": f"✅ Personnage généré avec succès ! (Modèle: {model_config['icon']} {model_name})",
            "lieux": f"✅ Lieu généré avec succès ! (Modèle: {model_config['icon']} {model_name})",
        }
        st.success(success_msg[domain.lower()])

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Cohérence",
                f"{result['coherence_score']:.2f}",
                delta="Bon" if result["coherence_score"] >= 0.7 else "À améliorer",
            )

        with col2:
            st.metric(
                "Complétude",
                f"{result['completeness_score']:.2f}",
                delta="Complet" if result["completeness_score"] >= 0.8 else "Incomplet",
            )

        with col3:
            st.metric(
                "Qualité",
                f"{result['quality_score']:.2f}",
                delta="Bon" if result["quality_score"] >= 0.7 else "À améliorer",
            )

        if result["ready_for_publication"]:
            st.markdown(
                '<div class="success-box">✅ <b>Prêt pour publication</b></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="warning-box">⚠️ <b>Nécessite révision</b></div>',
                unsafe_allow_html=True,
            )

        with st.expander("📄 Voir le contenu généré", expanded=True):
            st.markdown(result["content"])

        if result["review_issues"]:
            with st.expander(f"⚠️ Problèmes identifiés ({len(result['review_issues'])})"):
                for issue in result["review_issues"]:
                    severity = issue["severity"]
                    if severity == "critical":
                        severity_icon = "🔴"
                        box_color = "#f8d7da"
                        border_color = "#dc3545"
                    elif severity == "major":
                        severity_icon = "🟠"
                        box_color = "#fff3cd"
                        border_color = "#ffc107"
                    else:
                        severity_icon = "🟡"
                        box_color = "#d1ecf1"
                        border_color = "#17a2b8"

                    st.markdown(
                        f"""
                    <div style="background-color: {box_color}; border-left: 4px solid {border_color}; padding: 1rem; margin: 0.5rem 0; border-radius: 0.3rem;">
                        {severity_icon} <b>{issue.get('category', 'General').capitalize()}</b><br>
                        {issue['description']}
                        {f"<br><i>💡 Suggestion: {issue['suggestion']}</i>" if issue.get('suggestion') else ""}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

        if result["corrections"]:
            with st.expander(f"✏️ Corrections ({len(result['corrections'])})"):
                for corr in result["corrections"]:
                    st.markdown(
                        f"""
                    <div style="background-color: #e7f3ff; border-left: 4px solid #2196F3; padding: 1rem; margin: 0.5rem 0; border-radius: 0.3rem;">
                        <b>{corr['type']}</b>: <code>{corr['original']}</code> → <code>{corr['corrected']}</code>
                        {f"<br><i>{corr['explanation']}</i>" if corr.get('explanation') else ""}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

        col_files, col_export = st.columns([2, 1])

        with col_files:
            st.info(
                f"""
            **Fichiers sauvegardés:**
            - 📊 JSON: `{json_file.name}`
            - 📝 Markdown: `{md_file.name}`
            """
            )

        from .results import export_to_notion  # local import to avoid cycle

        with col_export:
            st.write("")
            if st.button("📤 Exporter vers Notion", help="Créer une page dans Notion"):
                export_to_notion(result)

            json_data = json_file.read_text(encoding="utf-8")
            st.download_button(
                label="💾 Télécharger JSON",
                data=json_data,
                file_name=json_file.name,
                mime="application/json",
                key=f"download_json_{json_file.stem}",
            )

    except Exception as exc:  # pragma: no cover - UI feedback path
        st.error(f"❌ Erreur lors de la génération: {exc}")
