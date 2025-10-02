"""
Helper pour récupérer et gérer les schémas Notion

Résout le problème des noms de propriétés vs IDs internes
"""

import os
import requests
from typing import Dict, Optional


class NotionSchemaHelper:
    """
    Gère les schémas des bases Notion et le mapping nom→ID
    
    Critique pour les relations : Notion nécessite l'ID interne
    de la propriété, pas son nom lisible.
    """
    
    def __init__(self):
        self.notion_token = os.getenv("NOTION_TOKEN")
        self.notion_version = "2022-06-28"
        self.schema_cache: Dict[str, Dict] = {}  # {database_id: schema}
        self.property_map_cache: Dict[str, Dict[str, str]] = {}  # {database_id: {name: id}}
    
    def fetch_database_schema(self, database_id: str) -> Optional[Dict]:
        """
        Fetch le schéma complet d'une base Notion
        
        Args:
            database_id: ID de la database (avec ou sans tirets)
        
        Returns:
            Dict avec 'properties' et métadonnées, ou None si erreur
        """
        # Formater l'ID avec tirets si nécessaire
        if "-" not in database_id and len(database_id) == 32:
            database_id = f"{database_id[:8]}-{database_id[8:12]}-{database_id[12:16]}-{database_id[16:20]}-{database_id[20:]}"
        
        # Vérifier cache
        if database_id in self.schema_cache:
            return self.schema_cache[database_id]
        
        try:
            headers = {
                "Authorization": f"Bearer {self.notion_token}",
                "Notion-Version": self.notion_version,
            }
            
            url = f"https://api.notion.com/v1/databases/{database_id}"
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                print(f"Error fetching schema: {response.status_code} - {response.text}")
                return None
            
            schema = response.json()
            
            # Mise en cache
            self.schema_cache[database_id] = schema
            
            return schema
            
        except Exception as e:
            print(f"Error in fetch_database_schema: {e}")
            return None
    
    def get_property_id_map(self, database_id: str) -> Dict[str, str]:
        """
        Récupère le mapping nom_propriété → id_propriété
        
        Args:
            database_id: ID de la database
        
        Returns:
            Dict {nom_propriété: id_propriété}
            Ex: {"Lieux de vie": "eBMT", "Communautés": "xYz1"}
        """
        # Vérifier cache
        if database_id in self.property_map_cache:
            return self.property_map_cache[database_id]
        
        # Fetch schema
        schema = self.fetch_database_schema(database_id)
        if not schema:
            return {}
        
        # Construire le mapping
        properties = schema.get("properties", {})
        property_map = {}
        
        for prop_id, prop_data in properties.items():
            prop_name = prop_data.get("name", "")
            if prop_name:
                property_map[prop_name] = prop_id
        
        # Mise en cache
        self.property_map_cache[database_id] = property_map
        
        return property_map
    
    def convert_properties_to_ids(
        self,
        properties: Dict[str, any],
        database_id: str
    ) -> Dict[str, any]:
        """
        Convertit un dict de propriétés avec noms → dict avec IDs
        
        Args:
            properties: Dict avec noms lisibles {"Lieux de vie": {...}}
            database_id: ID de la database cible
        
        Returns:
            Dict avec IDs internes {"eBMT": {...}}
        """
        prop_map = self.get_property_id_map(database_id)
        
        converted = {}
        for name, value in properties.items():
            # Chercher l'ID correspondant
            prop_id = prop_map.get(name)
            
            if prop_id:
                # Utiliser l'ID interne
                converted[prop_id] = value
            else:
                # Fallback : garder le nom (pour les propriétés standard comme "title")
                # On essaie quand même car certaines propriétés marchent avec le nom
                converted[name] = value
                print(f"Warning: Property '{name}' not found in schema, using name as fallback")
        
        return converted
    
    def get_property_type(self, database_id: str, property_name: str) -> Optional[str]:
        """
        Récupère le type d'une propriété
        
        Args:
            database_id: ID de la database
            property_name: Nom de la propriété
        
        Returns:
            Type de la propriété (ex: "relation", "select", "rich_text") ou None
        """
        schema = self.fetch_database_schema(database_id)
        if not schema:
            return None
        
        properties = schema.get("properties", {})
        
        # Chercher par nom
        for prop_id, prop_data in properties.items():
            if prop_data.get("name") == property_name:
                return prop_data.get("type")
        
        return None


if __name__ == "__main__":
    # Test du schema helper
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("=== Test NotionSchemaHelper ===\n")
    
    helper = NotionSchemaHelper()
    
    # Test avec Personnages (1) sandbox
    db_id = "2806e4d21b458012a744d8d6723c8be1"
    
    print(f"1. Fetch schema de Personnages (1)...")
    schema = helper.fetch_database_schema(db_id)
    
    if schema:
        print(f"   [OK] Schema récupéré\n")
        
        print("2. Property map (nom → ID):")
        prop_map = helper.get_property_id_map(db_id)
        
        # Afficher les propriétés importantes
        important = ["Lieux de vie", "Communautés", "Détient", "Nom"]
        for name in important:
            prop_id = prop_map.get(name, "N/A")
            prop_type = helper.get_property_type(db_id, name)
            print(f"   - {name}: {prop_id} (type: {prop_type})")
        
        print(f"\n   Total: {len(prop_map)} propriétés\n")
        
        print("3. Test conversion:")
        test_props = {
            "Nom": {"title": [{"text": {"content": "Test"}}]},
            "Lieux de vie": {"relation": [{"id": "2806e4d21b4580969f1cd7463a4c889c"}]}
        }
        
        converted = helper.convert_properties_to_ids(test_props, db_id)
        print("   Avant:")
        for k in test_props.keys():
            print(f"     - {k}")
        print("   Après:")
        for k in converted.keys():
            print(f"     - {k}")
    else:
        print("   [X] Erreur fetch schema")
    
    print("\n=== Test terminé ===")

