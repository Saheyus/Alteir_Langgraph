"""
Configuration pytest partagée pour tous les tests

Fixtures communes:
- notion_headers: Headers pour API Notion
- sandbox_databases: IDs des bases sandbox
- test_llm: LLM configuré pour tests
- cleanup_notion_pages: Cleanup automatique des pages créées
"""
import os
import pytest
import requests
from typing import Dict, List
from dotenv import load_dotenv

# Charger .env
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_VERSION = "2022-06-28"

# Bases sandbox (ÉCRITURE AUTORISÉE)
SANDBOX_DBS = {
    "personnages": "2806e4d21b458012a744d8d6723c8be1",  # Personnages (1)
    "lieux": "2806e4d21b4580969f1cd7463a4c889c",        # Lieux (1)
}

# Bases principales (LECTURE SEULE)
MAIN_DBS = {
    "personnages": "1886e4d21b4581a29340f77f5f2e5885",
    "lieux": "1886e4d21b4581eda022ea4e0f1aba5f",
    "communautes": "1886e4d21b4581dea4f4d01beb5e1be2",
    "especes": "1886e4d21b4581e9a768df06185c1aea",
    "objets": "1886e4d21b4581098024c61acd801f52",
}

# Pages créées durant les tests (pour cleanup global)
_created_pages: List[str] = []


# ============================================================================
# FIXTURES - Configuration Notion
# ============================================================================

@pytest.fixture(scope="session")
def notion_token():
    """Token Notion pour tests"""
    if not NOTION_TOKEN:
        pytest.skip("NOTION_TOKEN non défini dans .env")
    return NOTION_TOKEN


@pytest.fixture(scope="session")
def notion_headers(notion_token):
    """Headers pour requêtes API Notion"""
    return {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="session")
def sandbox_databases():
    """IDs des bases sandbox pour tests d'écriture"""
    return SANDBOX_DBS


@pytest.fixture(scope="session")
def main_databases():
    """IDs des bases principales pour tests de lecture"""
    return MAIN_DBS


# ============================================================================
# FIXTURES - LLM
# ============================================================================

@pytest.fixture(scope="session")
def test_llm():
    """
    LLM configuré pour tests (GPT-4o-mini)
    
    Utilise GPT-4o-mini pour:
    - Rapidité (tests E2E < 3 minutes)
    - Coût minimal (~$0.01 par run)
    - Fiabilité suffisante pour tests
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        pytest.skip("OPENAI_API_KEY non défini dans .env")
    
    try:
        from langchain_openai import ChatOpenAI
        
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=1.0,
            max_tokens=2000,
        )
    except ImportError:
        pytest.skip("langchain_openai non installé")


@pytest.fixture(scope="session")
def test_llm_fast():
    """LLM ultra-rapide pour tests qui nécessitent juste une réponse"""
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        pytest.skip("OPENAI_API_KEY non défini dans .env")
    
    try:
        from langchain_openai import ChatOpenAI
        
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=1.0,
            max_tokens=500,
        )
    except ImportError:
        pytest.skip("langchain_openai non installé")


# ============================================================================
# FIXTURES - Cleanup Notion
# ============================================================================

@pytest.fixture(scope="function")
def notion_page_tracker():
    """
    Tracker pour pages créées dans un test
    
    Usage:
        def test_something(notion_page_tracker):
            page_id = create_page(...)
            notion_page_tracker.append(page_id)
            # Page sera automatiquement archivée après le test
    """
    pages = []
    yield pages
    
    # Cleanup après le test
    if pages and NOTION_TOKEN:
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": NOTION_VERSION,
        }
        
        for page_id in pages:
            try:
                url = f"https://api.notion.com/v1/pages/{page_id}"
                response = requests.patch(url, headers=headers, json={"archived": True})
                if response.status_code == 200:
                    print(f"\n[CLEANUP] ✓ Archived page: {page_id}")
                else:
                    print(f"\n[CLEANUP] ✗ Failed to archive {page_id}: {response.status_code}")
            except Exception as e:
                print(f"\n[CLEANUP] ✗ Error archiving {page_id}: {e}")


def pytest_configure(config):
    """Configuration pytest au démarrage"""
    # Enregistrer les marqueurs personnalisés
    config.addinivalue_line(
        "markers", "e2e: Tests end-to-end complets (workflow entier)"
    )
    config.addinivalue_line(
        "markers", "slow: Tests lents (> 10 secondes)"
    )
    config.addinivalue_line(
        "markers", "llm_api: Tests utilisant API LLM réelle"
    )
    config.addinivalue_line(
        "markers", "notion_api: Tests utilisant API Notion réelle"
    )
    config.addinivalue_line(
        "markers", "unit: Tests unitaires rapides"
    )
    config.addinivalue_line(
        "markers", "integration: Tests d'intégration"
    )


def pytest_collection_modifyitems(config, items):
    """Modifier les tests collectés"""
    # Auto-marquer les tests selon leur nom
    for item in items:
        # Tests E2E
        if "e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)
        
        # Tests Notion API
        if "notion" in item.nodeid and "api" in item.nodeid:
            item.add_marker(pytest.mark.notion_api)
        
        # Tests intégration qui utilisent LLM
        if any(x in item.nodeid for x in ["workflow", "writer", "reviewer", "corrector"]):
            if "integration" in item.nodeid or "e2e" in item.nodeid:
                item.add_marker(pytest.mark.llm_api)


# ============================================================================
# FIXTURES - Helpers
# ============================================================================

@pytest.fixture
def temp_output_dir(tmp_path):
    """Répertoire temporaire pour outputs de test"""
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_brief_personnage():
    """Brief simple pour tests personnages"""
    return "PNJ marchand humain, 45 ans, cynique, vend des artefacts douteux"


@pytest.fixture
def sample_brief_lieu():
    """Brief simple pour tests lieux"""
    return "Marché souterrain, taille: site, catégorie: lieu, atmosphère sombre"

