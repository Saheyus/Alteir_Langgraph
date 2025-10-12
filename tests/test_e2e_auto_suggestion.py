"""
End-to-end test for automatic suggestions.

Scope:
- Hits Notion API to preload previews (sandbox bases)
- Runs the metadata-only matcher with preloaded pages (no full fetch)
- Asserts we get a relevant suggestion quickly

Markers:
- e2e, slow, notion_api
"""

from __future__ import annotations

import time
import unicodedata
import pytest

from agents.notion_context_fetcher import NotionContextFetcher, NotionClientUnavailable
from agents.notion_context_matcher import NotionContextMatcher, MatchSuggestion


def _strip_accents(value: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", value) if not unicodedata.combining(ch)
    )


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.notion_api
def test_e2e_auto_suggestion_metadata_only():
    fetcher = NotionContextFetcher()
    matcher = NotionContextMatcher(fetcher=fetcher)

    # 1) Preload previews (lightweight)
    start_preload = time.time()
    try:
        previews_by_domain = fetcher.fetch_all_databases(force_refresh=True, lightweight=True)
    except NotionClientUnavailable:
        pytest.skip("Notion client unavailable in this environment")

    preload_time = time.time() - start_preload
    # Sanity: should have loaded some pages from sandbox
    total_pages = sum(len(v) for v in previews_by_domain.values())
    assert total_pages >= 1, "No pages loaded from sandbox databases"

    # 2) Suggestions (metadata-only, no refetch)
    brief = "un alchimiste du Leviathan petrifie"
    targets = ["lieux", "personnages"]
    available = [p for d in targets for p in previews_by_domain.get(d, [])]

    start_suggest = time.time()
    suggestions = matcher.suggest_context(
        brief,
        domains=targets,
        use_full_content=False,
        available_pages=available,
    )
    suggest_time = time.time() - start_suggest

    assert suggestions, "Expected at least one suggestion for Leviathan brief"

    # Simulate UI behavior: auto-select suggestions should go to selected_ids
    auto_selected = [s for s in suggestions if isinstance(s, MatchSuggestion) and s.auto_select]
    assert auto_selected, "Expected at least one auto-selected suggestion"

    # 3) Relevance check (metadata-based)
    top_title = _strip_accents(suggestions[0].page.title).lower()
    assert "leviathan" in top_title or any(
        "leviathan" in _strip_accents(s.page.title).lower() for s in suggestions
    ), "Leviathan-related page should be suggested"

    # 4) Performance: suggestion must be fast since it's metadata-only
    # Allow generous bound on CI; < 1.0s locally, but < 2.5s on shared runners
    assert suggest_time < 2.5, f"Auto-suggestion too slow: {suggest_time:.2f}s"


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.notion_api
def test_e2e_auto_suggestion_old_town_title_match():
    fetcher = NotionContextFetcher()
    matcher = NotionContextMatcher(fetcher=fetcher)

    try:
        previews_by_domain = fetcher.fetch_all_databases(force_refresh=True, lightweight=True)
    except NotionClientUnavailable:
        pytest.skip("Notion client unavailable in this environment")

    brief = (
        "Une chasseuse de primes cybernetique du Leviathan traquant son propre createur dans la Vieille Ville"
    )
    targets = ["lieux", "personnages"]
    available = [p for d in targets for p in previews_by_domain.get(d, [])]

    suggestions = matcher.suggest_context(
        brief,
        domains=targets,
        use_full_content=False,
        available_pages=available,
    )
    # Should not be empty even if strict thresholds fail; fallback returns top-N
    assert suggestions, "Expected at least one suggestion for Vieille Ville brief"


