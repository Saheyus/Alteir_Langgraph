
"""Utilities to retrieve and format Notion context for the agents."""

from __future__ import annotations

import logging
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
        "personnages": "2806e4d21b458012a744d8d6723c8be1",
        "lieux": "2806e4d21b4580969f1cd7463a4c889c",
        "communautes": None,
        "especes": None,
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
            from config.notion_config import NotionConfig
            
            if not NotionConfig.validate_token():
                LOGGER.warning("No valid Notion token found.")
                return None
            
            class DirectNotionClient(NotionClientProtocol):
                """Direct Notion API client as fallback."""
                
                def __init__(self):
                    self.headers = NotionConfig.get_headers()
                    self.base_url = "https://api.notion.com/v1"
                
                def list_pages(self, database_id: str) -> Sequence[Dict[str, Any]]:
                    """Query database for all pages."""
                    url = f"{self.base_url}/databases/{database_id}/query"
                    response = requests.post(url, headers=self.headers, json={})
                    response.raise_for_status()
                    return response.json().get("results", [])
                
                def retrieve_page(self, page_id: str) -> Dict[str, Any]:
                    """Retrieve a single page."""
                    url = f"{self.base_url}/pages/{page_id}"
                    response = requests.get(url, headers=self.headers)
                    response.raise_for_status()
                    return response.json()
                
                def retrieve_page_content(self, page_id: str) -> str:
                    """Retrieve page content blocks."""
                    url = f"{self.base_url}/blocks/{page_id}/children"
                    response = requests.get(url, headers=self.headers)
                    response.raise_for_status()
                    blocks = response.json().get("results", [])
                    
                    # Convert blocks to markdown-like text
                    content_parts = []
                    for block in blocks:
                        block_type = block.get("type")
                        if block_type == "paragraph":
                            text = self._extract_rich_text(block.get("paragraph", {}).get("rich_text", []))
                            if text:
                                content_parts.append(text)
                        elif block_type == "heading_1":
                            text = self._extract_rich_text(block.get("heading_1", {}).get("rich_text", []))
                            if text:
                                content_parts.append(f"# {text}")
                        elif block_type == "heading_2":
                            text = self._extract_rich_text(block.get("heading_2", {}).get("rich_text", []))
                            if text:
                                content_parts.append(f"## {text}")
                        elif block_type == "heading_3":
                            text = self._extract_rich_text(block.get("heading_3", {}).get("rich_text", []))
                            if text:
                                content_parts.append(f"### {text}")
                        elif block_type == "bulleted_list_item":
                            text = self._extract_rich_text(block.get("bulleted_list_item", {}).get("rich_text", []))
                            if text:
                                content_parts.append(f"- {text}")
                        elif block_type == "numbered_list_item":
                            text = self._extract_rich_text(block.get("numbered_list_item", {}).get("rich_text", []))
                            if text:
                                content_parts.append(f"1. {text}")
                    
                    return "\n".join(content_parts)
                
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

    def fetch_all_databases(self, force_refresh: bool = False) -> Dict[str, List[NotionPagePreview]]:
        """Return previews grouped by domain using sandbox databases only."""

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
            previews = [self._record_to_preview(record, domain) for record in records]
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
        preview = self._record_to_preview(record, detected_domain)
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

    def _record_to_preview(self, record: Dict[str, Any], domain: str) -> NotionPagePreview:
        """Convert a Notion API record to a preview object."""
        properties = record.get("properties", {})
        
        # Extract title from Notion title property
        title = self._extract_notion_title(properties)
        
        # Extract summary from rich_text properties (Alias, Description, etc.)
        summary = self._extract_notion_summary(properties)
        
        # Extract tags from multi_select properties
        tags = self._extract_notion_tags(properties)
        
        # Estimate tokens based on summary + reasonable page estimate
        summary_tokens = self._estimate_tokens(summary)
        
        # Estimate based on domain and number of properties
        base_estimate = 800  # Base estimate for a typical Notion page
        property_count = len([p for p in properties.values() if self._has_content(p)])
        property_bonus = property_count * 30  # ~30 tokens per filled property
        
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
        """Extract title from Notion properties (Nom, Name, or first title property)."""
        # Try common title property names
        for prop_name in ["Nom", "Name", "Titre", "Title"]:
            if prop_name in properties:
                prop = properties[prop_name]
                if prop.get("type") == "title" and prop.get("title"):
                    title_array = prop["title"]
                    if title_array and len(title_array) > 0:
                        return title_array[0].get("plain_text", "Sans titre")
        
        # Fallback: find any title property
        for prop_name, prop in properties.items():
            if prop.get("type") == "title" and prop.get("title"):
                title_array = prop["title"]
                if title_array and len(title_array) > 0:
                    return title_array[0].get("plain_text", "Sans titre")
        
        return "Sans titre"
    
    @staticmethod
    def _extract_notion_summary(properties: Dict[str, Any]) -> str:
        """Extract summary from rich_text properties (Alias, Description, etc.)."""
        # Try common summary properties
        for prop_name in ["Alias", "Description", "Résumé", "Summary"]:
            if prop_name in properties:
                prop = properties[prop_name]
                if prop.get("type") == "rich_text" and prop.get("rich_text"):
                    text_array = prop["rich_text"]
                    if text_array and len(text_array) > 0:
                        return text_array[0].get("plain_text", "")
        
        return ""
    
    @staticmethod
    def _extract_notion_tags(properties: Dict[str, Any]) -> List[str]:
        """Extract tags from multi_select properties."""
        tags = []
        
        # Collect from all multi_select properties
        for prop_name, prop in properties.items():
            if prop.get("type") == "multi_select" and prop.get("multi_select"):
                for item in prop["multi_select"]:
                    tag_name = item.get("name")
                    if tag_name:
                        tags.append(tag_name)
        
        # Also include select properties (single select)
        for prop_name in ["Type", "État", "Status", "Catégorie"]:
            if prop_name in properties:
                prop = properties[prop_name]
                if prop.get("type") == "select" and prop.get("select"):
                    tag_name = prop["select"].get("name")
                    if tag_name:
                        tags.append(tag_name)
        
        return tags

    @staticmethod
    def _has_content(prop: Dict[str, Any]) -> bool:
        """Check if a property has actual content."""
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


__all__ = [
    "NotionContextFetcher",
    "NotionClientProtocol",
    "NotionClientUnavailable",
    "NotionPagePreview",
    "NotionPageContent",
]
