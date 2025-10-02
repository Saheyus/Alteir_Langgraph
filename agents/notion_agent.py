#!/usr/bin/env python3
"""
Agent spécialisé pour l'interaction avec Notion via MCP
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Ajouter le répertoire racine au path
sys.path.append(str(Path(__file__).parent.parent))

from config.notion_config import NotionConfig

class NotionAgent:
    """Agent pour l'interaction avec Notion via MCP"""
    
    def __init__(self):
        """Initialise l'agent Notion"""
        self.config = NotionConfig()
        self.data_source_url = "collection://2806e4d2-1b45-811b-b079-000bda28ed01"  # Personnages
    
    def search_characters(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Recherche des personnages dans la base Notion
        
        Args:
            query: Terme de recherche
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des personnages trouvés
        """
        try:
            # Utiliser l'outil MCP pour rechercher
            # Note: Dans un vrai environnement, on utiliserait les outils MCP
            print(f"Recherche de personnages: '{query}'")
            print(f"Source de données: {self.data_source_url}")
            
            # Simulation des résultats (à remplacer par un vrai appel MCP)
            results = [
                {
                    "title": "Jast, l'Inéluctable",
                    "url": "https://www.notion.so/2806e4d21b45816fafe5eaf5b2efca5a",
                    "type": "page",
                    "highlight": "machine à broyer, dirigeant de la Vieille",
                    "id": "2806e4d2-1b45-816f-afe5-eaf5b2efca5a"
                },
                {
                    "title": "L'Ensevelie",
                    "url": "https://www.notion.so/2806e4d21b45818fac94cc1dacd2447e",
                    "type": "page", 
                    "highlight": "révèle des fragments de futurs possibles",
                    "id": "2806e4d2-1b45-818f-ac94-cc1dacd2447e"
                }
            ]
            
            return results[:limit]
            
        except Exception as e:
            print(f"Erreur lors de la recherche: {e}")
            return []
    
    def get_character_details(self, character_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails d'un personnage
        
        Args:
            character_id: ID du personnage
            
        Returns:
            Détails du personnage ou None
        """
        try:
            print(f"Récupération des détails du personnage: {character_id}")
            
            # Simulation des détails (à remplacer par un vrai appel MCP)
            details = {
                "id": character_id,
                "title": "Jast, l'Inéluctable",
                "properties": {
                    "Nom": "Jast, l'Inéluctable",
                    "Type": "Entité supérieure",
                    "Archétype littéraire": ["Reine / Tyran"],
                    "Axe idéologique": "Contrôle",
                    "Qualités": ["Confiante", "Organisée", "Rigoureuse"],
                    "Défauts": ["Autoritaire", "Orgueilleuse"]
                },
                "content": "Jast n'est pas le dirigeant de la Vieille, il n'édicte pas de loi, n'interagit pas directement avec les mortels..."
            }
            
            return details
            
        except Exception as e:
            print(f"Erreur lors de la récupération des détails: {e}")
            return None
    
    def create_character(self, character_data: Dict[str, Any]) -> Optional[str]:
        """
        Crée un nouveau personnage dans Notion
        
        Args:
            character_data: Données du personnage à créer
            
        Returns:
            ID du personnage créé ou None
        """
        try:
            print(f"Création d'un nouveau personnage: {character_data.get('Nom', 'Sans nom')}")
            
            # Simulation de la création (à remplacer par un vrai appel MCP)
            new_character_id = "2806e4d2-1b45-81xx-xxxx-xxxxxxxxxxxx"
            
            print(f"Personnage créé avec l'ID: {new_character_id}")
            return new_character_id
            
        except Exception as e:
            print(f"Erreur lors de la création: {e}")
            return None
    
    def update_character(self, character_id: str, updates: Dict[str, Any]) -> bool:
        """
        Met à jour un personnage existant
        
        Args:
            character_id: ID du personnage
            updates: Données à mettre à jour
            
        Returns:
            True si la mise à jour a réussi
        """
        try:
            print(f"Mise à jour du personnage: {character_id}")
            print(f"Modifications: {list(updates.keys())}")
            
            # Simulation de la mise à jour (à remplacer par un vrai appel MCP)
            print("Personnage mis à jour avec succès")
            return True
            
        except Exception as e:
            print(f"Erreur lors de la mise à jour: {e}")
            return False
    
    def get_database_schema(self) -> Dict[str, Any]:
        """
        Récupère le schéma de la base de données
        
        Returns:
            Schéma de la base de données
        """
        try:
            print("Récupération du schéma de la base de données")
            
            # Schéma basé sur les données récupérées
            schema = {
                "properties": [
                    "Nom", "Alias", "Occupation", "Portrait", "Type",
                    "Archétype littéraire", "Espèce", "Âge", "Genre",
                    "Communautés", "Lieux de vie", "Axe idéologique",
                    "Réponse au problème moral", "Dialogues liés", "Détient",
                    "Langage", "Sprint", "Scènes", "Défauts", "Qualités",
                    "Dates majeures", "Référence visuelle", "État"
                ],
                "data_source_url": self.data_source_url,
                "database_id": "2806e4d21b458012a744d8d6723c8be1"
            }
            
            return schema
            
        except Exception as e:
            print(f"Erreur lors de la récupération du schéma: {e}")
            return {}

def main():
    """Test de l'agent Notion"""
    print("Test de l'Agent Notion")
    print("=" * 50)
    
    agent = NotionAgent()
    
    # Test 1: Recherche de personnages
    print("\n1. Test de recherche de personnages...")
    results = agent.search_characters("personnages principaux", limit=5)
    print(f"Résultats trouvés: {len(results)}")
    for result in results:
        print(f"  - {result['title']}: {result['highlight']}")
    
    # Test 2: Détails d'un personnage
    print("\n2. Test de récupération des détails...")
    if results:
        character_id = results[0]['id']
        details = agent.get_character_details(character_id)
        if details:
            print(f"Personnage: {details['title']}")
            print(f"Type: {details['properties'].get('Type', 'N/A')}")
            print(f"Archétype: {details['properties'].get('Archétype littéraire', 'N/A')}")
    
    # Test 3: Schéma de la base
    print("\n3. Test de récupération du schéma...")
    schema = agent.get_database_schema()
    print(f"Propriétés disponibles: {len(schema.get('properties', []))}")
    print(f"Source de données: {schema.get('data_source_url', 'N/A')}")
    
    print("\n[SUCCESS] Tests de l'agent Notion terminés !")

if __name__ == "__main__":
    main()
