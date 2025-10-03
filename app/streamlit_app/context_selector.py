
"""Streamlit component allowing users to curate Notion context."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

import streamlit as st

from agents.notion_context_fetcher import (
    NotionClientUnavailable,
    NotionContextFetcher,
    NotionPagePreview,
)
from agents.notion_context_matcher import MatchSuggestion, NotionContextMatcher

# Domains exposed to the user in the selector
CONTEXT_DOMAINS = ["personnages", "lieux", "communautes", "especes", "objets"]

# Suggested domain grouping per main creation domain
DOMAIN_SUGGESTION_TARGETS = {
    "personnages": ["personnages", "lieux", "communautes", "especes", "objets"],
    "lieux": ["lieux", "personnages", "communautes", "objets"],
}


def _get_fetcher() -> NotionContextFetcher:
    if "_context_fetcher" not in st.session_state:
        st.session_state._context_fetcher = NotionContextFetcher()
    return st.session_state._context_fetcher  # type: ignore[return-value]


def _get_matcher(fetcher: NotionContextFetcher) -> NotionContextMatcher:
    if "_context_matcher" not in st.session_state:
        st.session_state._context_matcher = NotionContextMatcher(fetcher=fetcher)
    return st.session_state._context_matcher  # type: ignore[return-value]


def _init_session_state() -> None:
    if "context_selection" not in st.session_state:
        st.session_state.context_selection = {
            "selected_ids": set(),
            "previews": {},
            "suggestions": [],
        }

    # Ensure mutable structures exist
    selection = st.session_state.context_selection
    selection.setdefault("selected_ids", set())
    selection.setdefault("previews", {})
    selection.setdefault("suggestions", [])

    if not isinstance(selection["selected_ids"], set):
        selection["selected_ids"] = set(selection["selected_ids"])


def _toggle_selection(page: NotionPagePreview, checked: bool) -> None:
    selection = st.session_state.context_selection
    selected_ids: set = selection["selected_ids"]
    if checked:
        selected_ids.add(page.id)
        selection["previews"][page.id] = page
    else:
        selected_ids.discard(page.id)


def _render_suggestions(brief: str, domain_key: str, matcher: NotionContextMatcher) -> None:
    selection = st.session_state.context_selection

    st.subheader("🤖 Auto-suggestion")
    col_button, col_info = st.columns([1, 4])
    with col_button:
        button_disabled = not brief.strip()
        if st.button(
            "🔍 Suggérer automatiquement",
            disabled=button_disabled,
            help="Fournir un brief pour activer la suggestion",
        ):
            targets = DOMAIN_SUGGESTION_TARGETS.get(domain_key, CONTEXT_DOMAINS)
            try:
                suggestions = matcher.suggest_context(brief, domains=targets)
                selection["suggestions"] = suggestions
            except NotionClientUnavailable:
                st.warning("Connexion Notion indisponible : suggestions automatiques désactivées.")
    with col_info:
        st.write(
            "Sélectionne jusqu'à 5 fiches pertinentes en fonction du brief."
            if brief.strip()
            else "Renseigne un brief pour activer l'auto-sélection."
        )

    if not selection["suggestions"]:
        st.info("Aucune suggestion disponible pour le moment.")
        return

    st.markdown("#### Suggestions")
    for suggestion in selection["suggestions"]:
        assert isinstance(suggestion, MatchSuggestion)
        page = suggestion.page
        checked = page.id in selection["selected_ids"] or suggestion.auto_select
        checkbox = st.checkbox(
            f"{page.title} — {int(suggestion.score * 100)}%",
            value=checked,
            key=f"suggestion_{page.id}",
            help=page.summary or "",
        )
        _toggle_selection(page, checkbox)

        with st.expander(f"Détails · {page.domain.capitalize()} · ~{page.token_estimate} tokens", expanded=False):
            st.markdown(f"**Résumé :** {page.summary or '—'}")
            if suggestion.matched_keywords:
                keywords = ", ".join(suggestion.matched_keywords)
                st.caption(f"Correspondances : {keywords}")


def _render_manual_selection(previews_by_domain: Dict[str, List[NotionPagePreview]]) -> None:
    st.subheader("🗂️ Sélection manuelle")
    tabs = st.tabs([domain.capitalize() for domain in CONTEXT_DOMAINS])

    for tab, domain in zip(tabs, CONTEXT_DOMAINS):
        with tab:
            pages = previews_by_domain.get(domain, [])
            if not pages:
                st.caption("Aucune fiche disponible dans ce domaine.")
                continue

            search = st.text_input(
                "Recherche",
                key=f"context_search_{domain}",
                placeholder="Nom ou mot-clé",
            )
            filtered = [
                page
                for page in pages
                if not search
                or search.lower() in page.title.lower()
                or search.lower() in page.summary.lower()
            ]

            for page in filtered[:80]:  # Safety cap to avoid overwhelming the UI
                checked = page.id in st.session_state.context_selection["selected_ids"]
                checkbox = st.checkbox(
                    f"{page.title} · ~{page.token_estimate} tokens",
                    value=checked,
                    key=f"manual_{domain}_{page.id}",
                    help=page.summary or "Sans aperçu",
                )
                _toggle_selection(page, checkbox)


def _render_selected_summary(fetcher: NotionContextFetcher) -> Dict[str, Any]:
    selection = st.session_state.context_selection
    selected_ids = list(selection["selected_ids"])

    st.subheader(f"✅ Contexte sélectionné ({len(selected_ids)} fiches)")

    previews_cache: Dict[str, NotionPagePreview] = selection["previews"]
    ordered_previews: List[NotionPagePreview] = []
    total_tokens = 0
    for page_id in selected_ids:
        preview = previews_cache.get(page_id)
        if preview is None:
            try:
                preview = fetcher.fetch_page_preview(page_id)
                previews_cache[page_id] = preview
            except NotionClientUnavailable:
                continue
        ordered_previews.append(preview)
        total_tokens += preview.token_estimate

    for preview in ordered_previews:
        col_label, col_remove = st.columns([6, 1])
        with col_label:
            st.markdown(f"**{preview.title}** · {preview.domain.capitalize()} · ~{preview.token_estimate} tokens")
            if preview.summary:
                st.caption(preview.summary)
        with col_remove:
            if st.button("Retirer", key=f"remove_{preview.id}"):
                _toggle_selection(preview, False)
                st.experimental_rerun()

    st.metric("Total estimé", f"~{total_tokens} tokens")
    if total_tokens > 50000:
        st.warning("⚠️ Contexte volumineux : envisager de réduire en dessous de 50 000 tokens.")

    return {
        "selected_ids": selected_ids,
        "previews": [asdict(preview) for preview in ordered_previews],
        "token_estimate": total_tokens,
    }


def render_context_selector(domain: str, brief: str) -> Dict[str, Any]:
    """Render the Streamlit context selector and return selection metadata."""

    _init_session_state()

    domain_key = domain.lower()
    fetcher = _get_fetcher()
    matcher = _get_matcher(fetcher)

    try:
        previews_by_domain = fetcher.fetch_all_databases()
    except NotionClientUnavailable:
        st.warning("Impossible de récupérer les fiches Notion (mode hors ligne).")
        return {"selected_ids": [], "previews": [], "token_estimate": 0}

    _render_suggestions(brief, domain_key, matcher)
    _render_manual_selection(previews_by_domain)
    summary = _render_selected_summary(fetcher)

    return summary

