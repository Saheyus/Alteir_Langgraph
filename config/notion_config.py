"""
Configuration Notion MCP pour le système multi-agents GDD
"""
import os
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class NotionDatabase:
    """Configuration d'une base de données Notion"""
    id: str
    name: str
    read_access: bool = True
    write_access: bool = False
    description: str = ""

class NotionConfig:
    """Configuration centralisée pour l'accès Notion"""
    
    # Token d'intégration (à définir dans .env)
    NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
    
    # Bases de données principales (lecture seule pour commencer)
    DATABASES: Dict[str, NotionDatabase] = {
        "lieux": NotionDatabase(
            id="1886e4d21b4581eda022ea4e0f1aba5f",
            name="Lieux",
            read_access=True,
            write_access=False,
            description="Lieux et géographie du monde Alteir"
        ),
        "personnages": NotionDatabase(
            id="1886e4d21b4581a29340f77f5f2e5885",
            name="Personnages",
            read_access=True,
            write_access=False,
            description="Personnages principaux et secondaires"
        ),
        "communautes": NotionDatabase(
            id="1886e4d21b4581dea4f4d01beb5e1be2",
            name="Communautés",
            read_access=True,
            write_access=False,
            description="Groupes, organisations, factions"
        ),
        "especes": NotionDatabase(
            id="1886e4d21b4581e9a768df06185c1aea",
            name="Espèces",
            read_access=True,
            write_access=False,
            description="Races et espèces du monde"
        ),
        "objets": NotionDatabase(
            id="1886e4d21b4581098024c61acd801f52",
            name="Objets",
            read_access=True,
            write_access=False,
            description="Objets, artefacts, équipements"
        ),
        "chronologie": NotionDatabase(
            id="22c6e4d21b458066b17cc2af998de0b8",
            name="Chronologie d'Escelion",
            read_access=True,
            write_access=False,
            description="Événements historiques et timeline"
        ),
        # Base de test pour l'écriture
        "tests": NotionDatabase(
            id="",  # À remplir après création
            name="GDD - Tests Multi-Agents",
            read_access=True,
            write_access=True,
            description="Base de test pour les agents multi-agents"
        )
    }
    
    @classmethod
    def get_readable_databases(cls) -> List[NotionDatabase]:
        """Retourne les bases en lecture seule"""
        return [db for db in cls.DATABASES.values() if db.read_access]
    
    @classmethod
    def get_writable_databases(cls) -> List[NotionDatabase]:
        """Retourne les bases en écriture"""
        return [db for db in cls.DATABASES.values() if db.write_access]
    
    @classmethod
    def get_database_by_name(cls, name: str) -> NotionDatabase:
        """Retourne une base par son nom"""
        return cls.DATABASES.get(name.lower())
    
    @classmethod
    def validate_token(cls) -> bool:
        """Valide la présence du token Notion"""
        return bool(cls.NOTION_TOKEN)
    
    @classmethod
    def get_config_summary(cls) -> str:
        """Retourne un résumé de la configuration"""
        readable = len(cls.get_readable_databases())
        writable = len(cls.get_writable_databases())
        return f"Notion Config: {readable} bases en lecture, {writable} bases en écriture"

# Configuration des agents par type de contenu
AGENT_CONTENT_MAPPING = {
    "lieux": ["writer", "reviewer", "corrector"],
    "personnages": ["writer", "reviewer", "corrector", "validator"],
    "communautes": ["writer", "reviewer", "corrector"],
    "especes": ["writer", "reviewer", "corrector", "validator"],
    "objets": ["writer", "reviewer", "corrector"],
    "chronologie": ["writer", "reviewer", "corrector", "validator"],
    "tests": ["writer", "reviewer", "corrector", "validator"]
}

# Workflows par type de contenu
CONTENT_WORKFLOWS = {
    "creation": ["writer", "reviewer", "corrector", "validator"],
    "modification": ["reviewer", "corrector", "validator"],
    "correction": ["corrector", "validator"],
    "validation": ["validator"]
}
