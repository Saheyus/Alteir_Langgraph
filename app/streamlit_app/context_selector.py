
"""Streamlit component allowing users to curate Notion context."""

from __future__ import annotations

from dataclasses import asdict
from html import escape
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
    "personnages": "#e0f2fe",
    "lieux": "#ede9fe",
    "communautes": "#fef9c3",
    "especes": "#dcfce7",
    "objets": "#fee2e2",
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


def _ensure_selector_styles() -> None:
    if st.session_state.get("_context_selector_styles_loaded"):
        return

    st.markdown(
        """
        <style>
        .context-total {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            font-weight: 600;
            color: #111827;
            margin-bottom: 0.75rem;
            background: #f8fafc;
            padding: 0.4rem 0.75rem;
            border-radius: 999px;
            border: 1px solid #e2e8f0;
        }
        .context-total__badge {
            background: #e0f2fe;
            color: #0c4a6e;
            padding: 0.2rem 0.65rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .context-chip-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
            gap: 0.75rem;
            margin-bottom: 0.75rem;
        }
        .context-chip {
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 0.75rem;
            background: #ffffff;
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
        }
        .context-chip__header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 0.5rem;
        }
        .context-chip__title {
            font-weight: 600;
            color: #111827;
            flex: 1;
        }
        .context-chip__badge {
            font-size: 0.75rem;
            border-radius: 999px;
            padding: 0.2rem 0.6rem;
            font-weight: 600;
            color: #1f2937;
            border: 1px solid rgba(17, 24, 39, 0.08);
        }
        .context-chip__meta {
            font-size: 0.8rem;
            color: #4b5563;
        }
        .context-chip__summary {
            font-size: 0.85rem;
            color: #374151;
        }
        .context-chip__actions {
            display: flex;
            justify-content: flex-end;
        }
        .context-chip__actions button {
            width: 100%;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state["_context_selector_styles_loaded"] = True


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

    table_rows: List[Dict[str, Any]] = []
    page_lookup: Dict[str, NotionPagePreview] = {}
    for suggestion in selection["suggestions"]:
        assert isinstance(suggestion, MatchSuggestion)
        page = suggestion.page
        page_lookup[page.id] = page
        is_selected = page.id in selection["selected_ids"] or suggestion.auto_select
        if is_selected and page.id not in selection["selected_ids"]:
            _toggle_selection(page, True)

        table_rows.append(
            {
                "ID": page.id,
                "Sélection": is_selected,
                "Titre": page.title,
                "Score (%)": int(round(suggestion.score * 100)),
                "Domaine": page.domain.capitalize(),
                "Tokens": page.token_estimate,
                "Résumé": suggestion.page.summary or page.summary or "—",
                "Mots-clés": ", ".join(suggestion.matched_keywords) if suggestion.matched_keywords else "",
            }
        )

    suggestions_df = pd.DataFrame(table_rows).set_index("ID")

    edited_df = st.data_editor(
        suggestions_df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Sélection": st.column_config.CheckboxColumn(
                "Sélection",
                help="Cocher pour ajouter la fiche au contexte",
            ),
            "Score (%)": st.column_config.NumberColumn(
                "Score",
                help="Pertinence de la fiche",
                format="%d %%",
            ),
            "Tokens": st.column_config.NumberColumn(
                "Tokens",
                help="Estimation du volume de contexte",
                format="%d",
            ),
            "Résumé": st.column_config.TextColumn(
                "Résumé",
                help="Extrait de la fiche Notion",
                width="large",
            ),
            "Mots-clés": st.column_config.TextColumn(
                "Mots-clés",
                help="Mots détectés dans la fiche",
            ),
        },
        disabled=["Titre", "Score (%)", "Domaine", "Tokens", "Résumé", "Mots-clés"],
        key="context_suggestions_editor",
    )

    for page_id, row in edited_df.iterrows():
        page = page_lookup.get(page_id)
        if not page:
            continue
        _toggle_selection(page, bool(row.get("Sélection", False)))


def _render_manual_selection(previews_by_domain: Dict[str, List[NotionPagePreview]]) -> None:
    st.subheader("🗂️ Sélection manuelle")

    all_pages: List[NotionPagePreview] = []
    for domain, pages in previews_by_domain.items():
        all_pages.extend(pages)

    if not all_pages:
        st.caption("Aucune fiche disponible pour le moment.")
        return

    domain_options = sorted({page.domain for page in all_pages})
    col_domain, col_search, col_tokens = st.columns([2, 3, 2])

    with col_domain:
        selected_domains = st.multiselect(
            "Domaines",
            options=domain_options,
            default=domain_options,
            key="context_manual_domains",
            format_func=lambda value: value.capitalize(),
        )

    with col_search:
        search = st.text_input(
            "Recherche",
            key="context_manual_search",
            placeholder="Nom, résumé ou mot-clé",
        )

    token_values = [page.token_estimate for page in all_pages if page.token_estimate]
    min_tokens = min(token_values) if token_values else 0
    max_tokens = max(token_values) if token_values else 0

    with col_tokens:
        if min_tokens == max_tokens:
            token_range = (min_tokens, max_tokens)
            st.caption(f"Tokens : ~{max_tokens}")
        else:
            step = max(50, (max_tokens - min_tokens) // 10 or 1)
            token_range = st.slider(
                "Plage de tokens",
                min_value=min_tokens,
                max_value=max_tokens,
                value=(min_tokens, max_tokens),
                step=step,
                key="context_manual_token_range",
            )

    search_lower = search.lower().strip() if search else ""
    selection = st.session_state.context_selection
    selected_ids = selection["selected_ids"]

    filtered_pages: List[NotionPagePreview] = []
    for page in all_pages:
        if selected_domains and page.domain not in selected_domains:
            continue
        if search_lower:
            haystack = f"{page.title} {page.summary or ''}".lower()
            if search_lower not in haystack:
                continue
        if token_range and (page.token_estimate < token_range[0] or page.token_estimate > token_range[1]):
            continue
        filtered_pages.append(page)

    pinned_pages = [page for page in all_pages if page.id in selected_ids]
    for page in pinned_pages:
        if page not in filtered_pages:
            filtered_pages.append(page)

    if not filtered_pages:
        st.info("Aucune fiche ne correspond aux filtres sélectionnés.")
        return

    table_rows = []
    for page in filtered_pages:
        table_rows.append(
            {
                "ID": page.id,
                "Sélection": page.id in selected_ids,
                "Titre": page.title,
                "Domaine": page.domain.capitalize(),
                "Tokens": page.token_estimate,
                "Résumé": page.summary or "—",
            }
        )

    manual_df = pd.DataFrame(table_rows).set_index("ID")

    edited_df = st.data_editor(
        manual_df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Sélection": st.column_config.CheckboxColumn(
                "Sélection",
                help="Cocher pour ajouter la fiche au contexte",
            ),
            "Tokens": st.column_config.NumberColumn(
                "Tokens",
                help="Estimation du coût",
                format="%d",
            ),
            "Résumé": st.column_config.TextColumn(
                "Résumé",
                help="Aperçu de la fiche",
                width="large",
            ),
        },
        disabled=["Titre", "Domaine", "Tokens", "Résumé"],
        key="context_manual_editor",
    )

    for page_id, row in edited_df.iterrows():
        page = next((p for p in filtered_pages if p.id == page_id), None)
        if not page:
            continue
        _toggle_selection(page, bool(row.get("Sélection", False)))


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

    _ensure_selector_styles()

    st.markdown(
        f"<div class='context-total'>Total contexte <span class='context-total__badge'>~{total_tokens} tokens</span></div>",
        unsafe_allow_html=True,
    )

    if not ordered_previews:
        st.caption("Aucune fiche sélectionnée pour le moment.")
        return {
            "selected_ids": selected_ids,
            "previews": [],
            "token_estimate": 0,
        }

    columns_count = 3 if len(ordered_previews) >= 3 else len(ordered_previews)
    summaries_container = st.container()

    for row_start in range(0, len(ordered_previews), columns_count):
        cols = summaries_container.columns(columns_count)
        for col, preview in zip(cols, ordered_previews[row_start : row_start + columns_count]):
            domain_color = DOMAIN_COLORS.get(preview.domain, "#f3f4f6")
            summary_text = preview.summary or "—"
            if len(summary_text) > 160:
                summary_text = summary_text[:157] + "…"
            with col:
                col.markdown(
                    """
                    <div class="context-chip">
                        <div class="context-chip__header">
                            <span class="context-chip__title">{title}</span>
                            <span class="context-chip__badge" style="background: {bg};">{domain}</span>
                        </div>
                        <div class="context-chip__meta">~{tokens} tokens</div>
                        <div class="context-chip__summary">{summary}</div>
                    </div>
                    """.format(
                        title=escape(preview.title),
                        bg=domain_color,
                        domain=escape(preview.domain.capitalize()),
                        tokens=preview.token_estimate,
                        summary=escape(summary_text),
                    ),
                    unsafe_allow_html=True,
                )
                if st.button(
                    "Retirer",
                    key=f"remove_{preview.id}",
                    help="Retirer cette fiche du contexte",
                ):
                    _toggle_selection(preview, False)
                    st.experimental_rerun()

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

