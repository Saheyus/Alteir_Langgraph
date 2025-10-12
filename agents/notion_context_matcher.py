
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
        """Score pages using token overlaps to avoid spurious substring hits.

        - Exact token matches only (no substring like 'age' in 'personnage')
        - Weighted by overlap with title/summary tokens
        """

        keyword_tokens = list(keywords)
        keyword_set = set(keyword_tokens)
        candidates: List[MatchCandidate] = []
        for page in pages:
            title_norm = _normalise_text(page.title)
            summary_norm = _normalise_text(page.summary)
            tags_norm = _normalise_text(" ".join(page.tags))

            haystack_tokens = set((title_norm + " " + summary_norm + " " + tags_norm).split())
            matches = [kw for kw in keyword_tokens if kw in haystack_tokens]
            keyword_ratio = len(matches) / len(keyword_tokens) if keyword_tokens else 0.0

            title_tokens = set(title_norm.split())
            summary_tokens = set(summary_norm.split())
            title_overlap = len(title_tokens & keyword_set) / len(keyword_set) if keyword_set else 0.0
            summary_overlap = len(summary_tokens & keyword_set) / len(keyword_set) if keyword_set else 0.0

            score = 0.6 * max(title_overlap, summary_overlap) + 0.4 * keyword_ratio
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
        use_full_content: bool = False,
        available_pages: Optional[Sequence[NotionPagePreview]] = None,
    ) -> List[MatchSuggestion]:
        """Return the most relevant context pages for a given brief."""

        keywords = self.extract_keywords(brief)
        brief_norm = _normalise_text(brief)
        brief_tokens_set = set(brief_norm.split()) if brief_norm else set()
        if available_pages is None:
            available_pages = self._load_available_pages(domains)
        else:
            # Optionally filter by domains if provided
            if domains:
                available_pages = [p for p in available_pages if p.domain in domains]
        rough_candidates = self.fuzzy_match_pages(keywords, available_pages)

        # Decide scoring thresholds. When avoiding full-content fetches,
        # relax the minimum score a bit to avoid filtering out relevant
        # metadata-only matches.
        effective_min_score = min_score if use_full_content else min(min_score, 0.3)

        # Refine with full-content scoring only for the top candidates if
        # explicitly requested. By default we operate on previews only to keep
        # the UI extremely responsive.
        TOP_K_REFINE = max(10, max_fiches * 5) if use_full_content else 0
        rough_candidates.sort(key=lambda c: c.score, reverse=True)
        refine_pool = rough_candidates[:TOP_K_REFINE]

        suggestions: List[MatchSuggestion] = []
        added_ids: Dict[str, None] = {}

        # Always include candidates whose title appears (even partially) in the brief,
        # with a strong boost. This guarantees pages like "Léviathan Pétrifié" show up
        # when the brief contains "Léviathan".
        if brief_norm:
            for candidate in rough_candidates:
                page_title_norm = _normalise_text(candidate.page.title)
                if page_title_norm:
                    title_tokens = [t for t in page_title_norm.split() if t not in STOP_WORDS and len(t) >= 4]
                    if not title_tokens:
                        continue
                    tokens_in_brief = set(title_tokens) & brief_tokens_set
                    if not tokens_in_brief:
                        continue
                    # Full phrase mention → max score
                    if page_title_norm in brief_norm:
                        boosted_score = 1.0
                        auto = True
                    else:
                        # Partial mention → moderated boost (avoid 100% for a single token like "mecanique")
                        m = len(tokens_in_brief)
                        boosted_score = min(0.9, max(0.6 + 0.1 * min(m, 3), 0.0))
                        auto = m >= 2
                    if candidate.page.id not in added_ids:
                        suggestions.append(
                            MatchSuggestion(
                                page=candidate.page,
                                score=boosted_score,
                                matched_keywords=candidate.matched_keywords,
                                auto_select=auto,
                            )
                        )
                        added_ids[candidate.page.id] = None
                        if len(suggestions) >= max_fiches:
                            break
        if TOP_K_REFINE > 0 and len(suggestions) < max_fiches:
            for candidate in refine_pool:
                if candidate.page.id in added_ids:
                    continue
                refined_score = candidate.score
                try:
                    page_payload = self.fetcher.fetch_page_full(candidate.page.id, domain=candidate.page.domain)
                except Exception:  # pragma: no cover - integration fallback
                    page_payload = None
                if isinstance(page_payload, NotionPageContent):
                    refined_score = max(refined_score, self.score_relevance(brief, page_payload.content))
                if refined_score < effective_min_score:
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
                added_ids[candidate.page.id] = None
                if len(suggestions) >= max_fiches:
                    break

        # Always include the top-N candidates (metadata-only) regardless of thresholds
        # to guarantee non-empty, high-coverage suggestions.
        for candidate in rough_candidates:
            if len(suggestions) >= max_fiches:
                break
            if candidate.page.id in added_ids:
                continue
            title_hit = _normalise_text(candidate.page.title) in brief_norm if brief_norm else False
            auto_select = candidate.score >= auto_select_threshold or title_hit
            suggestions.append(
                MatchSuggestion(
                    page=candidate.page,
                    score=min(candidate.score, 1.0),
                    matched_keywords=candidate.matched_keywords,
                    auto_select=auto_select,
                )
            )
            added_ids[candidate.page.id] = None

        # Then append any additional candidates above the threshold (positions 6+)
        for candidate in rough_candidates:
            if candidate.page.id in added_ids:
                continue
            if candidate.score < effective_min_score:
                continue
            title_hit = _normalise_text(candidate.page.title) in brief_norm if brief_norm else False
            auto_select = candidate.score >= auto_select_threshold or title_hit
            suggestions.append(
                MatchSuggestion(
                    page=candidate.page,
                    score=min(candidate.score, 1.0),
                    matched_keywords=candidate.matched_keywords,
                    auto_select=auto_select,
                )
            )
            added_ids[candidate.page.id] = None

        suggestions.sort(key=lambda item: item.score, reverse=True)
        return suggestions

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
