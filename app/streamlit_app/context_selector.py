
"""Streamlit component allowing users to curate Notion context."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional
from requests.exceptions import HTTPError

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
                with st.spinner("Génération des suggestions..."):
                    suggestions = matcher.suggest_context(brief, domains=targets)
                selection["suggestions"] = suggestions
                st.info(f"✓ {len(suggestions)} suggestion(s) trouvée(s)")
            except NotionClientUnavailable:
                st.warning("Connexion Notion indisponible : suggestions automatiques désactivées.")
            except HTTPError as e:
                st.error(f"❌ Erreur API Notion pendant la suggestion: {e}")
            except Exception as e:  # pragma: no cover - UI feedback
                st.error(f"❌ Erreur inattendue pendant la suggestion: {e}")
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

            # Dynamic search simple (filtrage côté Python)
            search = st.text_input(
                "Recherche",
                key=f"context_search_{domain}",
                placeholder="Nom ou mot-clé",
            )
            def _match(p: NotionPagePreview, q: str) -> bool:
                if not q:
                    return True
                ql = q.lower()
                return (ql in (p.title or '').lower()) or (ql in (p.summary or '').lower())

            filtered = [page for page in pages if _match(page, search)]

            for page in filtered[:80]:
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
            except HTTPError as e:
                st.caption(f"⚠️ Erreur API sur l'aperçu {page_id}: {e}")
                continue
            except Exception:
                # On ignore silencieusement pour ne pas bloquer le rendu
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

    # Récupération des fiches avec feedback visuel et progression
    progress_bar = st.progress(0)
    status_text = st.empty()
    previews_by_domain: Dict[str, List[NotionPagePreview]] = {d: [] for d in CONTEXT_DOMAINS}

    try:
        # Déterminer les domaines effectivement configurés (avec database sandbox)
        try:
            sandbox_map = getattr(fetcher, "SANDBOX_DATABASES", {})
        except Exception:
            sandbox_map = {}

        targets = [(d, sandbox_map.get(d)) for d in CONTEXT_DOMAINS]
        targets = [(d, dbid) for d, dbid in targets if dbid]
        total = max(1, len(targets))

        for idx, (d, dbid) in enumerate(targets, start=1):
            status_text.text(f"🔄 Récupération: {d.capitalize()} ({idx}/{total})")
            try:
                records = fetcher._list_database_pages(dbid)  # type: ignore[attr-defined]
                # Mode léger: ne pas récupérer le contenu, juste propriétés/titres
                previews = [fetcher._record_to_preview(rec, d, eager_content=False) for rec in records]  # type: ignore[attr-defined]
                previews_by_domain[d] = previews
                # Avancement intra-domaine retiré pour éviter plusieurs barres concurrentes
            except NotionClientUnavailable:
                st.warning("Connexion Notion indisponible (mode hors ligne)")
                previews_by_domain[d] = []
            except HTTPError as e:
                st.error(f"❌ Erreur API Notion sur {d}: {e}")
                previews_by_domain[d] = []
            except Exception as e:  # pragma: no cover - robustesse UI
                st.error(f"❌ Erreur inattendue sur {d}: {e}")
                previews_by_domain[d] = []

            pct = int(idx * 100 / total)
            progress_bar.progress(min(100, pct))

        total_pages = sum(len(pages) for pages in previews_by_domain.values())
        status_text.text("")
        progress_bar.progress(100)
        st.info(f"✓ {total_pages} fiche(s) préchargée(s) pour la sélection")
    except Exception as e:  # pragma: no cover - garde-fou global
        status_text.text("")
        progress_bar.progress(0)
        st.error(f"❌ Erreur lors de la récupération des fiches: {e}")

    _render_suggestions(brief, domain_key, matcher)
    _render_manual_selection(previews_by_domain)
    summary = _render_selected_summary(fetcher)

    return summary

