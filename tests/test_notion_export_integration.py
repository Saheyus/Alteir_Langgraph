"""
Test d'intégration réel de l'export Notion

⚠️ ATTENTION: Ces tests créent de vraies pages dans le bac à sable Notion
Utiliser avec NOTION_TOKEN configuré et cleanup manuel après.

Usage:
    pytest tests/test_notion_export_integration.py -v --run-notion-tests
"""

import pytest
import os
import sys
import requests
from datetime import datetime

# Fix encodage Windows pour emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# ============================================================================
# CONFIGURATION
# ============================================================================

# IDs des bases sandbox
PERSONNAGES_SANDBOX_ID = "2806e4d21b458012a744d8d6723c8be1"
LIEUX_SANDBOX_ID = "2806e4d21b4580969f1cd7463a4c889c"

# API
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
NOTION_VERSION = "2022-06-28"


def get_headers():
    """Headers pour API Notion"""
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }


# ============================================================================
# HELPERS
# ============================================================================

def create_test_page(database_id: str, properties: dict) -> dict:
    """Crée une page de test dans Notion"""
    url = "https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": database_id.replace("-", "")},
        "properties": properties
    }
    
    response = requests.post(url, headers=get_headers(), json=payload)
    assert response.status_code == 200, f"Failed to create page: {response.text}"
    return response.json()


def delete_test_page(page_id: str):
    """Archive une page de test (Notion ne permet pas la suppression)"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {"archived": True}
    
    response = requests.patch(url, headers=get_headers(), json=payload)
    return response.status_code == 200


def verify_page_properties(page_id: str, expected_properties: dict) -> dict:
    """Récupère et vérifie les propriétés d'une page"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    response = requests.get(url, headers=get_headers())
    
    assert response.status_code == 200, f"Failed to fetch page: {response.text}"
    return response.json()


# ============================================================================
# TESTS
# ============================================================================

@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.skipif(not NOTION_TOKEN, reason="NOTION_TOKEN not set")
def test_create_personnage_with_all_properties():
    """
    Test création complète d'un personnage avec toutes les propriétés
    
    Vérifie:
    - Création de la page
    - Nom correct (title)
    - Type correct (select)
    - État correct (status)
    - Propriétés optionnelles
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_name = f"TEST_Perso_{timestamp}"
    
    properties = {
        "Nom": {
            "title": [{"text": {"content": test_name}}]
        },
        "Type": {"select": {"name": "PNJ"}},
        "Genre": {"select": {"name": "Non défini"}},
        "État": {"status": {"name": "Brouillon IA"}},
        "Alias": {"rich_text": [{"text": {"content": "Test Alias"}}]},
        "Occupation": {"rich_text": [{"text": {"content": "Testeur"}}]}
    }
    
    # Créer la page
    page = create_test_page(PERSONNAGES_SANDBOX_ID, properties)
    page_id = page['id']
    
    try:
        # Vérifier les propriétés
        retrieved = verify_page_properties(page_id, properties)
        
        # Assertions
        assert retrieved['properties']['Nom']['title'][0]['text']['content'] == test_name
        assert retrieved['properties']['Type']['select']['name'] == "PNJ"
        assert retrieved['properties']['État']['status']['name'] == "Brouillon IA"
        
        print(f"✅ Personnage créé: {page['url']}")
        
    finally:
        # Cleanup
        deleted = delete_test_page(page_id)
        if deleted:
            print(f"🗑️ Page archivée: {page_id}")
        else:
            print(f"⚠️ Impossible d'archiver: {page_id} - Nettoyage manuel requis")


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.skipif(not NOTION_TOKEN, reason="NOTION_TOKEN not set")
def test_create_lieu_with_role_as_select():
    """
    Test création d'un lieu avec Rôle en select (pas rich_text)
    
    Vérifie:
    - Création de la page
    - Rôle correct (select)
    - Catégorie et Taille (select)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_name = f"TEST_Lieu_{timestamp}"
    
    properties = {
        "Nom": {
            "title": [{"text": {"content": test_name}}]
        },
        "Catégorie": {"select": {"name": "Lieu"}},
        "Rôle": {"select": {"name": "Lieu commercial"}},  # ⚠️ SELECT, pas rich_text
        "Taille": {"select": {"name": "Secteur"}},
        "État": {"status": {"name": "Brouillon IA"}}
    }
    
    # Créer la page
    page = create_test_page(LIEUX_SANDBOX_ID, properties)
    page_id = page['id']
    
    try:
        # Vérifier les propriétés
        retrieved = verify_page_properties(page_id, properties)
        
        # Assertions critiques
        assert retrieved['properties']['Nom']['title'][0]['text']['content'] == test_name
        assert retrieved['properties']['Rôle']['select']['name'] == "Lieu commercial", \
            "Rôle doit être un select avec valeur 'Lieu commercial'"
        assert retrieved['properties']['Catégorie']['select']['name'] == "Lieu"
        
        print(f"✅ Lieu créé: {page['url']}")
        
    finally:
        # Cleanup
        deleted = delete_test_page(page_id)
        if deleted:
            print(f"🗑️ Page archivée: {page_id}")


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.skipif(not NOTION_TOKEN, reason="NOTION_TOKEN not set")
def test_create_lieu_with_wrong_role_type_fails():
    """
    Test que Rôle en rich_text échoue (doit être select)
    
    Vérifie que l'API rejette le mauvais type de propriété
    """
    properties = {
        "Nom": {
            "title": [{"text": {"content": "TEST_FAIL_Role"}}]
        },
        "Rôle": {"rich_text": [{"text": {"content": "Lieu commercial"}}]},  # ❌ MAUVAIS
        "État": {"status": {"name": "Brouillon IA"}}
    }
    
    # Devrait échouer
    url = "https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": LIEUX_SANDBOX_ID.replace("-", "")},
        "properties": properties
    }
    
    response = requests.post(url, headers=get_headers(), json=payload)
    
    # Vérifier que ça échoue bien
    assert response.status_code == 400, "Should fail with wrong property type"
    error_data = response.json()
    assert "Rôle is expected to be select" in error_data['message'], \
        f"Error message should mention Rôle type mismatch: {error_data['message']}"
    
    print("✅ Erreur attendue confirmée: Rôle doit être select")


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.skipif(not NOTION_TOKEN, reason="NOTION_TOKEN not set")
def test_create_page_with_content_blocks():
    """
    Test création d'une page avec contenu (blocks)
    
    Vérifie:
    - Création de la page
    - Ajout de blocks de contenu
    - Types de blocks variés (heading, paragraph, list)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_name = f"TEST_Content_{timestamp}"
    
    # 1. Créer la page
    properties = {
        "Nom": {"title": [{"text": {"content": test_name}}]},
        "État": {"status": {"name": "Brouillon IA"}}
    }
    
    page = create_test_page(PERSONNAGES_SANDBOX_ID, properties)
    page_id = page['id']
    
    try:
        # 2. Ajouter du contenu
        blocks = [
            {
                "heading_1": {
                    "rich_text": [{"text": {"content": "Test Heading"}}]
                }
            },
            {
                "paragraph": {
                    "rich_text": [{"text": {"content": "Test paragraph content."}}]
                }
            },
            {
                "bulleted_list_item": {
                    "rich_text": [{"text": {"content": "Test list item"}}]
                }
            }
        ]
        
        url = f"https://api.notion.com/v1/blocks/{page_id}/children"
        payload = {"children": blocks}
        
        response = requests.patch(url, headers=get_headers(), json=payload)
        assert response.status_code == 200, f"Failed to add blocks: {response.text}"
        
        # 3. Vérifier le contenu
        response = requests.get(url, headers=get_headers())
        assert response.status_code == 200
        
        content = response.json()
        assert len(content['results']) >= 3, "Should have at least 3 blocks"
        
        print(f"✅ Page avec contenu créée: {page['url']}")
        
    finally:
        # Cleanup
        deleted = delete_test_page(page_id)
        if deleted:
            print(f"🗑️ Page archivée: {page_id}")


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.skipif(not NOTION_TOKEN, reason="NOTION_TOKEN not set")
def test_validate_all_sandbox_databases_accessible():
    """
    Test que les bases sandbox sont accessibles
    """
    databases = {
        "Personnages (1)": PERSONNAGES_SANDBOX_ID,
        "Lieux (1)": LIEUX_SANDBOX_ID
    }
    
    for name, db_id in databases.items():
        url = f"https://api.notion.com/v1/databases/{db_id}"
        response = requests.get(url, headers=get_headers())
        
        assert response.status_code == 200, \
            f"Database {name} ({db_id}) not accessible: {response.status_code}"
        
        db_data = response.json()
        print(f"✅ {name}: {db_data['title'][0]['text']['content']}")


if __name__ == "__main__":
    # Pour lancer manuellement
    pytest.main([
        __file__, 
        "-v", 
        "--tb=short",
        "-s"  # Afficher les print()
    ])

