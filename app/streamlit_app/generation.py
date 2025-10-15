"""Content generation helpers for the Streamlit UI."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional
from pathlib import Path
import json

import streamlit as st

from agents.notion_context_fetcher import NotionClientUnavailable, NotionContextFetcher
from .cache import load_workflow_dependencies
from dataclasses import asdict


def create_llm(
    model_name: str,
    model_config: Dict[str, Any],
    creativity: float | None = None,
    reasoning_effort: str | None = None,
    verbosity: str | None = None,
    max_tokens: int | None = None,
):
    """Crée une instance LLM selon le modèle choisi."""
    import os
    from langchain_openai import ChatOpenAI
    import streamlit as st

    provider = model_config.get("provider", "OpenAI")
    
    # Clamp max_tokens to model's limit to avoid 400 errors
    model_max = model_config.get("max_tokens", 2000)
    effective_max_tokens = min(max_tokens or model_max, model_max)

    if provider == "OpenAI":
        # Check OpenAI key early and fail fast with clear UI message
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key.startswith("your_") or api_key.startswith("sk-proj-YOUR"):
            try:
                st.error("⚠️ **OPENAI_API_KEY manquante ou invalide.** Ajoute ta clé OpenAI dans le fichier `.env` à la racine, puis relance l'app.")
            except Exception:
                pass
            raise RuntimeError(f"Missing or invalid OPENAI_API_KEY for model {model_name}. Check your .env file.")
        if model_config.get("uses_reasoning"):
            # GPT-5 Responses API: reasoning effort passed via reasoning param, not extra_body
            llm_config: Dict[str, Any] = {
                "model": model_config["name"],
                "use_responses_api": True,
                "reasoning": {
                    "effort": reasoning_effort or model_config.get("default_reasoning", "minimal")
                },
                "max_tokens": effective_max_tokens,
            }
            # Verbosity: prefer explicit kw if supported; otherwise use model_kwargs
            if verbosity:
                try:
                    # Newer langchain_openai forwards unknown kwargs to provider
                    return ChatOpenAI(**llm_config, verbosity=verbosity)
                except TypeError:
                    llm_config["model_kwargs"] = {"verbosity": verbosity}
                    return ChatOpenAI(**llm_config)
            return ChatOpenAI(**llm_config)
        else:
            # Classic chat models (GPT-4, GPT-4o-mini)
            llm_config: Dict[str, Any] = {
                "model": model_config["name"],
                "max_tokens": effective_max_tokens,
                "temperature": creativity,
            }
            return ChatOpenAI(**llm_config)

    elif provider == "Anthropic":
        # Anthropic models are handled via ChatAnthropic
        # Do not enforce API key here; let the underlying client resolve it from the environment.
        from langchain_anthropic import ChatAnthropic

        # Claude uses standard params; avoid passing vendor-specific kwargs for testability
        return ChatAnthropic(
            model=model_config["name"],
            temperature=(creativity if creativity is not None else 0.7),
            max_tokens=effective_max_tokens,
        )

    else:
        # Fallback: try OpenAI signature to avoid crashing
        return ChatOpenAI(
            model=model_config["name"],
            temperature=creativity,
            max_tokens=effective_max_tokens,
        )


def _build_context_payload(context_summary: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Fetch full Notion pages for the selected context and format them."""

    # Primary path: use provided summary
    if not context_summary or not context_summary.get("selected_ids"):
        # Fallback 1: use last computed summary from session
        try:
            ss_summary = (st.session_state.get("selected_context_summary") or {})
            if ss_summary and ss_summary.get("selected_ids"):
                context_summary = ss_summary
                st.caption("📌 Contexte récupéré depuis la sélection en mémoire")
        except Exception:
            pass

    if not context_summary or not context_summary.get("selected_ids"):
        # Fallback 2: reconstruct from raw session selection
        try:
            selection = st.session_state.get("context_selection") or {}
            selected_ids = list(selection.get("selected_ids") or [])
            if selected_ids:
                previews_map = selection.get("previews") or {}
                previews_list = []
                for pid in selected_ids:
                    pv = previews_map.get(pid)
                    if pv is None:
                        continue
                    try:
                        # Convert dataclass to dict if applicable
                        if hasattr(pv, "__dataclass_fields__"):
                            previews_list.append(asdict(pv))
                        elif isinstance(pv, dict):
                            previews_list.append(pv)
                    except Exception:
                        # Best-effort; ignore malformed preview
                        continue
                if previews_list:
                    context_summary = {
                        "selected_ids": selected_ids,
                        "previews": previews_list,
                        "token_estimate": sum((p.get("token_estimate", 0) for p in previews_list if isinstance(p, dict))),
                    }
                    st.caption("📌 Contexte reconstruit depuis la sélection active")
        except Exception:
            # If anything goes wrong, continue to no-context path below
            pass

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
    verbosity: str | None,
    max_tokens: int,
    model_name: str,
    model_config: Dict[str, Any],
    domain: str,
    context_summary: Optional[Dict[str, Any]] = None,
    include_reasoning: bool = False,
):
    """Génère du contenu (personnage ou lieu) selon le domaine."""

    ContentWorkflow, WriterConfig, domain_config = load_workflow_dependencies(domain.lower())
    llm = create_llm(
        model_name,
        model_config,
        creativity=creativity,
        reasoning_effort=reasoning_effort,
        verbosity=verbosity,
        max_tokens=max_tokens,
    )

    writer_config = WriterConfig(
        intent=intent,
        level=level,
        dialogue_mode=dialogue_mode,
        creativity=creativity,
    )

    context_payload = _build_context_payload(context_summary)
    # Inject Vision page as primary context
    try:
        from config.notion_config import NotionConfig
        from agents.notion_context_fetcher import NotionContextFetcher
        vision_id = NotionConfig.VISION_PAGE_ID
        fetcher = NotionContextFetcher()
        vision_page = fetcher.fetch_page_full(vision_id, domain="vision")
        # Convert to plain dict to ensure JSON-serializable context
        vision_page_dict = {
            "id": vision_page.id,
            "title": vision_page.title,
            "domain": vision_page.domain,
            "summary": vision_page.summary,
            "content": vision_page.content,
            "properties": vision_page.properties,
            "token_estimate": vision_page.token_estimate,
            "last_edited": vision_page.last_edited,
        }
        if context_payload is None:
            context_payload = {
                "selected_ids": [vision_page.id],
                "pages": [vision_page_dict],
                "formatted": fetcher.format_context_for_llm([vision_page]),
                "token_estimate": vision_page.token_estimate,
                "previews": [],
            }
        else:
            # Prepend to pages and rebuild formatted/context tokens
            existing_pages = context_payload.get("pages", [])
            # formatted needs NotionPageContent objects, so use a temp list
            temp_pages_for_format = [vision_page]
            formatted = fetcher.format_context_for_llm(temp_pages_for_format)
            pages = [vision_page_dict] + existing_pages
            context_payload.update({
                "selected_ids": [vision_page.id] + list(context_payload.get("selected_ids", [])),
                "pages": pages,
                "formatted": formatted,
                "token_estimate": sum(p.get("token_estimate", 0) for p in pages),
            })
        st.caption("📌 Contexte primaire ajouté: Vision")
    except Exception:
        # Best-effort; continue without blocking UI
        pass
    # Safety log for full context usage
    if context_payload and context_payload.get("pages"):
        st.caption(f"📚 Contexte chargé: {len(context_payload['pages'])} page(s) (~{context_payload.get('token_estimate', 0)} tokens)")

    workflow = ContentWorkflow(domain_config, llm=llm)

    progress_container = st.container()

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

    # Simple progress/ETA tracker (rolling average persisted in outputs/metrics.json)
    metrics_path = Path("outputs") / "metrics.json"
    try:
        prior = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
    except Exception:
        prior = {}

    def _estimate_total_seconds(token_estimate: int | None) -> float:
        # Heuristic: base + 0.0015s per token + model factor
        base = 8.0
        per_token = 0.0015 * (token_estimate or 2000)
        model_factor = 1.0 if model_config.get("uses_reasoning") else 0.7
        hist = prior.get("avg_total_s", 30.0)
        return max(6.0, 0.5 * hist + 0.5 * (base + per_token) * model_factor)

    # Use context token estimate if available (avoid double fetch)
    eta_seconds = _estimate_total_seconds(context_payload.get("token_estimate") if context_payload else None)
    time_estimate.text(f"⏱️ Temps estimé : ~{int(eta_seconds)}s")

    # Resolve include_reasoning before entering try block
    if model_config.get("provider") == "OpenAI":
        include_reasoning = bool(model_config.get("uses_reasoning"))
    else:
        include_reasoning = bool(include_reasoning)

    try:
        start_time = time.time()

        # --- Exécution itérative avec mises à jour UI par étape ---
        # Writer
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

        # Collapsible draft area containing reasoning first, then live streams
        reason_writer = reason_reviewer = reason_corrector = reason_validator = None
        draft_expander = st.expander("📝 Ébauche (en direct)", expanded=True)
        with draft_expander:
            if include_reasoning:
                reasoning_expander = st.expander("💭 Raisonnement (en direct)", expanded=False)
                with reasoning_expander:
                    reason_writer = st.empty()
                    reason_reviewer = st.empty()
                    reason_corrector = st.empty()
                    reason_validator = st.empty()
            stream_area = st.container()
            live_writer = stream_area.empty()
            live_reviewer = stream_area.empty()
            live_corrector = stream_area.empty()
            live_validator = stream_area.empty()

        content_buffer = {"writer": [], "reviewer": [], "corrector": [], "validator": []}
        reasoning_buffer = {"writer": [], "reviewer": [], "corrector": [], "validator": []}
        result = None

        for event, payload in workflow.run_iter_live(
            brief,
            writer_config,
            context=context_payload,
            include_reasoning=include_reasoning,
        ):
            if event == "writer:start":
                status_text.text("✍️ Writer : Génération du contenu initial...")
                progress_bar.progress(10)
            elif event == "writer:delta":
                text = payload.get("text", "")
                if text:
                    content_buffer["writer"].append(text)
                live_writer.markdown("".join(content_buffer["writer"]) + " ▌")
                if include_reasoning and payload.get("reasoning") and reason_writer is not None:
                    reasoning_buffer["writer"].append(payload["reasoning"])
                    reason_writer.markdown("".join(reasoning_buffer["writer"]))
            elif event == "writer:done":
                live_writer.markdown("".join(content_buffer["writer"]))
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
                progress_bar.progress(35)
                result = payload
            elif event == "reviewer:start":
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
                progress_bar.progress(45)
            elif event == "reviewer:delta":
                text = payload.get("text", "")
                if text:
                    content_buffer["reviewer"].append(text)
                live_reviewer.markdown("".join(content_buffer["reviewer"]) + " ▌")
                if include_reasoning and payload.get("reasoning") and reason_reviewer is not None:
                    reasoning_buffer["reviewer"].append(payload["reasoning"])
                    reason_reviewer.markdown("".join(reasoning_buffer["reviewer"]))
            elif event == "reviewer:done":
                live_reviewer.markdown("".join(content_buffer["reviewer"]))
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
                result = payload
            elif event == "corrector:start":
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
                progress_bar.progress(75)
            elif event == "corrector:delta":
                text = payload.get("text", "")
                if text:
                    content_buffer["corrector"].append(text)
                live_corrector.markdown("".join(content_buffer["corrector"]) + " ▌")
                if include_reasoning and payload.get("reasoning") and reason_corrector is not None:
                    reasoning_buffer["corrector"].append(payload["reasoning"])
                    reason_corrector.markdown("".join(reasoning_buffer["corrector"]))
            elif event == "corrector:done":
                live_corrector.markdown("".join(content_buffer["corrector"]))
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
                result = payload
            elif event == "validator:start":
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
                progress_bar.progress(95)
            elif event == "validator:delta":
                text = payload.get("text", "")
                if text:
                    content_buffer["validator"].append(text)
                live_validator.markdown("".join(content_buffer["validator"]) + " ▌")
                if include_reasoning and payload.get("reasoning") and reason_validator is not None:
                    reasoning_buffer["validator"].append(payload["reasoning"])
                    reason_validator.markdown("".join(reasoning_buffer["validator"]))
            elif event == "validator:done":
                live_validator.markdown("".join(content_buffer["validator"]))
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
                result = payload
                # No immediate break; loop will end naturally after last event
                try:
                    # Auto-collapse draft after completion
                    draft_expander.empty()
                except Exception:
                    pass
        # Writer "done" card already updated in writer:done

        # After live completes, result contains final state (from last :done)
        progress_bar.progress(100)

        elapsed_time = time.time() - start_time
        
        # Check for auth/API errors in result metadata
        if result and result.get("writer_metadata", {}).get("error"):
            error_msg = result["writer_metadata"]["error"]
            st.error(error_msg)
            status_text.text(f"❌ Échec après {elapsed_time:.1f}s")
            return  # Stop here, don't save empty result
        
        # Check for empty content (generation failed silently)
        if not result or not result.get("content") or len(result.get("content", "").strip()) == 0:
            st.error("❌ **Génération échouée** : le contenu est vide. Vérifie tes clés API dans `.env` et relance.")
            status_text.text(f"❌ Échec après {elapsed_time:.1f}s")
            return
        
        status_text.text(f"✅ Terminé en {elapsed_time:.1f}s !")
        progress_bar.progress(100)
        time_estimate.text("")

        # Persist rolling metrics
        try:
            prev_avg = float(prior.get("avg_total_s", elapsed_time))
            new_avg = 0.7 * prev_avg + 0.3 * elapsed_time
            prior["avg_total_s"] = new_avg
            metrics_path.parent.mkdir(parents=True, exist_ok=True)
            metrics_path.write_text(json.dumps(prior, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

        result["model_used"] = model_name
        # Enrich model_config with runtime knobs for auditability
        # Clamp max_tokens to model's limit (same logic as in create_llm)
        model_max = model_config.get("max_tokens", 2000)
        effective_max_tokens = min(max_tokens or model_max, model_max)
        
        enriched_model_config = dict(model_config)
        if model_config.get("uses_reasoning"):
            # Surface reasoning effort and verbosity when available
            enriched_model_config.setdefault("runtime", {})
            enriched_model_config["runtime"].update({
                "reasoning_effort": reasoning_effort,
                # Try explicit attribute first, then model_kwargs
                "verbosity": (
                    getattr(llm, "verbosity", None)
                    if hasattr(llm, "verbosity") else (
                        llm.model_kwargs.get("verbosity")
                        if hasattr(llm, "model_kwargs") and isinstance(getattr(llm, "model_kwargs", None), dict)
                        else None
                    )
                ),
                "max_tokens": effective_max_tokens,
            })
        else:
            enriched_model_config.setdefault("runtime", {})
            enriched_model_config["runtime"].update({
                "temperature": creativity,
                "max_tokens": effective_max_tokens,
            })
        result["model_config"] = enriched_model_config
        if context_payload:
            result["context"] = context_payload

        json_file, md_file = workflow.save_results(result)

        # Log a concise output summary in Streamlit console too
        try:
            content_len = len(result.get("content", ""))
            num_issues = len(result.get("review_issues", []) or [])
            num_corrections = len(result.get("corrections", []) or [])
            ctx_tokens = (result.get("context") or {}).get("token_estimate")
            st.caption(
                f"🧾 Résumé: {content_len} caractères | {num_issues} problèmes | {num_corrections} corrections | tokens contexte ≈ {ctx_tokens}"
            )
        except Exception:
            pass

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

        with st.expander("📄 Contenu final", expanded=True):
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
                    <div style="background-color: {box_color}; border-left: 4px solid {border_color}; padding: 1rem; margin: 0.5rem 0; border-radius: 0.3rem; color: #000;">
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
                    <div style="background-color: #e7f3ff; border-left: 4px solid #2196F3; padding: 1rem; margin: 0.5rem 0; border-radius: 0.3rem; color: #000;">
                        <b>{corr['type']}</b>: <code style="background-color: #fffbe6; color: #000; padding: 0 4px; border-radius: 3px;">{corr['original']}</code> → <code style="background-color: #fffbe6; color: #000; padding: 0 4px; border-radius: 3px;">{corr['corrected']}</code>
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
            if st.button("📤 Exporter vers Notion", help="Créer une page dans Notion", key="export_btn_creation"):
                st.session_state.trigger_export = True

            json_data = json_file.read_text(encoding="utf-8")
            st.download_button(
                label="💾 Télécharger JSON",
                data=json_data,
                file_name=json_file.name,
                mime="application/json",
                key=f"download_json_{json_file.stem}",
            )

        # Feedback OUTSIDE columns so it persists across reruns
        export_feedback_area = st.container()
        if st.session_state.get("trigger_export", False):
            st.session_state.trigger_export = False
            with export_feedback_area:
                export_to_notion(result)

    except Exception as exc:  # pragma: no cover - UI feedback path
        st.error(f"❌ Erreur lors de la génération: {exc}")
