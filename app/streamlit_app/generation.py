"""Content generation helpers for the Streamlit UI."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, Optional

import streamlit as st

from agents.notion_context_fetcher import NotionClientUnavailable, NotionContextFetcher
from .cache import load_workflow_dependencies


DEFAULT_STEP_ESTIMATES = {
    "writer": 18.0,
    "reviewer": 12.0,
    "corrector": 10.0,
    "validator": 4.0,
}


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
    context_count = len(context_summary.get("selected_ids", [])) if context_summary else 0
    context_tokens = (
        context_summary.get("token_estimate", 0) if context_summary else 0
    )
    step_order = ["writer", "reviewer", "corrector", "validator"]
    step_history = st.session_state.get("step_duration_history", {})
    for step in step_order:
        step_history.setdefault(step, [])
    st.session_state.step_duration_history = step_history

    avg_durations = {}
    for step in step_order:
        history_values = step_history.get(step, [])
        if history_values:
            avg_durations[step] = sum(history_values) / len(history_values)
        else:
            avg_durations[step] = DEFAULT_STEP_ESTIMATES[step]

    estimated_total = sum(avg_durations.values())

    with progress_container:
        cols = st.columns(4)
        steps = [
            {"name": "Writer", "icon": "✍️", "desc": "Génération"},
            {"name": "Reviewer", "icon": "🔍", "desc": "Analyse"},
            {"name": "Corrector", "icon": "✏️", "desc": "Correction"},
            {"name": "Validator", "icon": "✅", "desc": "Validation"},
        ]

        step_placeholders = []
        for col, step in zip(cols, steps):
            with col:
                placeholder = st.empty()
                step_placeholders.append(placeholder)
                placeholder.markdown(
                    f"""
                <div style='text-align: center; padding: 10px; border-radius: 5px; background-color: #1E1E1E;'>
                    <div style='font-size: 24px;'>{step['icon']}</div>
                    <div style='font-size: 12px; color: #888;'>{step['name']}</div>
                    <div style='font-size: 10px; color: #666;'>{step['desc']}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

        progress_bar = st.progress(0)
        status_text = st.empty()
        time_estimate = st.empty()
        time_estimate.markdown(
            f"⏱️ Estimation initiale : ~{estimated_total:.1f}s (historique)")

        recap_badges = [
            f"<span class='badge-soft'>{model_config['icon']} {model_name}</span>",
            f"<span class='badge-soft secondary'>Intent : {intent}</span>",
            f"<span class='badge-soft secondary'>Niveau : {level}</span>",
            f"<span class='badge-soft secondary'>Tokens max : {max_tokens}</span>",
        ]
        if dialogue_mode and dialogue_mode != "none":
            recap_badges.append(
                f"<span class='badge-soft secondary'>Dialogue : {dialogue_mode}</span>"
            )
        if context_count:
            recap_badges.append(
                f"<span class='badge-soft'>Contexte : {context_count} fiche(s) · ~{context_tokens} tokens</span>"
            )

        recap_html = "".join(recap_badges)
        st.markdown(
            f"<div class='run-recap'>{recap_html}</div>",
            unsafe_allow_html=True,
        )

    try:
        start_time = time.time()

        step_placeholders[0].markdown(
            """
        <div style='text-align: center; padding: 10px; border-radius: 5px; background-color: #667eea; color: white;'>
            <div style='font-size: 24px;'>✍️</div>
            <div style='font-size: 12px; font-weight: bold;'>Writer</div>
            <div style='font-size: 10px;'>En cours...</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        status_text.text("✍️ Writer : Génération du contenu initial...")
        progress_bar.progress(10)

        result = workflow.run(brief, writer_config, context=context_payload)

        history_entries = result.get("history", [])
        step_durations: Dict[str, float] = {}
        previous_timestamp = datetime.fromtimestamp(start_time)
        for entry in history_entries:
            step_key = entry.get("step", "").lower()
            timestamp_str = entry.get("timestamp")
            if step_key not in step_order or not timestamp_str:
                continue
            try:
                current_timestamp = datetime.fromisoformat(timestamp_str)
            except ValueError:
                continue
            duration = max((current_timestamp - previous_timestamp).total_seconds(), 0.1)
            step_durations[step_key] = duration
            previous_timestamp = current_timestamp

        for step in step_order:
            step_durations.setdefault(step, avg_durations[step])

        def update_time_feedback(completed_steps: int) -> None:
            elapsed_total = sum(
                step_durations[step] for step in step_order[:completed_steps]
            )
            remaining_total = sum(
                step_durations[step] for step in step_order[completed_steps:]
            )
            time_estimate.markdown(
                f"⏱️ {elapsed_total:.1f}s écoulées • ~{remaining_total:.1f}s restantes"
            )

        step_placeholders[0].markdown(
            """
        <div style='text-align: center; padding: 10px; border-radius: 5px; background-color: #28a745; color: white;'>
            <div style='font-size: 24px;'>✅</div>
            <div style='font-size: 12px; font-weight: bold;'>Writer</div>
            <div style='font-size: 10px;'>Terminé</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        progress_bar.progress(25)
        update_time_feedback(1)

        step_placeholders[1].markdown(
            """
        <div style='text-align: center; padding: 10px; border-radius: 5px; background-color: #667eea; color: white;'>
            <div style='font-size: 24px;'>🔍</div>
            <div style='font-size: 12px; font-weight: bold;'>Reviewer</div>
            <div style='font-size: 10px;'>En cours...</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        status_text.text("🔍 Reviewer : Analyse de cohérence narrative...")
        progress_bar.progress(50)

        step_placeholders[1].markdown(
            """
        <div style='text-align: center; padding: 10px; border-radius: 5px; background-color: #28a745; color: white;'>
            <div style='font-size: 24px;'>✅</div>
            <div style='font-size: 12px; font-weight: bold;'>Reviewer</div>
            <div style='font-size: 10px;'>Terminé</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        progress_bar.progress(65)
        update_time_feedback(2)

        step_placeholders[2].markdown(
            """
        <div style='text-align: center; padding: 10px; border-radius: 5px; background-color: #667eea; color: white;'>
            <div style='font-size: 24px;'>✏️</div>
            <div style='font-size: 12px; font-weight: bold;'>Corrector</div>
            <div style='font-size: 10px;'>En cours...</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        status_text.text("✏️ Corrector : Correction du style...")
        progress_bar.progress(80)

        step_placeholders[2].markdown(
            """
        <div style='text-align: center; padding: 10px; border-radius: 5px; background-color: #28a745; color: white;'>
            <div style='font-size: 24px;'>✅</div>
            <div style='font-size: 12px; font-weight: bold;'>Corrector</div>
            <div style='font-size: 10px;'>Terminé</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        progress_bar.progress(90)
        update_time_feedback(3)

        step_placeholders[3].markdown(
            """
        <div style='text-align: center; padding: 10px; border-radius: 5px; background-color: #667eea; color: white;'>
            <div style='font-size: 24px;'>✅</div>
            <div style='font-size: 12px; font-weight: bold;'>Validator</div>
            <div style='font-size: 10px;'>En cours...</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        status_text.text("✅ Validator : Validation finale...")

        step_placeholders[3].markdown(
            """
        <div style='text-align: center; padding: 10px; border-radius: 5px; background-color: #28a745; color: white;'>
            <div style='font-size: 24px;'>✅</div>
            <div style='font-size: 12px; font-weight: bold;'>Validator</div>
            <div style='font-size: 10px;'>Terminé</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        elapsed_time = time.time() - start_time
        status_text.text(f"✅ Terminé en {elapsed_time:.1f}s !")
        progress_bar.progress(100)
        update_time_feedback(len(step_order))

        for step in step_order:
            history_list = st.session_state.step_duration_history.setdefault(step, [])
            history_list.append(step_durations[step])
            st.session_state.step_duration_history[step] = history_list[-10:]

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
