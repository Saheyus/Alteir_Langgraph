
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
            # Use list for Streamlit state stability across reruns
            "selected_ids": [],
            "previews": {},
            "suggestions": [],
        }

    # Ensure mutable structures exist
    selection = st.session_state.context_selection
    selection.setdefault("selected_ids", [])
    selection.setdefault("previews", {})
    selection.setdefault("suggestions", [])

    # Index of checkbox keys -> lightweight page info for just-in-time commit
    if "_context_checkbox_index" not in st.session_state:
        st.session_state._context_checkbox_index = {}

    # Normalize storage to list for persistence
    if isinstance(selection["selected_ids"], set):
        selection["selected_ids"] = list(selection["selected_ids"])


def _toggle_selection(page: NotionPagePreview, checked: bool) -> None:
    selection = st.session_state.context_selection
    current: list = selection["selected_ids"]
    selected_ids = set(current)
    if checked:
        selected_ids.add(page.id)
        selection["previews"][page.id] = page
    else:
        selected_ids.discard(page.id)
    selection["selected_ids"] = list(selected_ids)


def _render_suggestions(brief: str, domain_key: str, matcher: NotionContextMatcher, previews_by_domain: Dict[str, List[NotionPagePreview]]) -> None:
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
                    # Ultra-rapide: suggestions basées uniquement sur les titres/métadonnées
                    # Réutilise les aperçus déjà préchargés au lancement (aucun refetch)
                    available = [p for d in targets for p in previews_by_domain.get(d, [])]
                    suggestions = matcher.suggest_context(
                        brief,
                        domains=targets,
                        use_full_content=False,
                        available_pages=available,
                    )
                selection["suggestions"] = suggestions
                # Commit immediate auto-selected suggestions to the persistent selection
                # so that a user can cliquer "Générer" sans retoucher les cases.
                selected_set = set(selection.get("selected_ids", []))
                for s in suggestions:
                    if isinstance(s, MatchSuggestion) and s.auto_select:
                        selected_set.add(s.page.id)
                        selection["previews"][s.page.id] = s.page
                selection["selected_ids"] = list(selected_set)
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
        checked = (page.id in set(selection["selected_ids"])) or suggestion.auto_select
        checkbox_key = f"suggestion_{page.id}"
        checkbox = st.checkbox(
            f"{page.title} — {int(suggestion.score * 100)}%",
            value=checked,
            key=checkbox_key,
            help=page.summary or "",
        )
        # Record mapping for force-commit later
        try:
            st.session_state._context_checkbox_index[checkbox_key] = {
                "id": page.id,
                "title": page.title,
                "domain": page.domain,
                "summary": page.summary,
                # Fixed coarse estimate per fiche
                "token_estimate": 3000,
                "last_edited": page.last_edited,
                "tags": getattr(page, "tags", []) or [],
            }
        except Exception:
            pass
        _toggle_selection(page, checkbox)

        with st.expander(f"Détails · {page.domain.capitalize()} · ~3000 tokens", expanded=False):
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
                checkbox_key = f"manual_{domain}_{page.id}"
                checkbox = st.checkbox(
                    f"{page.title} · ~3000 tokens",
                    value=checked,
                    key=checkbox_key,
                    help=page.summary or "Sans aperçu",
                )
                # Record mapping for force-commit later
                try:
                    st.session_state._context_checkbox_index[checkbox_key] = {
                        "id": page.id,
                        "title": page.title,
                        "domain": page.domain,
                        "summary": page.summary,
                        # Fixed coarse estimate per fiche
                        "token_estimate": 3000,
                        "last_edited": page.last_edited,
                        "tags": getattr(page, "tags", []) or [],
                    }
                except Exception:
                    pass
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
        # Fixed coarse estimate per fiche
        total_tokens += 3000

    for preview in ordered_previews:
        col_label, col_remove = st.columns([6, 1])
        with col_label:
            st.markdown(f"**{preview.title}** · {preview.domain.capitalize()} · ~3000 tokens")
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

    # Récupération des fiches (utilise le cache interne du fetcher)
    progress_bar = st.progress(10)
    status_text = st.empty()
    try:
        status_text.text("🔄 Préchargement des fiches depuis le bac à sable…")
        previews_by_domain = fetcher.fetch_all_databases(force_refresh=False, lightweight=True)
        total_pages = sum(len(pages) for pages in previews_by_domain.values())
        progress_bar.progress(100)
        status_text.text("")
        st.info(f"✓ {total_pages} fiche(s) préchargée(s) pour la sélection")
    except NotionClientUnavailable:
        status_text.text("")
        progress_bar.progress(0)
        previews_by_domain = {d: [] for d in CONTEXT_DOMAINS}
        st.warning("Connexion Notion indisponible (mode hors ligne)")
    except HTTPError as e:
        status_text.text("")
        progress_bar.progress(0)
        previews_by_domain = {d: [] for d in CONTEXT_DOMAINS}
        st.error(f"❌ Erreur API Notion: {e}")
    except Exception as e:  # pragma: no cover - robustesse UI
        status_text.text("")
        progress_bar.progress(0)
        previews_by_domain = {d: [] for d in CONTEXT_DOMAINS}
        st.error(f"❌ Erreur lors de la récupération des fiches: {e}")

    _render_suggestions(brief, domain_key, matcher, previews_by_domain)
    _render_manual_selection(previews_by_domain)
    summary = _render_selected_summary(fetcher)

    return summary


def force_commit_selection() -> Dict[str, Any]:
    """Recompute selection from current checkbox states and return a summary.

    This ensures that a click on "Générer" cannot miss the latest UI state
    due to Streamlit rerun timing.
    """
    _init_session_state()
    selection = st.session_state.context_selection
    index: Dict[str, Dict[str, Any]] = st.session_state.get("_context_checkbox_index", {})

    # Rebuild selected_ids from checkbox values
    selected_ids_set = set()
    for key, page_info in index.items():
        try:
            if bool(st.session_state.get(key)):
                pid = page_info.get("id")
                if pid:
                    selected_ids_set.add(pid)
                    # Ensure preview is available for this id
                    if pid not in selection["previews"]:
                        selection["previews"][pid] = NotionPagePreview(
                            id=page_info.get("id", ""),
                            title=page_info.get("title", "Sans titre"),
                            domain=page_info.get("domain", "inconnu"),
                            summary=page_info.get("summary", ""),
                            tags=page_info.get("tags", []) or [],
                            last_edited=page_info.get("last_edited"),
                            token_estimate=int(page_info.get("token_estimate", 0)),
                        )
        except Exception:
            continue

    # Persist back to session selection
    selection["selected_ids"] = list(selected_ids_set)

    # Build ordered previews list following the current order in selection
    previews_cache: Dict[str, NotionPagePreview] = selection["previews"]
    ordered_previews: List[NotionPagePreview] = []
    total_tokens = 0
    for pid in selection["selected_ids"]:
        pv = previews_cache.get(pid)
        if pv is not None:
            ordered_previews.append(pv)
            total_tokens += int(getattr(pv, "token_estimate", 0) or 0)

    return {
        "selected_ids": list(selection["selected_ids"]),
        "previews": [asdict(p) for p in ordered_previews],
        "token_estimate": total_tokens,
    }

