"""Tests unitaires pour la récupération récursive du contenu Notion.

Ce module teste la capacité du NotionContextFetcher à récupérer
le contenu complet des pages Notion, y compris les blocs enfants
(toggles, sections repliables, etc.).
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence
from unittest.mock import Mock, patch

import pytest

from agents.notion_context_fetcher import (
    NotionContextFetcher,
    NotionPageContent,
)
from config.context_cache import context_cache


@pytest.fixture(autouse=True)
def clear_global_cache():
    """Ensure the shared cache is clean before and after each test."""
    context_cache.clear()
    yield
    context_cache.clear()


class FakeNotionClientWithChildren:
    """Client Notion factice qui simule des blocs avec enfants."""

    def __init__(self, blocks_structure: Dict[str, List[Dict[str, Any]]]):
        """
        Initialise le client avec une structure de blocs.
        
        Args:
            blocks_structure: Dict mapping block_id -> list of child blocks
        """
        self.blocks_structure = blocks_structure
        self.retrieve_calls: List[str] = []

    def list_pages(self, database_id: str) -> Sequence[Dict[str, Any]]:
        """Liste les pages d'une base."""
        return []

    def retrieve_page(self, page_id: str) -> Dict[str, Any]:
        """Récupère les métadonnées d'une page."""
        self.retrieve_calls.append(page_id)
        return {
            "id": page_id,
            "properties": {
                "Nom": {
                    "type": "title",
                    "title": [{"plain_text": "Test Page", "type": "text"}],
                },
            },
            "last_edited_time": "2025-10-04T16:00:00Z",
        }

    def retrieve_page_content(self, page_id: str) -> str:
        """Cette méthode ne devrait pas être appelée car on teste le fallback client."""
        raise NotImplementedError("This method should not be called in these tests")


@pytest.fixture
def simple_nested_structure() -> Dict[str, List[Dict[str, Any]]]:
    """
    Structure simple avec un heading contenant un toggle avec des paragraphes.
    
    Page Root
    └── Heading 1: "Section principale"
        └── Toggle: "Détails cachés"
            ├── Paragraph: "Contenu du toggle ligne 1"
            └── Paragraph: "Contenu du toggle ligne 2"
    """
    return {
        "page-root": [
            {
                "type": "heading_1",
                "id": "block-heading-1",
                "has_children": True,
                "heading_1": {
                    "rich_text": [{"plain_text": "Section principale"}],
                },
            }
        ],
        "block-heading-1": [
            {
                "type": "toggle",
                "id": "block-toggle-1",
                "has_children": True,
                "toggle": {
                    "rich_text": [{"plain_text": "Détails cachés"}],
                },
            }
        ],
        "block-toggle-1": [
            {
                "type": "paragraph",
                "id": "block-para-1",
                "has_children": False,
                "paragraph": {
                    "rich_text": [{"plain_text": "Contenu du toggle ligne 1"}],
                },
            },
            {
                "type": "paragraph",
                "id": "block-para-2",
                "has_children": False,
                "paragraph": {
                    "rich_text": [{"plain_text": "Contenu du toggle ligne 2"}],
                },
            },
        ],
    }


@pytest.fixture
def complex_nested_structure() -> Dict[str, List[Dict[str, Any]]]:
    """
    Structure complexe avec plusieurs niveaux d'imbrication.
    
    Page Root
    ├── Heading 1: "Identité & Vue d'ensemble"
    │   ├── Paragraph: "Description générale"
    │   └── Heading 2: "Sous-section"
    │       └── Bulleted list: "Item 1"
    └── Heading 1: "Géographie & Environnement"
        └── Callout: "Note importante"
            └── Paragraph: "Détail de la note"
    """
    return {
        "page-root": [
            {
                "type": "heading_1",
                "id": "block-h1-1",
                "has_children": True,
                "heading_1": {"rich_text": [{"plain_text": "Identité & Vue d'ensemble"}]},
            },
            {
                "type": "heading_1",
                "id": "block-h1-2",
                "has_children": True,
                "heading_1": {"rich_text": [{"plain_text": "Géographie & Environnement"}]},
            },
        ],
        "block-h1-1": [
            {
                "type": "paragraph",
                "id": "block-para-1",
                "has_children": False,
                "paragraph": {"rich_text": [{"plain_text": "Description générale"}]},
            },
            {
                "type": "heading_2",
                "id": "block-h2-1",
                "has_children": True,
                "heading_2": {"rich_text": [{"plain_text": "Sous-section"}]},
            },
        ],
        "block-h2-1": [
            {
                "type": "bulleted_list_item",
                "id": "block-bullet-1",
                "has_children": False,
                "bulleted_list_item": {"rich_text": [{"plain_text": "Item 1"}]},
            },
        ],
        "block-h1-2": [
            {
                "type": "callout",
                "id": "block-callout-1",
                "has_children": True,
                "callout": {"rich_text": [{"plain_text": "Note importante"}]},
            },
        ],
        "block-callout-1": [
            {
                "type": "paragraph",
                "id": "block-para-2",
                "has_children": False,
                "paragraph": {"rich_text": [{"plain_text": "Détail de la note"}]},
            },
        ],
    }


@pytest.fixture
def empty_page_structure() -> Dict[str, List[Dict[str, Any]]]:
    """Structure vide (page sans contenu)."""
    return {"page-root": []}


@pytest.fixture
def only_headings_structure() -> Dict[str, List[Dict[str, Any]]]:
    """Structure avec seulement des headings vides (comme avant le fix)."""
    return {
        "page-root": [
            {
                "type": "heading_1",
                "id": "block-h1-1",
                "has_children": False,
                "heading_1": {"rich_text": [{"plain_text": "Identité & Vue d'ensemble"}]},
            },
            {
                "type": "heading_1",
                "id": "block-h1-2",
                "has_children": False,
                "heading_1": {"rich_text": [{"plain_text": "Géographie & Environnement"}]},
            },
        ],
    }


def create_mock_client(blocks_structure: Dict[str, List[Dict[str, Any]]]):
    """Crée un client mocké qui retourne la structure de blocs donnée."""
    
    class MockClient:
        """Client mocké avec support de la récupération récursive."""
        
        def list_pages(self, database_id: str) -> Sequence[Dict[str, Any]]:
            return []
        
        def retrieve_page(self, page_id: str) -> Dict[str, Any]:
            return {
                "id": page_id,
                "properties": {
                    "Nom": {
                        "type": "title",
                        "title": [{"plain_text": "Test Page", "type": "text"}],
                    },
                },
                "last_edited_time": "2025-10-04T16:00:00Z",
            }
        
        def retrieve_page_content(self, page_id: str) -> str:
            """Récupère le contenu récursif de la page."""
            def fetch_blocks_recursive(block_id: str, indent: int = 0) -> List[str]:
                """Fetch blocks and their children recursively."""
                blocks = blocks_structure.get(block_id, [])
                content_parts = []
                indent_str = "  " * indent
                
                for block in blocks:
                    block_type = block.get("type")
                    block_id_child = block.get("id")
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
                    if has_children and block_id_child:
                        children = fetch_blocks_recursive(block_id_child, indent + 1)
                        content_parts.extend(children)
                
                return content_parts
            
            all_content = fetch_blocks_recursive(page_id)
            return "\n".join(all_content)
        
        @staticmethod
        def _extract_rich_text(rich_text_array: List[Dict[str, Any]]) -> str:
            """Extract plain text from Notion rich text array."""
            return "".join(rt.get("plain_text", "") for rt in rich_text_array)
    
    return MockClient()


def test_recursive_fetch_simple_nested(simple_nested_structure):
    """Test la récupération récursive d'une structure simple imbriquée."""
    # Créer un fetcher avec un client mocké
    mock_client = create_mock_client(simple_nested_structure)
    fetcher = NotionContextFetcher(client=mock_client)
    
    # Récupérer le contenu de la page
    content = fetcher.fetch_page_full("page-root", domain="test")
    
    # Vérifications
    assert isinstance(content, NotionPageContent)
    assert "Section principale" in content.content
    assert "Détails cachés" in content.content
    assert "Contenu du toggle ligne 1" in content.content
    assert "Contenu du toggle ligne 2" in content.content
    
    # Vérifier que le contenu est bien structuré avec indentation
    lines = content.content.split("\n")
    assert any("# Section principale" in line for line in lines)
    assert any("▶ Détails cachés" in line for line in lines)


def test_recursive_fetch_complex_nested(complex_nested_structure):
    """Test la récupération récursive d'une structure complexe."""
    mock_client = create_mock_client(complex_nested_structure)
    fetcher = NotionContextFetcher(client=mock_client)
    
    content = fetcher.fetch_page_full("page-root", domain="test")
    
    # Vérifier tous les niveaux
    assert "Identité & Vue d'ensemble" in content.content
    assert "Description générale" in content.content
    assert "Sous-section" in content.content
    assert "Item 1" in content.content
    assert "Géographie & Environnement" in content.content
    assert "Note importante" in content.content
    assert "Détail de la note" in content.content


def test_recursive_fetch_empty_page(empty_page_structure):
    """Test la récupération d'une page vide."""
    mock_client = create_mock_client(empty_page_structure)
    fetcher = NotionContextFetcher(client=mock_client)
    
    content = fetcher.fetch_page_full("page-root", domain="test")
    
    # Une page vide devrait retourner un contenu vide
    assert content.content == ""


def test_recursive_fetch_only_headings(only_headings_structure):
    """Test la récupération d'une page avec seulement des headings (cas problématique initial)."""
    mock_client = create_mock_client(only_headings_structure)
    fetcher = NotionContextFetcher(client=mock_client)
    
    content = fetcher.fetch_page_full("page-root", domain="test")
    
    # Devrait contenir les headings mais être court (comme avant le fix)
    assert "Identité & Vue d'ensemble" in content.content
    assert "Géographie & Environnement" in content.content
    assert len(content.content) < 200  # Court car pas de contenu


def test_recursive_fetch_handles_errors():
    """Test la gestion des erreurs lors de la récupération récursive."""
    structure = {
        "page-root": [
            {
                "type": "heading_1",
                "id": "block-good",
                "has_children": False,
                "heading_1": {"rich_text": [{"plain_text": "Section OK"}]},
            },
            {
                "type": "heading_1",
                "id": "block-error",
                "has_children": True,
                "heading_1": {"rich_text": [{"plain_text": "Section avec erreur"}]},
            },
        ],
        # block-error n'a pas d'enfants dans la structure, simulant une erreur
    }
    
    mock_client = create_mock_client(structure)
    fetcher = NotionContextFetcher(client=mock_client)
    
    content = fetcher.fetch_page_full("page-root", domain="test")
    
    # Devrait contenir les deux sections (même si block-error n'a pas d'enfants)
    assert "Section OK" in content.content
    assert "Section avec erreur" in content.content


def test_block_types_formatting():
    """Test le formatage des différents types de blocs."""
    structure = {
        "page-root": [
            {
                "type": "paragraph",
                "id": "b1",
                "has_children": False,
                "paragraph": {"rich_text": [{"plain_text": "Un paragraphe"}]},
            },
            {
                "type": "heading_1",
                "id": "b2",
                "has_children": False,
                "heading_1": {"rich_text": [{"plain_text": "Titre niveau 1"}]},
            },
            {
                "type": "heading_2",
                "id": "b3",
                "has_children": False,
                "heading_2": {"rich_text": [{"plain_text": "Titre niveau 2"}]},
            },
            {
                "type": "heading_3",
                "id": "b4",
                "has_children": False,
                "heading_3": {"rich_text": [{"plain_text": "Titre niveau 3"}]},
            },
            {
                "type": "bulleted_list_item",
                "id": "b5",
                "has_children": False,
                "bulleted_list_item": {"rich_text": [{"plain_text": "Item liste"}]},
            },
            {
                "type": "numbered_list_item",
                "id": "b6",
                "has_children": False,
                "numbered_list_item": {"rich_text": [{"plain_text": "Item numéroté"}]},
            },
            {
                "type": "quote",
                "id": "b7",
                "has_children": False,
                "quote": {"rich_text": [{"plain_text": "Citation"}]},
            },
            {
                "type": "callout",
                "id": "b8",
                "has_children": False,
                "callout": {"rich_text": [{"plain_text": "Callout"}]},
            },
            {
                "type": "toggle",
                "id": "b9",
                "has_children": False,
                "toggle": {"rich_text": [{"plain_text": "Toggle"}]},
            },
        ],
    }
    
    mock_client = create_mock_client(structure)
    fetcher = NotionContextFetcher(client=mock_client)
    
    content = fetcher.fetch_page_full("page-root", domain="test")
    
    # Vérifier les formatages
    assert "Un paragraphe" in content.content
    assert "# Titre niveau 1" in content.content
    assert "## Titre niveau 2" in content.content
    assert "### Titre niveau 3" in content.content
    assert "- Item liste" in content.content
    assert "1. Item numéroté" in content.content
    assert "> Citation" in content.content
    assert "💡 Callout" in content.content
    assert "▶ Toggle" in content.content


def test_indentation_preserved():
    """Test que l'indentation est correctement préservée pour les niveaux imbriqués."""
    structure = {
        "page-root": [
            {
                "type": "heading_1",
                "id": "level-0",
                "has_children": True,
                "heading_1": {"rich_text": [{"plain_text": "Niveau 0"}]},
            }
        ],
        "level-0": [
            {
                "type": "paragraph",
                "id": "level-1",
                "has_children": True,
                "paragraph": {"rich_text": [{"plain_text": "Niveau 1"}]},
            }
        ],
        "level-1": [
            {
                "type": "paragraph",
                "id": "level-2",
                "has_children": False,
                "paragraph": {"rich_text": [{"plain_text": "Niveau 2"}]},
            }
        ],
    }
    
    mock_client = create_mock_client(structure)
    fetcher = NotionContextFetcher(client=mock_client)
    
    content = fetcher.fetch_page_full("page-root", domain="test")
    
    lines = content.content.split("\n")
    
    # Vérifier l'indentation (2 espaces par niveau)
    assert any(line == "# Niveau 0" for line in lines)  # Pas d'indentation
    assert any(line == "  Niveau 1" for line in lines)  # 2 espaces
    assert any(line == "    Niveau 2" for line in lines)  # 4 espaces


def test_preview_with_content_summary():
    """Test que le summary est généré depuis le contenu si absent des propriétés."""
    structure = {
        "page-root": [
            {
                "type": "paragraph",
                "id": "p1",
                "has_children": False,
                "paragraph": {"rich_text": [{"plain_text": "Ceci est le premier paragraphe avec beaucoup de contenu intéressant qui devrait apparaître dans l'aperçu de la fiche Notion."}]},
            },
            {
                "type": "paragraph",
                "id": "p2",
                "has_children": False,
                "paragraph": {"rich_text": [{"plain_text": "Un deuxième paragraphe qui ne devrait pas apparaître."}]},
            },
        ],
    }
    
    mock_client = create_mock_client(structure)
    fetcher = NotionContextFetcher(client=mock_client)
    
    # Récupérer le preview
    preview = fetcher.fetch_page_preview("page-root", domain="test")
    
    # Vérifier que le summary contient les premiers mots
    assert preview.summary != ""
    assert "premier paragraphe" in preview.summary
    assert len(preview.summary) <= 160  # Tronqué à ~150 chars + "..."


def test_token_estimate_based_on_content():
    """Test que l'estimation des tokens est basée sur le contenu réel."""
    # Structure avec beaucoup de contenu
    large_structure = {
        "page-root": [
            {
                "type": "heading_1",
                "id": "h1",
                "has_children": True,
                "heading_1": {"rich_text": [{"plain_text": "Section 1"}]},
            }
        ],
        "h1": [
            {
                "type": "paragraph",
                "id": "p1",
                "has_children": False,
                "paragraph": {"rich_text": [{"plain_text": " ".join(["mot"] * 100)}]},  # 100 mots
            },
            {
                "type": "paragraph",
                "id": "p2",
                "has_children": False,
                "paragraph": {"rich_text": [{"plain_text": " ".join(["texte"] * 100)}]},  # 100 mots
            },
        ],
    }
    
    mock_client = create_mock_client(large_structure)
    fetcher = NotionContextFetcher(client=mock_client)
    
    preview = fetcher.fetch_page_preview("page-root", domain="test")
    
    # L'estimation devrait être basée sur ~200 mots + headers
    # ~200 mots * 1.3 ≈ 260 tokens (au minimum)
    assert preview.token_estimate > 250  # Au moins 250 tokens
    assert preview.token_estimate < 500  # Mais pas trop élevé non plus


def test_extract_first_words_cleans_markdown():
    """Test que _extract_first_words nettoie correctement le markdown."""
    text = """# Titre principal
## Sous-titre

Ceci est le premier paragraphe avec du contenu réel.
Encore plus de contenu.

- Item de liste 1
- Item de liste 2

> Une citation

💡 Un callout important"""
    
    from agents.notion_context_fetcher import NotionContextFetcher
    
    result = NotionContextFetcher._extract_first_words(text, max_chars=80)
    
    # Vérifier que les headers sont ignorés
    assert "Titre principal" not in result
    assert "Sous-titre" not in result
    
    # Vérifier que le contenu réel est présent
    assert "premier paragraphe" in result
    
    # Vérifier que c'est tronqué
    assert len(result) <= 85  # 80 + "..."


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

