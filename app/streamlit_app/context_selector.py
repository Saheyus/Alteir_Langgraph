
"""Streamlit component allowing users to curate Notion context."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from typing import Any, Dict, List, Optional

import streamlit as st

import pandas as pd

from agents.notion_context_fetcher import (
    NotionClientUnavailable,
    NotionContextFetcher,
    NotionPagePreview,
)
from agents.notion_context_matcher import MatchSuggestion, NotionContextMatcher

# Domains exposed to the user in the selector
CONTEXT_DOMAINS = ["personnages", "lieux", "communautes", "especes", "objets"]

DOMAIN_COLORS = {
    "personnages": "#6366F1",
    "lieux": "#10B981",
    "communautes": "#F59E0B",
    "especes": "#EC4899",
    "objets": "#8B5CF6",
}

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

    suggestion_rows = []
    for suggestion in selection["suggestions"]:
        assert isinstance(suggestion, MatchSuggestion)
        page = suggestion.page
        suggestion_rows.append(
            {
                "id": page.id,
                "Sélection": page.id in selection["selected_ids"] or suggestion.auto_select,
                "Titre": page.title,
                "Pertinence": int(round(suggestion.score * 100)),
                "Domaine": page.domain.capitalize(),
                "Tokens": page.token_estimate,
                "Résumé": page.summary or "—",
            }
        )

    suggestion_df = pd.DataFrame(suggestion_rows).set_index("id")
    edited_df = st.data_editor(
        suggestion_df,
        hide_index=True,
        use_container_width=True,
        key="context_suggestions_editor",
        column_config={
            "Sélection": st.column_config.CheckboxColumn(
                "Sélection",
                help="Ajouter la fiche au contexte",
            ),
            "Pertinence": st.column_config.ProgressColumn(
                "Pertinence",
                format="%d%%",
                min_value=0,
                max_value=100,
            ),
            "Tokens": st.column_config.NumberColumn(
                "Tokens",
                format="~%d",
                help="Estimation du coût contextuel",
            ),
            "Résumé": st.column_config.TextColumn("Résumé", width="large"),
        },
    )

    for suggestion in selection["suggestions"]:
        page = suggestion.page
        row = edited_df.loc[page.id]
        _toggle_selection(page, bool(row["Sélection"]))


def _render_manual_selection(previews_by_domain: Dict[str, List[NotionPagePreview]]) -> None:
    st.subheader("🗂️ Sélection manuelle")

    all_pages: List[Dict[str, Any]] = []
    page_lookup: Dict[str, NotionPagePreview] = {}
    for domain, pages in previews_by_domain.items():
        for page in pages:
            all_pages.append(
                {
                    "id": page.id,
                    "Sélection": page.id in st.session_state.context_selection["selected_ids"],
                    "Titre": page.title,
                    "Domaine": domain.capitalize(),
                    "Tokens": page.token_estimate,
                    "Résumé": page.summary or "—",
                }
            )
            page_lookup[page.id] = page

    if not all_pages:
        st.caption("Aucune fiche disponible pour le moment.")
        return

    domains_available = sorted({row["Domaine"] for row in all_pages})
    max_tokens = max((row["Tokens"] for row in all_pages), default=0)
    token_cap_default = max(max_tokens, 1000)

    filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 1])
    with filter_col1:
        domain_filter = st.multiselect(
            "Domaines",
            options=domains_available,
            default=domains_available,
            key="manual_domain_filter",
        )
    with filter_col2:
        search = st.text_input(
            "Recherche globale",
            key="manual_search_filter",
            placeholder="Titre, résumé ou mot-clé",
        )
    with filter_col3:
        token_cap = st.slider(
            "Tokens max",
            min_value=0,
            max_value=token_cap_default,
            value=token_cap_default,
            step=500,
            key="manual_token_cap",
        )

    filtered_rows = [
        row
        for row in all_pages
        if row["Domaine"] in domain_filter
        and row["Tokens"] <= token_cap
        and (
            not search
            or search.lower() in row["Titre"].lower()
            or search.lower() in row["Résumé"].lower()
        )
    ]

    if not filtered_rows:
        st.info("Aucun résultat ne correspond aux filtres actuels.")
        return

    filtered_rows = filtered_rows[:200]
    manual_df = pd.DataFrame(filtered_rows).set_index("id")
    edited_manual = st.data_editor(
        manual_df,
        hide_index=True,
        use_container_width=True,
        key="context_manual_editor",
        column_config={
            "Sélection": st.column_config.CheckboxColumn(
                "Sélection",
                help="Cocher pour inclure la fiche",
            ),
            "Tokens": st.column_config.NumberColumn(
                "Tokens",
                format="~%d",
            ),
            "Résumé": st.column_config.TextColumn("Résumé", width="large"),
        },
    )

    for page_id, row in edited_manual.iterrows():
        page = page_lookup.get(page_id)
        if not page:
            continue
        _toggle_selection(page, bool(row["Sélection"]))


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

    if ordered_previews:
        grid_columns = st.columns(min(3, len(ordered_previews)))
        for idx, preview in enumerate(ordered_previews):
            column = grid_columns[idx % len(grid_columns)]
            with column:
                color = DOMAIN_COLORS.get(preview.domain, "#475569")
                st.markdown(
                    f"""
                    <div class="context-card" style="border-left: 4px solid {color};">
                        <div class="context-card__title">{preview.title}</div>
                        <div class="context-card__meta">
                            <span>{preview.domain.capitalize()}</span>
                            <span>~{preview.token_estimate} tokens</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Retirer", key=f"remove_{preview.id}", use_container_width=True):
                    _toggle_selection(preview, False)
                    st.experimental_rerun()

        domain_counts = Counter(preview.domain for preview in ordered_previews)
        top_domain, top_count = domain_counts.most_common(1)[0]
        st.caption(
            f"Domaine dominant : {top_domain.capitalize()} ({top_count} fiche(s))"
        )

    st.markdown(
        f"<div class='badge-soft'>Total estimé : ~{total_tokens} tokens</div>",
        unsafe_allow_html=True,
    )
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

