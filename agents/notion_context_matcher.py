
"""Fuzzy matching helpers to suggest Notion context pages."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Dict, Iterable, List, Optional, Sequence

from agents.notion_context_fetcher import (
    NotionContextFetcher,
    NotionPageContent,
    NotionPagePreview,
)

STOP_WORDS = {
    "le",
    "la",
    "les",
    "des",
    "un",
    "une",
    "du",
    "de",
    "et",
    "a",
    "au",
    "aux",
    "en",
    "sur",
    "dans",
    "pour",
    "avec",
    "par",
    "que",
    "qui",
    "quoi",
    "comme",
    "dont",
    "ou",
}


@dataclass
class MatchCandidate:
    """Intermediate scoring information for a Notion page."""

    page: NotionPagePreview
    score: float
    matched_keywords: List[str]


@dataclass
class MatchSuggestion(MatchCandidate):
    """Final suggestion enriched with auto-selection flag."""

    auto_select: bool


class NotionContextMatcher:
    """Suggest context pages based on a free-form brief."""

    def __init__(self, fetcher: Optional[NotionContextFetcher] = None) -> None:
        self.fetcher = fetcher or NotionContextFetcher()

    # ------------------------------------------------------------------
    # Keyword extraction
    # ------------------------------------------------------------------

    @staticmethod
    def extract_keywords(brief: str, max_keywords: int = 25) -> List[str]:
        """Extract meaningful keywords from a brief."""

        tokens = re.findall(r"[\w'-]+", brief.lower())
        filtered = []
        for token in tokens:
            normalized = _strip_accents(token)
            if normalized in STOP_WORDS or len(normalized) <= 2:
                continue
            filtered.append(normalized)

        # Preserve order of appearance while removing duplicates
        seen: Dict[str, None] = {}
        keywords: List[str] = []
        for token in filtered:
            if token not in seen:
                seen[token] = None
                keywords.append(token)
            if len(keywords) >= max_keywords:
                break
        return keywords

    # ------------------------------------------------------------------
    # Scoring helpers
    # ------------------------------------------------------------------

    @staticmethod
    def fuzzy_match_pages(keywords: Sequence[str], pages: Iterable[NotionPagePreview]) -> List[MatchCandidate]:
        """Score every page according to keyword overlap and fuzzy ratio."""

        joined_keywords = " ".join(keywords)
        candidates: List[MatchCandidate] = []
        for page in pages:
            haystack = _normalise_text(f"{page.title} {page.summary} {' '.join(page.tags)}")
            matches = [kw for kw in keywords if kw in haystack]
            keyword_ratio = len(matches) / len(keywords) if keywords else 0.0

            title_ratio = SequenceMatcher(None, joined_keywords, _normalise_text(page.title)).ratio() if joined_keywords else 0.0
            summary_ratio = SequenceMatcher(None, joined_keywords, _normalise_text(page.summary)).ratio() if joined_keywords else 0.0

            score = 0.5 * max(title_ratio, summary_ratio) + 0.5 * keyword_ratio
            candidates.append(MatchCandidate(page=page, score=score, matched_keywords=matches))
        return candidates

    @staticmethod
    def score_relevance(brief: str, page_content: str) -> float:
        """Fine grained score using the full content of the page."""

        if not brief or not page_content:
            return 0.0
        brief_norm = _normalise_text(brief)
        content_norm = _normalise_text(page_content)
        # Use sequence ratio and scaled coverage of keywords within content
        ratio = SequenceMatcher(None, brief_norm, content_norm).ratio()
        # Estimate coverage using shared unique tokens
        brief_tokens = set(brief_norm.split())
        content_tokens = set(content_norm.split())
        overlap = len(brief_tokens & content_tokens)
        coverage = overlap / len(brief_tokens) if brief_tokens else 0.0
        return max(ratio, coverage * 0.8 + ratio * 0.2)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def suggest_context(
        self,
        brief: str,
        max_fiches: int = 5,
        min_score: float = 0.5,
        auto_select_threshold: float = 0.7,
        domains: Optional[Sequence[str]] = None,
    ) -> List[MatchSuggestion]:
        """Return the most relevant context pages for a given brief."""

        keywords = self.extract_keywords(brief)
        brief_norm = _normalise_text(brief)
        available_pages = self._load_available_pages(domains)
        rough_candidates = self.fuzzy_match_pages(keywords, available_pages)

        suggestions: List[MatchSuggestion] = []
        for candidate in rough_candidates:
            refined_score = candidate.score
            try:
                page_payload = self.fetcher.fetch_page_full(candidate.page.id, domain=candidate.page.domain)
            except Exception:  # pragma: no cover - integration fallback
                page_payload = None
            if isinstance(page_payload, NotionPageContent):
                refined_score = max(refined_score, self.score_relevance(brief, page_payload.content))
            if refined_score < min_score:
                continue

            title_hit = _normalise_text(candidate.page.title) in brief_norm if brief_norm else False
            auto_select = refined_score >= auto_select_threshold or title_hit

            suggestions.append(
                MatchSuggestion(
                    page=candidate.page,
                    score=min(refined_score, 1.0),
                    matched_keywords=candidate.matched_keywords,
                    auto_select=auto_select,
                )
            )

        suggestions.sort(key=lambda item: item.score, reverse=True)
        return suggestions[:max_fiches]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_available_pages(self, domains: Optional[Sequence[str]]) -> List[NotionPagePreview]:
        data = self.fetcher.fetch_all_databases()
        previews: List[NotionPagePreview] = []
        for domain, pages in data.items():
            if domains and domain not in domains:
                continue
            previews.extend(pages)
        return previews


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _normalise_text(value: str) -> str:
    value = _strip_accents(value.lower())
    value = re.sub(r"[^\w\s]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


__all__ = [
    "NotionContextMatcher",
    "MatchSuggestion",
    "MatchCandidate",
]
