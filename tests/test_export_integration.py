"""
Tests d'intégration pour l'export Notion (API réelle)

⚠️ Ces tests créent de vraies pages dans Notion (sandbox)
⚠️ Cleanup automatique après chaque test
"""

import pytest
import sys
import os
import requests
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_export_payload import build_notion_properties_personnage, build_notion_properties_lieu
from tests.test_export_extraction import sample_personnage_content, sample_lieu_content


# ============================================================================
# CONFIGURATION
# ============================================================================

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_VERSION = "2022-06-28"

SANDBOX_DBS = {
    "personnages": "2806e4d21b458012a744d8d6723c8be1",  # Personnages (1)
    "lieux": "2806e4d21b4580969f1cd7463a4c889c",  # Lieux (1)
}

# Pages créées durant les tests (pour cleanup)
created_pages = []


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def notion_headers():
    """Headers pour les requêtes Notion"""
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="function", autouse=True)
def cleanup_pages(notion_headers):
    """Cleanup automatique des pages créées après chaque test"""
    yield
    
    # Archiver toutes les pages créées
    for page_id in created_pages:
        try:
            archive_url = f"https://api.notion.com/v1/pages/{page_id}"
            requests.patch(archive_url, headers=notion_headers, json={"archived": True})
            print(f"\n[CLEANUP] Archived page: {page_id}")
        except Exception as e:
            print(f"\n[CLEANUP] Failed to archive {page_id}: {e}")
    
    created_pages.clear()


# ============================================================================
# HELPERS
# ============================================================================

def create_notion_page(database_id: str, properties: dict, headers: dict) -> dict:
    """Crée une page dans Notion et retourne la réponse"""
    url = "https://api.notion.com/v1/pages"
    
    payload = {
        "parent": {"database_id": database_id.replace("-", "")},
        "properties": properties
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        page_data = response.json()
        created_pages.append(page_data["id"])
        return page_data
    else:
        raise Exception(f"Notion API Error: {response.status_code} - {response.text}")


def get_page_properties(page_id: str, headers: dict) -> dict:
    """Récupère les propriétés d'une page"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()["properties"]
    else:
        raise Exception(f"Failed to get page: {response.status_code}")


# ============================================================================
# TESTS - Export Personnage
# ============================================================================

@pytest.mark.integration
@pytest.mark.slow
class TestExportPersonnageIntegration:
    """Tests d'export réel pour personnages"""
    
    def test_create_personnage_basic(self, notion_headers, sample_personnage_content):
        """Test basique : création d'un personnage dans Notion"""
        properties = build_notion_properties_personnage(sample_personnage_content)
        
        page_data = create_notion_page(
            SANDBOX_DBS["personnages"],
            properties,
            notion_headers
        )
        
        assert page_data["id"] is not None
        assert page_data["url"] is not None
        print(f"\n✅ Page créée: {page_data['url']}")
    
    def test_personnage_properties_saved(self, notion_headers, sample_personnage_content):
        """Vérifie que les propriétés sont bien sauvegardées"""
        properties = build_notion_properties_personnage(sample_personnage_content)
        
        page_data = create_notion_page(
            SANDBOX_DBS["personnages"],
            properties,
            notion_headers
        )
        
        # Récupérer les propriétés sauvegardées
        saved_props = get_page_properties(page_data["id"], notion_headers)
        
        # Vérifier les champs essentiels
        assert saved_props["Nom"]["title"][0]["plain_text"] == "Drarus Lumenflex"
        assert saved_props["Type"]["select"]["name"] == "PNJ"
        assert saved_props["Genre"]["select"]["name"] == "Masculin"
        assert saved_props["Axe idéologique"]["select"]["name"] == "Subversion"
        
        print(f"\n✅ Propriétés vérifiées pour: {page_data['url']}")
    
    def test_personnage_multiselects_saved(self, notion_headers, sample_personnage_content):
        """Vérifie que les multi-selects sont bien sauvegardés"""
        properties = build_notion_properties_personnage(sample_personnage_content)
        
        page_data = create_notion_page(
            SANDBOX_DBS["personnages"],
            properties,
            notion_headers
        )
        
        saved_props = get_page_properties(page_data["id"], notion_headers)
        
        # Archétype
        archetypes = saved_props["Archétype littéraire"]["multi_select"]
        assert len(archetypes) == 2
        archetype_names = [a["name"] for a in archetypes]
        assert "Mentor / Gourou" in archetype_names
        
        # Qualités
        qualites = saved_props["Qualités"]["multi_select"]
        assert len(qualites) == 3
        
        # Défauts
        defauts = saved_props["Défauts"]["multi_select"]
        assert len(defauts) == 3
        
        print(f"\n✅ Multi-selects vérifiés pour: {page_data['url']}")
    
    def test_personnage_rich_text_saved(self, notion_headers, sample_personnage_content):
        """Vérifie que les rich text sont bien sauvegardés"""
        properties = build_notion_properties_personnage(sample_personnage_content)
        
        page_data = create_notion_page(
            SANDBOX_DBS["personnages"],
            properties,
            notion_headers
        )
        
        saved_props = get_page_properties(page_data["id"], notion_headers)
        
        # Alias
        alias = saved_props["Alias"]["rich_text"][0]["plain_text"]
        assert alias == "Le Tisseur d'Ombres"
        
        # Réponse au problème moral
        reponse = saved_props["Réponse au problème moral"]["rich_text"]
        if reponse:  # Peut être vide selon config Notion
            assert len(reponse[0]["plain_text"]) > 0
        
        print(f"\n✅ Rich text vérifiés pour: {page_data['url']}")


# ============================================================================
# TESTS - Export Lieu
# ============================================================================

@pytest.mark.integration
@pytest.mark.slow
class TestExportLieuIntegration:
    """Tests d'export réel pour lieux"""
    
    def test_create_lieu_basic(self, notion_headers, sample_lieu_content):
        """Test basique : création d'un lieu dans Notion"""
        properties = build_notion_properties_lieu(sample_lieu_content)
        
        page_data = create_notion_page(
            SANDBOX_DBS["lieux"],
            properties,
            notion_headers
        )
        
        assert page_data["id"] is not None
        assert page_data["url"] is not None
        print(f"\n✅ Lieu créé: {page_data['url']}")
    
    def test_lieu_properties_saved(self, notion_headers, sample_lieu_content):
        """Vérifie que les propriétés lieu sont bien sauvegardées"""
        properties = build_notion_properties_lieu(sample_lieu_content)
        
        page_data = create_notion_page(
            SANDBOX_DBS["lieux"],
            properties,
            notion_headers
        )
        
        saved_props = get_page_properties(page_data["id"], notion_headers)
        
        assert saved_props["Nom"]["title"][0]["plain_text"] == "Marché des Placides Respirants"
        assert saved_props["Catégorie"]["select"]["name"] == "Lieu"
        assert saved_props["Taille"]["select"]["name"] == "Site"
        assert saved_props["Rôle"]["select"]["name"] == "Lieu commercial"
        
        print(f"\n✅ Propriétés lieu vérifiées pour: {page_data['url']}")


# ============================================================================
# TESTS - Validation complète
# ============================================================================

@pytest.mark.integration
@pytest.mark.slow
class TestExportComplet:
    """Tests de validation complète de l'export"""
    
    def test_personnage_all_critical_fields(self, notion_headers, sample_personnage_content):
        """Vérifie TOUS les champs critiques demandés par l'utilisateur"""
        properties = build_notion_properties_personnage(sample_personnage_content)
        
        page_data = create_notion_page(
            SANDBOX_DBS["personnages"],
            properties,
            notion_headers
        )
        
        saved_props = get_page_properties(page_data["id"], notion_headers)
        
        # Liste des champs critiques (user query)
        critical_fields = {
            "Nom": "Drarus Lumenflex",
            "Type": "PNJ",
            "Genre": "Masculin",
            "Axe idéologique": "Subversion",
        }
        
        for field_name, expected_value in critical_fields.items():
            prop = saved_props[field_name]
            
            if "title" in prop:
                actual = prop["title"][0]["plain_text"]
            elif "select" in prop:
                actual = prop["select"]["name"]
            else:
                actual = None
            
            assert actual == expected_value, f"{field_name}: expected {expected_value}, got {actual}"
        
        # Vérifier présence multi-selects
        assert len(saved_props["Archétype littéraire"]["multi_select"]) > 0
        assert len(saved_props["Qualités"]["multi_select"]) > 0
        assert len(saved_props["Défauts"]["multi_select"]) > 0
        
        print(f"\n✅ TOUS les champs critiques vérifiés: {page_data['url']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

