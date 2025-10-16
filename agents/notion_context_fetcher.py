
"""Utilities to retrieve and format Notion context for the agents."""

from __future__ import annotations

import logging
import os
import time
import math
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Protocol, Sequence

from config.context_cache import context_cache

LOGGER = logging.getLogger(__name__)


class NotionClientProtocol(Protocol):
    """Protocol describing the minimal Notion client behaviour."""

    def list_pages(self, database_id: str) -> Sequence[Dict[str, Any]]:  # pragma: no cover - protocol
        """Return lightweight records for every page inside a database."""

    def retrieve_page(self, page_id: str) -> Dict[str, Any]:  # pragma: no cover - protocol
        """Return full metadata for a page."""

    def retrieve_page_content(self, page_id: str) -> str:  # pragma: no cover - protocol
        """Return the rich text content for a page."""


@dataclass
class NotionPagePreview:
    """Minimal data shown in the selector UI."""

    id: str
    title: str
    domain: str
    summary: str
    tags: List[str]
    last_edited: Optional[str]
    token_estimate: int


@dataclass
class NotionPageContent(NotionPagePreview):
    """Full data injected in the prompt."""

    content: str
    properties: Dict[str, Any]


class NotionClientUnavailable(RuntimeError):
    """Raised when the Notion client cannot be instantiated."""


class NotionContextFetcher:
    """Fetch and format Notion pages used as LLM context."""

    SANDBOX_DATABASES: Dict[str, Optional[str]] = {
        # Écriture autorisée uniquement sur Personnages (1) et Lieux (1)
        "personnages": "2806e4d21b458012a744d8d6723c8be1",
        "lieux": "2806e4d21b4580969f1cd7463a4c889c",
        # Bases principales: lecture seule → ne pas les lister dans le bac à sable
        "communautes": "28d6e4d21b4581c88f48c7aaed8a2803",
        "especes": "28d6e4d21b4581f4864ac2a5a65f9221",
        "objets": None,
    }

    def __init__(self, client: Optional[NotionClientProtocol] = None) -> None:
        self.client = client or self._build_default_client()

    def _build_default_client(self) -> Optional[NotionClientProtocol]:
        """Try constructing a MCP-backed client, return None if impossible."""

        try:  # pragma: no cover - exercised only in integration
            # Test if we can import the MCP module that contains the tools
            import inspect
            # In Cursor, MCP tools are injected globally but not as importable modules
            # We need to check if they exist in the current execution context
            frame = inspect.currentframe()
            if frame and hasattr(frame, 'f_globals'):
                # Check if MCP tools are available in globals
                if 'mcp_notionMCP_notion_fetch' not in dir() and 'mcp_notionMCP_notion_fetch' not in frame.f_globals:
                    # Try importing from a local MCP client wrapper
                    try:
                        from agents.notion_mcp_client import get_mcp_client
                        return get_mcp_client()
                    except ImportError:
                        pass  # Continue to fallback instead of returning None
            
            # If we get here, we need to create the client differently
            LOGGER.info("MCP tools not directly accessible; trying fallback client with direct API calls.")
            return self._build_fallback_client()
            
        except Exception as e:  # pragma: no cover - handled gracefully in tests
            LOGGER.warning(f"Error initializing MCP client: {e}. Trying fallback client.")
            return self._build_fallback_client()

    def _build_fallback_client(self) -> Optional[NotionClientProtocol]:
        """Build a fallback client using direct Notion API calls."""
        try:
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            from config.notion_config import NotionConfig
            
            if not NotionConfig.validate_token():
                LOGGER.warning("No valid Notion token found.")
                return None
            
            class DirectNotionClient(NotionClientProtocol):
                """Direct Notion API client as fallback."""
                
                def __init__(self):
                    # Utiliser la version stable directe pour éviter erreurs 400
                    self.headers = NotionConfig.get_direct_headers()
                    self.base_url = "https://api.notion.com/v1"
                    # HTTP session with retries for robustness (handles 429/5xx)
                    self.session = requests.Session()
                    retry = Retry(
                        total=3,
                        connect=3,
                        read=3,
                        backoff_factor=0.8,
                        status_forcelist=(429, 500, 502, 503, 504),
                        allowed_methods=("GET", "POST", "PATCH"),
                        raise_on_status=False,
                    )
                    adapter = HTTPAdapter(max_retries=retry)
                    self.session.mount("http://", adapter)
                    self.session.mount("https://", adapter)
                    # Timeouts and caps
                    self.request_timeout = float(os.getenv("NOTION_REQUEST_TIMEOUT", "20"))
                    self.max_records = int(os.getenv("NOTION_MAX_RECORDS", "200"))
                    self.page_size = int(os.getenv("NOTION_PAGE_SIZE", "50"))
                    LOGGER.info(
                        "DirectNotionClient initialised | timeout=%ss max_records=%s page_size=%s",
                        self.request_timeout,
                        self.max_records,
                        self.page_size,
                    )
                
                def _request(self, method: str, url: str, **kwargs):
                    kwargs.setdefault("headers", self.headers)
                    kwargs.setdefault("timeout", self.request_timeout)
                    return self.session.request(method, url, **kwargs)
                
                def list_pages(self, database_id: str) -> Sequence[Dict[str, Any]]:
                    """Query database for all pages."""
                    url = f"{self.base_url}/databases/{database_id}/query"
                    results: List[Dict[str, Any]] = []
                    has_more = True
                    start_cursor = None
                    pages_fetched = 0
                    LOGGER.info("[Notion] list_pages start | db=%s", database_id)
                    while has_more and len(results) < self.max_records:
                        payload: Dict[str, Any] = {"page_size": self.page_size}
                        if start_cursor:
                            payload["start_cursor"] = start_cursor
                        response = self._request("POST", url, json=payload)
                        response.raise_for_status()
                        data = response.json()
                        batch = data.get("results", [])
                        results.extend(batch)
                        has_more = bool(data.get("has_more"))
                        start_cursor = data.get("next_cursor")
                        pages_fetched += 1
                        LOGGER.debug(
                            "[Notion] list_pages batch | db=%s size=%s total=%s has_more=%s",
                            database_id,
                            len(batch),
                            len(results),
                            has_more,
                        )
                        # Soft rate-limit guard
                        time.sleep(0.2)
                        if pages_fetched >= 10:  # safety cap on batches
                            LOGGER.warning(
                                "[Notion] list_pages reached batch cap (10) | db=%s total=%s",
                                database_id,
                                len(results),
                            )
                            break
                    if len(results) > self.max_records:
                        results = results[: self.max_records]
                    LOGGER.info(
                        "[Notion] list_pages done | db=%s total=%s batches=%s",
                        database_id,
                        len(results),
                        pages_fetched,
                    )
                    return results
                
                def retrieve_page(self, page_id: str) -> Dict[str, Any]:
                    """Retrieve a single page."""
                    url = f"{self.base_url}/pages/{page_id}"
                    response = self._request("GET", url)
                    response.raise_for_status()
                    return response.json()
                
                def retrieve_page_content(self, page_id: str) -> str:
                    """Retrieve page content blocks recursively."""
                    def fetch_blocks_recursive(block_id: str, indent: int = 0) -> List[str]:
                        """Fetch blocks and their children recursively."""
                        url = f"{self.base_url}/blocks/{block_id}/children"
                        try:
                            response = self._request("GET", url)
                            response.raise_for_status()
                            blocks = response.json().get("results", [])
                        except Exception as e:
                            # 404 or transient errors are expected on some legacy blocks; keep silent in normal runs
                            LOGGER.debug(f"Failed to fetch children for block {block_id}: {e}")
                            return []
                        
                        content_parts = []
                        indent_str = "  " * indent  # Indentation for nested content
                        
                        for block in blocks:
                            block_type = block.get("type")
                            block_id = block.get("id")
                            has_children = block.get("has_children", False)
                            
                            # Extract text based on block type
                            if block_type == "paragraph":
                                text = self._extract_rich_text(block.get("paragraph", {}).get("rich_text", []))
                                if text:
                                    content_parts.append(f"{indent_str}{text}")
                            elif block_type == "heading_1":
                                text = self._extract_rich_text(block.get("heading_1", {}).get("rich_text", []))
                                if text:
                                    content_parts.append(f"{indent_str}# {text}")
                            elif block_type == "heading_2":
                                text = self._extract_rich_text(block.get("heading_2", {}).get("rich_text", []))
                                if text:
                                    content_parts.append(f"{indent_str}## {text}")
                            elif block_type == "heading_3":
                                text = self._extract_rich_text(block.get("heading_3", {}).get("rich_text", []))
                                if text:
                                    content_parts.append(f"{indent_str}### {text}")
                            elif block_type == "bulleted_list_item":
                                text = self._extract_rich_text(block.get("bulleted_list_item", {}).get("rich_text", []))
                                if text:
                                    content_parts.append(f"{indent_str}- {text}")
                            elif block_type == "numbered_list_item":
                                text = self._extract_rich_text(block.get("numbered_list_item", {}).get("rich_text", []))
                                if text:
                                    content_parts.append(f"{indent_str}1. {text}")
                            elif block_type == "quote":
                                text = self._extract_rich_text(block.get("quote", {}).get("rich_text", []))
                                if text:
                                    content_parts.append(f"{indent_str}> {text}")
                            elif block_type == "callout":
                                text = self._extract_rich_text(block.get("callout", {}).get("rich_text", []))
                                if text:
                                    content_parts.append(f"{indent_str}💡 {text}")
                            elif block_type == "toggle":
                                text = self._extract_rich_text(block.get("toggle", {}).get("rich_text", []))
                                if text:
                                    content_parts.append(f"{indent_str}▶ {text}")
                            
                            # Recursively fetch children if present
                            if has_children and block_id:
                                children = fetch_blocks_recursive(block_id, indent + 1)
                                content_parts.extend(children)
                        
                        return content_parts
                    
                    # Start fetching from the page root
                    all_content = fetch_blocks_recursive(page_id)
                    return "\n".join(all_content)
                
                @staticmethod
                def _extract_rich_text(rich_text_array: List[Dict[str, Any]]) -> str:
                    """Extract plain text from Notion rich text array."""
                    return "".join(rt.get("plain_text", "") for rt in rich_text_array)
            
            return DirectNotionClient()
            
        except ImportError:
            LOGGER.warning("requests library not available; cannot use fallback client.")
            return None
        except Exception as e:
            LOGGER.warning(f"Error building fallback client: {e}")
            return None

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def fetch_all_databases(self, force_refresh: bool = False, lightweight: bool = True) -> Dict[str, List[NotionPagePreview]]:
        """Return previews grouped by domain using sandbox databases only.

        Args:
            force_refresh: Ignore cache and refetch.
            lightweight: When True, avoid any content retrieval; only use properties
                (title, light summary from properties) and compute a coarse token estimate.
        """

        previews_by_domain: Dict[str, List[NotionPagePreview]] = {}
        for domain, database_id in self.SANDBOX_DATABASES.items():
            if not database_id:
                LOGGER.debug("No sandbox database configured for domain '%s'", domain)
                previews_by_domain[domain] = []
                continue

            cache_key = f"{domain}:{database_id}"
            if not force_refresh:
                cached = context_cache.get("list", cache_key)
                if cached is not None:
                    previews_by_domain[domain] = cached
                    continue

            records = self._list_database_pages(database_id)
            previews = [self._record_to_preview(record, domain, eager_content=not lightweight) for record in records]
            previews_by_domain[domain] = previews
            context_cache.set("list", cache_key, previews)

        return previews_by_domain

    def fetch_page_preview(self, page_id: str, domain: Optional[str] = None, force_refresh: bool = False) -> NotionPagePreview:
        """Return a cached or freshly retrieved preview for a page."""

        if not force_refresh:
            cached = context_cache.get("preview", page_id)
            if cached is not None:
                return cached

        record = self._retrieve_page(page_id)
        detected_domain = domain or record.get("domain") or "inconnu"
        # Use eager mode for single-page preview to allow content-based summary
        preview = self._record_to_preview(record, detected_domain, eager_content=True)
        context_cache.set("preview", page_id, preview)
        return preview

    def fetch_page_full(self, page_id: str, domain: Optional[str] = None, force_refresh: bool = False) -> NotionPageContent:
        """Return the full payload (metadata + markdown) for a page."""

        if not force_refresh:
            cached = context_cache.get("full", page_id)
            if cached is not None:
                return cached

        record = self._retrieve_page(page_id)
        detected_domain = domain or record.get("domain") or "inconnu"
        preview = self._record_to_preview(record, detected_domain)
        content = self._retrieve_content(page_id, record)
        payload = NotionPageContent(
            **preview.__dict__,
            content=content,
            properties=record.get("properties", {}),
        )
        context_cache.set("full", page_id, payload)
        return payload

    def format_context_for_llm(self, pages: Iterable[NotionPageContent], compact: bool = True) -> str:
        """Create a deterministic prompt fragment from selected pages."""

        sections: List[str] = []
        for page in pages:
            header = f"### {page.title} ({page.domain})"
            body = page.content.strip()
            if compact:
                body = self._keep_first_blocks(body, max_tokens=4000)
            sections.append(f"{header}\n{body}\n")
        return "\n".join(sections).strip()
    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _assert_client(self) -> None:
        if self.client is None:
            raise NotionClientUnavailable(
                "No MCP Notion client available. Provide a client when instantiating NotionContextFetcher."
            )

    def _list_database_pages(self, database_id: str) -> Sequence[Dict[str, Any]]:
        self._assert_client()
        return self.client.list_pages(self._normalise_id(database_id))

    def _retrieve_page(self, page_id: str) -> Dict[str, Any]:
        self._assert_client()
        return self.client.retrieve_page(self._normalise_id(page_id))

    def _retrieve_content(self, page_id: str, record: Optional[Dict[str, Any]] = None) -> str:
        if record and record.get("content"):
            return record["content"]
        self._assert_client()
        return self.client.retrieve_page_content(self._normalise_id(page_id))

    @staticmethod
    def _normalise_id(raw_id: str) -> str:
        if "-" in raw_id or len(raw_id) != 32:
            return raw_id
        return f"{raw_id[:8]}-{raw_id[8:12]}-{raw_id[12:16]}-{raw_id[16:20]}-{raw_id[20:]}"

    def _record_to_preview(self, record: Dict[str, Any], domain: str, *, eager_content: bool = False) -> NotionPagePreview:
        """Convert a Notion API record to a preview object.

        Supports both real Notion API shape (properties nested with types)
        and simplified test/fixture shapes where fields are present at top-level
        (e.g. ``title``, ``summary``, ``tags``) or property values are strings.
        """
        properties = record.get("properties", {})

        # Extract title with graceful fallbacks
        title = self._extract_notion_title(properties)
        if not title:
            # Fallback to top-level record field commonly used in tests
            title = record.get("title", "Sans titre")

        # Extract summary with graceful fallbacks
        summary = self._extract_notion_summary(properties)
        if not summary:
            summary = record.get("summary", "")
        
        # Si eager_content est demandé et summary vide, tenter un aperçu depuis le contenu
        content: str = record.get("content", "")
        if eager_content and not summary:
            page_id = record.get("id", "")
            if page_id:
                try:
                    content = self._retrieve_content(page_id, record)
                    if content:
                        summary = self._extract_first_words(content, max_chars=150)
                except Exception as e:
                    LOGGER.debug(f"Could not fetch content for preview summary: {e}")
        # If still empty summary, attempt a content-based summary only when eager
        if eager_content and not summary:
            try:
                page_id = record.get("id", "")
                if page_id:
                    content = content or self._retrieve_content(page_id, record)
                if content:
                    summary = self._extract_first_words(content, max_chars=150)
            except Exception:
                pass
        
        # Extract tags from properties with fallback to top-level list
        tags = self._extract_notion_tags(properties)
        if not tags:
            tags = list(record.get("tags", []))
        
        # Estimation tokens
        token_estimate: int
        if eager_content:
            if not content:
                try:
                    page_id = record.get("id", "")
                    if page_id:
                        content = self._retrieve_content(page_id, record)
                except Exception:
                    content = ""
            token_estimate = self._estimate_tokens(content) if content else 0
        else:
            # Lightweight: estimation approximative basée sur propriétés uniquement
            summary_tokens = self._estimate_tokens(summary)
            base_estimate = 300  # léger pour lister rapidement
            property_count = len([p for p in properties.values() if self._has_content(p)])
            property_bonus = property_count * 15
            token_estimate = max(summary_tokens, base_estimate + property_bonus)

        return NotionPagePreview(
            id=record.get("id", ""),
            title=title,
            domain=domain,
            summary=summary,
            tags=tags,
            last_edited=record.get("last_edited_time"),
            token_estimate=token_estimate,
        )
    
    @staticmethod
    def _extract_notion_title(properties: Dict[str, Any]) -> str:
        """Extract title from Notion properties or return empty string if unavailable.

        Handles both full Notion property objects and simplified string values.
        """
        if not isinstance(properties, dict):
            return ""

        # Try common title property names (full Notion shape)
        for prop_name in ["Nom", "Name", "Titre", "Title"]:
            if prop_name in properties:
                prop = properties[prop_name]
                # Simplified shape: direct string
                if isinstance(prop, str):
                    return prop
                # Notion shape
                if isinstance(prop, dict) and prop.get("type") == "title" and prop.get("title"):
                    title_array = prop["title"]
                    if title_array and len(title_array) > 0:
                        return title_array[0].get("plain_text", "Sans titre")

        # Fallback: find any title property
        for prop_name, prop in properties.items():
            if isinstance(prop, dict) and prop.get("type") == "title" and prop.get("title"):
                title_array = prop["title"]
                if title_array and len(title_array) > 0:
                    return title_array[0].get("plain_text", "Sans titre")

        return ""
    
    @staticmethod
    def _extract_notion_summary(properties: Dict[str, Any]) -> str:
        """Extract summary from rich_text properties with support for simplified shapes."""
        if not isinstance(properties, dict):
            return ""

        for prop_name in ["Alias", "Description", "Résumé", "Summary"]:
            if prop_name in properties:
                prop = properties[prop_name]
                # Simplified: direct string
                if isinstance(prop, str):
                    return prop
                # Notion rich_text
                if isinstance(prop, dict) and prop.get("type") == "rich_text" and prop.get("rich_text"):
                    text_array = prop["rich_text"]
                    if text_array and len(text_array) > 0:
                        return text_array[0].get("plain_text", "")

        return ""
    
    @staticmethod
    def _extract_notion_tags(properties: Dict[str, Any]) -> List[str]:
        """Extract tags from properties (multi_select/select) or simplified strings."""
        tags: List[str] = []

        if not isinstance(properties, dict):
            return tags

        # Collect from all multi_select properties
        for prop_name, prop in properties.items():
            if isinstance(prop, dict) and prop.get("type") == "multi_select" and prop.get("multi_select"):
                for item in prop["multi_select"]:
                    tag_name = item.get("name")
                    if tag_name:
                        tags.append(tag_name)

        # Also include select properties (single select)
        for prop_name in ["Type", "État", "Status", "Catégorie"]:
            if prop_name in properties:
                prop = properties[prop_name]
                # Simplified: direct string treated as tag
                if isinstance(prop, str):
                    tags.append(prop)
                elif isinstance(prop, dict) and prop.get("type") == "select" and prop.get("select"):
                    tag_name = prop["select"].get("name")
                    if tag_name:
                        tags.append(tag_name)

        return tags

    @staticmethod
    def _has_content(prop: Dict[str, Any]) -> bool:
        """Check if a property has actual content."""
        # Support simplified shapes used in tests
        if isinstance(prop, str):
            return bool(prop.strip())
        if isinstance(prop, (list, tuple)):
            return len(prop) > 0
        if not isinstance(prop, dict):
            return prop is not None

        prop_type = prop.get("type")
        if prop_type in ["title", "rich_text"]:
            content = prop.get(prop_type, [])
            return bool(content)
        elif prop_type in ["select", "status"]:
            return bool(prop.get(prop_type))
        elif prop_type in ["multi_select", "relation"]:
            content = prop.get(prop_type, [])
            return bool(content)
        elif prop_type == "number":
            return prop.get("number") is not None
        return False
    
    @staticmethod
    def _estimate_tokens(text: str) -> int:
        if not text:
            return 0
        word_count = max(1, len(text.split()))
        return int(math.ceil(word_count * 1.3))

    @staticmethod
    def _keep_first_blocks(text: str, max_tokens: int) -> str:
        if not text:
            return ""
        words = text.split()
        if len(words) <= max_tokens:
            return text
        slice_size = max_tokens
        return " ".join(words[:slice_size]) + " ..."
    
    @staticmethod
    def _extract_first_words(text: str, max_chars: int = 150) -> str:
        """Extrait les premiers mots du contenu pour créer un aperçu."""
        if not text:
            return ""
        
        # Nettoyer le texte (enlever les markdowns headers)
        lines = text.split("\n")
        clean_lines = []
        
        for line in lines:
            # Ignorer les lignes vides et les headers markdown
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                # Enlever les symboles markdown courants au début
                for prefix in ["- ", "* ", "> ", "1. ", "💡 ", "▶ "]:
                    if stripped.startswith(prefix):
                        stripped = stripped[len(prefix):]
                        break
                if stripped:
                    clean_lines.append(stripped)
        
        # Joindre et tronquer
        full_text = " ".join(clean_lines)
        if len(full_text) <= max_chars:
            return full_text
        
        # Tronquer proprement au dernier espace avant max_chars
        truncated = full_text[:max_chars]
        last_space = truncated.rfind(" ")
        if last_space > max_chars * 0.8:  # Si on a au moins 80% du texte
            truncated = truncated[:last_space]
        
        return truncated + "..."


__all__ = [
    "NotionContextFetcher",
    "NotionClientProtocol",
    "NotionClientUnavailable",
    "NotionPagePreview",
    "NotionPageContent",
]
