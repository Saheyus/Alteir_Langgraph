"""
Tests consolidés pour l'API Notion

Regroupe les tests de:
- test_notion_connection.py
- test_sandbox_connection.py
- test_notion_api_2025.py
- test_notion_integration.py

Tests organisés par catégorie:
- Configuration
- Connexion (sandbox et bases principales)
- API basique (fetch, search)
- API version 2025-09-03
"""
import pytest
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config.notion_config import NotionConfig


# ============================================================================
# TESTS - Configuration
# ============================================================================

class TestNotionConfiguration:
    """Tests de configuration Notion"""
    
    def test_token_present(self, notion_token):
        """Vérifie que le token Notion est configuré"""
        assert notion_token
        assert len(notion_token) > 20
        assert notion_token.startswith("secret_") or notion_token.startswith("ntn_")
    
    def test_api_version(self):
        """Vérifie la version de l'API"""
        assert NotionConfig.API_VERSION == "2025-09-03"
    
    def test_headers_complete(self, notion_headers):
        """Vérifie que tous les headers requis sont présents"""
        required = ["Authorization", "Notion-Version", "Content-Type"]
        for header in required:
            assert header in notion_headers
    
    def test_sandbox_databases_configured(self, sandbox_databases):
        """Vérifie que les bases sandbox sont configurées"""
        assert "personnages" in sandbox_databases
        assert "lieux" in sandbox_databases
        assert len(sandbox_databases["personnages"]) == 32  # UUID sans tirets
        assert len(sandbox_databases["lieux"]) == 32
    
    def test_main_databases_configured(self, main_databases):
        """Vérifie que les bases principales sont configurées"""
        assert "personnages" in main_databases
        assert "lieux" in main_databases
        assert "communautes" in main_databases
        assert "especes" in main_databases


# ============================================================================
# TESTS - Connexion Sandbox
# ============================================================================

class TestSandboxConnection:
    """Tests de connexion avec les bases sandbox"""
    
    @pytest.mark.notion_api
    @pytest.mark.slow
    def test_fetch_sandbox_personnages(self, notion_headers, sandbox_databases):
        """Test fetch de la base sandbox Personnages (1)"""
        import requests
        
        db_id = sandbox_databases["personnages"]
        url = f"https://api.notion.com/v1/databases/{db_id}"
        
        response = requests.get(url, headers=notion_headers)
        
        assert response.status_code == 200, f"Failed to fetch database: {response.text}"
        
        data = response.json()
        assert data["object"] == "database"
        assert "properties" in data
        
        # Vérifier propriétés essentielles personnages
        assert "Nom" in data["properties"]
        assert "Type" in data["properties"]
        assert "Genre" in data["properties"]
    
    @pytest.mark.notion_api
    @pytest.mark.slow
    def test_fetch_sandbox_lieux(self, notion_headers, sandbox_databases):
        """Test fetch de la base sandbox Lieux (1)"""
        import requests
        
        db_id = sandbox_databases["lieux"]
        url = f"https://api.notion.com/v1/databases/{db_id}"
        
        response = requests.get(url, headers=notion_headers)
        
        assert response.status_code == 200, f"Failed to fetch database: {response.text}"
        
        data = response.json()
        assert data["object"] == "database"
        assert "properties" in data
        
        # Vérifier propriétés essentielles lieux
        assert "Nom" in data["properties"]
        assert "Catégorie" in data["properties"]
        assert "Rôle" in data["properties"]


# ============================================================================
# TESTS - Connexion Bases Principales (Lecture Seule)
# ============================================================================

class TestMainDatabasesConnection:
    """Tests de connexion avec les bases principales (lecture seule)"""
    
    @pytest.mark.notion_api
    @pytest.mark.slow
    def test_fetch_main_personnages(self, notion_headers, main_databases):
        """Test fetch de la base principale Personnages"""
        import requests
        
        db_id = main_databases["personnages"]
        url = f"https://api.notion.com/v1/databases/{db_id}"
        
        response = requests.get(url, headers=notion_headers)
        
        assert response.status_code == 200, f"Failed to fetch database: {response.text}"
        
        data = response.json()
        assert data["object"] == "database"
        assert "properties" in data
    
    @pytest.mark.notion_api
    @pytest.mark.slow
    def test_fetch_main_lieux(self, notion_headers, main_databases):
        """Test fetch de la base principale Lieux"""
        import requests
        
        db_id = main_databases["lieux"]
        url = f"https://api.notion.com/v1/databases/{db_id}"
        
        response = requests.get(url, headers=notion_headers)
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["object"] == "database"
    
    @pytest.mark.notion_api
    @pytest.mark.slow
    def test_fetch_main_communautes(self, notion_headers, main_databases):
        """Test fetch de la base principale Communautés"""
        import requests
        
        db_id = main_databases["communautes"]
        url = f"https://api.notion.com/v1/databases/{db_id}"
        
        response = requests.get(url, headers=notion_headers)
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["object"] == "database"


# ============================================================================
# TESTS - API Basique
# ============================================================================

class TestNotionBasicAPI:
    """Tests des opérations API basiques"""
    
    @pytest.mark.notion_api
    @pytest.mark.slow
    def test_query_empty_sandbox(self, notion_headers, sandbox_databases):
        """Test query d'une base sandbox (peut être vide)"""
        import requests
        
        db_id = sandbox_databases["personnages"]
        url = f"https://api.notion.com/v1/databases/{db_id}/query"
        
        response = requests.post(url, headers=notion_headers, json={})
        
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)
    
    @pytest.mark.notion_api
    @pytest.mark.slow
    def test_create_and_delete_page(self, notion_headers, sandbox_databases, notion_page_tracker):
        """Test création et suppression d'une page dans le sandbox"""
        import requests
        
        db_id = sandbox_databases["personnages"]
        
        # Créer une page de test
        create_url = "https://api.notion.com/v1/pages"
        payload = {
            "parent": {"database_id": db_id},
            "properties": {
                "Nom": {
                    "title": [{"text": {"content": "TEST_API_Personnage"}}]
                },
                "Type": {
                    "select": {"name": "PNJ"}
                },
                "Genre": {
                    "select": {"name": "Non défini"}
                },
                "État": {
                    "status": {"name": "Brouillon IA"}
                }
            }
        }
        
        response = requests.post(create_url, headers=notion_headers, json=payload)
        
        assert response.status_code == 200, f"Failed to create page: {response.text}"
        
        page_data = response.json()
        page_id = page_data["id"]
        
        # Ajouter au tracker pour cleanup automatique
        notion_page_tracker.append(page_id)
        
        # Vérifier que la page existe
        get_url = f"https://api.notion.com/v1/pages/{page_id}"
        response = requests.get(get_url, headers=notion_headers)
        
        assert response.status_code == 200
        assert response.json()["id"] == page_id


# ============================================================================
# TESTS - API Version 2025-09-03
# ============================================================================

class TestNotion2025API:
    """Tests spécifiques à la version API 2025-09-03"""
    
    def test_headers_include_correct_version(self, notion_headers):
        """Vérifie que les headers utilisent la bonne version"""
        # Note: Pour version 2025-09-03, on utilise encore 2022-06-28
        # car la vraie version n'est pas encore déployée
        assert notion_headers["Notion-Version"] in ["2022-06-28", "2025-09-03"]
    
    @pytest.mark.notion_api
    @pytest.mark.slow
    def test_database_has_properties(self, notion_headers, sandbox_databases):
        """Vérifie que fetch database retourne les propriétés"""
        import requests
        
        db_id = sandbox_databases["personnages"]
        url = f"https://api.notion.com/v1/databases/{db_id}"
        
        response = requests.get(url, headers=notion_headers)
        
        assert response.status_code == 200
        
        data = response.json()
        assert "properties" in data
        assert len(data["properties"]) > 0


# ============================================================================
# TESTS - Intégration NotionConfig
# ============================================================================

class TestNotionConfigMethods:
    """Tests des méthodes utilitaires NotionConfig"""
    
    def test_validate_token(self):
        """Test validation du token"""
        # Si on arrive ici, le token est validé par la fixture
        assert NotionConfig.validate_token()
    
    def test_get_headers(self):
        """Test récupération des headers"""
        headers = NotionConfig.get_headers()
        
        assert "Authorization" in headers
        assert "Notion-Version" in headers
        assert "Content-Type" in headers
    
    def test_get_readable_databases(self):
        """Test récupération des bases en lecture"""
        dbs = NotionConfig.get_readable_databases()
        
        assert len(dbs) > 0
        
        # Vérifier structure
        for db in dbs:
            assert hasattr(db, "id")
            assert hasattr(db, "name")
    
    def test_get_writable_databases(self):
        """Test récupération des bases en écriture"""
        dbs = NotionConfig.get_writable_databases()
        
        assert len(dbs) > 0
        
        # Les bases sandbox doivent être présentes
        names = [db.name for db in dbs]
        assert any("Personnages" in name for name in names)
        assert any("Lieux" in name for name in names)

