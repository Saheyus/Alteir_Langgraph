
"""Unit tests for the Notion context selection backend."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

import pytest

from agents.notion_context_fetcher import (
    NotionContextFetcher,
    NotionPageContent,
    NotionPagePreview,
)
from agents.notion_context_matcher import NotionContextMatcher
from config.context_cache import ContextCache, context_cache


@pytest.fixture(autouse=True)
def clear_global_cache():
    """Ensure the shared cache is clean before and after each test."""

    context_cache.clear()
    yield
    context_cache.clear()


def test_context_cache_expiration_and_invalidation():
    cache = ContextCache()
    cache.set("list", "foo", 42, ttl=0)
    assert cache.get("list", "foo") is None

    cache.set("preview", "bar", "value")
    assert cache.get("preview", "bar") == "value"
    cache.invalidate("preview", "bar")
    assert cache.get("preview", "bar") is None

    cache.set("full", "baz", {"a": 1})
    cache.invalidate("full")
    assert cache.get("full", "baz") is None


@dataclass
class FakeRecord:
    id: str
    title: str
    summary: str
    tags: Sequence[str]
    content: str
    last_edited_time: str
    properties: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "tags": list(self.tags),
            "content": self.content,
            "last_edited_time": self.last_edited_time,
            "properties": self.properties,
        }


class FakeNotionClient:
    def __init__(self, mapping: Dict[str, List[FakeRecord]]):
        self.mapping = mapping
        self.page_lookup = {
            record.id: record for records in mapping.values() for record in records
        }
        self.list_calls: List[str] = []
        self.page_calls: List[str] = []

    def list_pages(self, database_id: str) -> Sequence[Dict[str, Any]]:
        self.list_calls.append(database_id)
        return [record.as_dict() for record in self.mapping.get(database_id, [])]

    def retrieve_page(self, page_id: str) -> Dict[str, Any]:
        self.page_calls.append(page_id)
        return self.page_lookup[page_id].as_dict()

    def retrieve_page_content(self, page_id: str) -> str:
        return self.page_lookup[page_id].content


@pytest.fixture
def fake_fetcher() -> NotionContextFetcher:
    personnages_db = "2806e4d21b458012a744d8d6723c8be1"
    lieux_db = "2806e4d21b4580969f1cd7463a4c889c"

    def _normalise(raw: str) -> str:
        if "-" in raw:
            return raw
        return f"{raw[:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:]}"

    records = {
        _normalise(personnages_db): [
            FakeRecord(
                id="page-character-1",
                title="Lysandre Vervent",
                summary="Cartographe visionnaire passionnee par les cartes vivantes",
                tags=["personnage", "cartographie"],
                content="""Nom: Lysandre Vervent
Domaine: Cartographes
Mot-cle: leviathan petrifie
""",
                last_edited_time="2025-10-02T18:53:49Z",
                properties={"Type": "PNJ secondaire"},
            ),
            FakeRecord(
                id="page-character-2",
                title="Jast, l'Ineluctable",
                summary="Dirigeante implacable des strates profondes",
                tags=["personnage", "tyran"],
                content="""Nom: Jast
Force: controle total sur les flux emotionnels
""",
                last_edited_time="2025-10-01T12:00:00Z",
                properties={"Type": "Entite superieure"},
            ),
        ],
        _normalise(lieux_db): [
            FakeRecord(
                id="page-location-1",
                title="Le Leviathan Petrifie",
                summary="Vestige mineral respirant encore les marees",
                tags=["lieu", "mystique"],
                content="""Nom: Le Leviathan Petrifie
Usage: sanctuaire
""",
                last_edited_time="2025-10-02T07:20:00Z",
                properties={"Type": "Zone"},
            ),
        ],
    }

    client = FakeNotionClient(records)
    fetcher = NotionContextFetcher(client=client)
    return fetcher


def test_fetch_all_databases_uses_cache(fake_fetcher: NotionContextFetcher):
    client = fake_fetcher.client  # type: ignore[attr-defined]
    assert client.list_calls == []

    data_first = fake_fetcher.fetch_all_databases()
    assert "personnages" in data_first
    assert len(data_first["personnages"]) == 2

    data_second = fake_fetcher.fetch_all_databases()
    assert data_second == data_first
    assert len(client.list_calls) == 2  # personnages + lieux once


def test_fetch_page_preview_and_full(fake_fetcher: NotionContextFetcher):
    preview = fake_fetcher.fetch_page_preview("page-character-1", domain="personnages")
    assert isinstance(preview, NotionPagePreview)
    assert preview.title == "Lysandre Vervent"

    full = fake_fetcher.fetch_page_full("page-character-1", domain="personnages")
    assert isinstance(full, NotionPageContent)
    assert "Nom: Lysandre" in full.content
    assert full.token_estimate > 0

    client = fake_fetcher.client  # type: ignore[attr-defined]
    initial_calls = list(client.page_calls)
    _ = fake_fetcher.fetch_page_full("page-character-1", domain="personnages")
    assert client.page_calls == initial_calls


def test_format_context_for_llm_compact(fake_fetcher: NotionContextFetcher):
    page = fake_fetcher.fetch_page_full("page-location-1", domain="lieux")
    formatted = fake_fetcher.format_context_for_llm([page], compact=True)
    assert formatted.startswith("### Le Leviathan Petrifie")
    assert "Nom: Le Leviathan" in formatted


def test_matcher_keyword_extraction_handles_accents():
    keywords = NotionContextMatcher.extract_keywords("A la recherche du Leviathan petrifie et des cartes vivantes")
    assert "leviathan" in keywords
    assert "petrifie" in keywords
    assert "des" not in keywords


def test_matcher_suggest_context_prioritises_scores(fake_fetcher: NotionContextFetcher):
    matcher = NotionContextMatcher(fetcher=fake_fetcher)
    brief = "Explorer le Leviathan petrifie avec le soutien des cartographes"
    suggestions = matcher.suggest_context(brief, max_fiches=3)

    assert suggestions, "Expected at least one suggestion"
    titles = [suggestion.page.title for suggestion in suggestions]
    assert titles[0] == "Le Leviathan Petrifie"
    assert any(s.auto_select for s in suggestions)


def test_matcher_always_includes_topN_and_appends_above_threshold(fake_fetcher: NotionContextFetcher):
    matcher = NotionContextMatcher(fetcher=fake_fetcher)
    # Force domains to include both personnages and lieux
    brief = "Titre qui ne matche rien explicitement"
    suggestions = matcher.suggest_context(brief, max_fiches=2, domains=["personnages", "lieux"], use_full_content=False)
    # Should include at least 2 candidates regardless of thresholds
    assert len(suggestions) >= 2
    # And order should start with the highest-scored ones (rough order)
    scores = [s.score for s in suggestions[:2]]
    assert scores[0] >= scores[1]


def test_build_context_payload(monkeypatch):
    import sys
    import types

    def _identity_decorator(*args, **kwargs):
        def _wrap(func):
            return func
        if args and callable(args[0]) and len(args) == 1 and not kwargs:
            return args[0]
        return _wrap

    dummy_streamlit = types.SimpleNamespace(
        warning=lambda *args, **kwargs: None,
        session_state={},
        cache_resource=_identity_decorator,
        cache_data=_identity_decorator,
    )
    monkeypatch.setitem(sys.modules, "streamlit", dummy_streamlit)

    from app.streamlit_app import generation

    class DummyPage:
        def __init__(self, pid: str, domain: str):
            self.id = pid
            self.title = f'Title {pid}'
            self.domain = domain
            self.summary = 'Summary'
            self.content = 'Full content'
            self.properties = {'Type': 'Test'}
            self.token_estimate = 123
            self.last_edited = '2025-10-02T00:00:00Z'

    class DummyFetcher:
        def __init__(self):
            self.calls = []

        def fetch_page_full(self, page_id: str, domain: str = None):
            self.calls.append((page_id, domain))
            return DummyPage(page_id, domain or 'unknown')

        def format_context_for_llm(self, pages):
            return '\n'.join(page.title for page in pages)

    dummy = DummyFetcher()
    monkeypatch.setattr(generation, 'NotionContextFetcher', lambda: dummy)

    summary = {
        'selected_ids': ['page-1'],
        'previews': [{'id': 'page-1', 'domain': 'personnages'}],
    }

    payload = generation._build_context_payload(summary)

    assert payload is not None
    assert payload['formatted'] == 'Title page-1'
    assert payload['pages'][0]['domain'] == 'personnages'
    assert dummy.calls == [('page-1', 'personnages')]

