"""
Test d'intégration finale : sandbox → base principale

Vérifie que :
1. Le resolver fetch depuis les bases principales
2. Les relations fonctionnent entre sandbox et bases principales
"""

import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

# Ajouter le répertoire parent au path pour imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import du resolver
from agents.notion_relation_resolver import NotionRelationResolver


def test_complete_workflow():
    """Test complet du workflow de résolution"""
    
    print("=== Test Workflow Complet ===\n")
    
    # 1. Initialiser le resolver
    print("1. Initialisation resolver...")
    resolver = NotionRelationResolver(fuzzy_threshold=0.80)
    print("   [OK]\n")
    
    # 2. Fetch des lieux depuis la base PRINCIPALE
    print("2. Fetch lieux depuis base principale...")
    lieux_count = len(resolver.fetch_entity_names("lieux"))
    print(f"   [OK] {lieux_count} lieux en cache\n")
    
    if lieux_count == 0:
        print("   [X] Aucun lieu trouvé, impossible de continuer")
        return False
    
    # 3. Test fuzzy matching
    print("3. Test fuzzy matching...")
    test_names = [
        "Strate I",
        "La Périphérie Caudale",
        "Marché",
        "Léviathan"
    ]
    
    for test_name in test_names:
        match = resolver.find_match(test_name, "lieux")
        if match:
            print(f"   ✅ '{test_name}' → {match.matched_name} ({int(match.confidence*100)}%)")
        else:
            print(f"   ❌ '{test_name}' → Aucun match")
    
    print()
    
    # 4. Test avec création réelle dans Notion
    print("\n4. Test création page avec relation...")
    
    # Prendre un lieu existant (on sait que "Léviathan" matche à 100%)
    match = resolver.find_match("Léviathan", "lieux")
    if not match:
        print("   [X] Impossible de trouver un lieu de test")
        return False
    
    print(f"   Lieu cible: {match.matched_name}")
    print(f"   ID: {match.notion_id}")
    
    # Créer une page test dans le sandbox Personnages (1)
    import requests
    from datetime import datetime
    
    notion_token = os.getenv("NOTION_TOKEN")
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    timestamp = datetime.now().strftime("%H%M%S")
    
    # Base sandbox Personnages (1)
    sandbox_db = "2806e4d21b458012a744d8d6723c8be1"
    
    payload = {
        "parent": {"database_id": sandbox_db.replace("-", "")},
        "properties": {
            "Nom": {
                "title": [{"text": {"content": f"Test Relation {timestamp}"}}]
            },
            "État": {
                "status": {"name": "Brouillon IA"}
            },
            "Lieux de vie": {
                "relation": [{"id": match.notion_id.replace("-", "")}]
            }
        }
    }
    
    create_url = "https://api.notion.com/v1/pages"
    response = requests.post(create_url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"   [X] Erreur création: {response.status_code}")
        print(f"   {response.text}")
        return False
    
    page_data = response.json()
    page_id = page_data.get("id")
    page_url = page_data.get("url")
    
    print(f"   [OK] Page créée: {page_url}")
    
    # 5. Vérifier que la relation est présente
    print("\n5. Vérification relation...")
    
    get_url = f"https://api.notion.com/v1/pages/{page_id}"
    verify_response = requests.get(get_url, headers=headers)
    
    if verify_response.status_code == 200:
        verify_data = verify_response.json()
        lieux_prop = verify_data.get("properties", {}).get("Lieux de vie", {})
        relation_data = lieux_prop.get("relation", [])
        
        if relation_data:
            print(f"   [OK] ✅ Relation présente ! {len(relation_data)} lieu(x)")
            print(f"   Relations: {relation_data}")
            success = True
        else:
            print(f"   [X] ❌ Relation VIDE")
            print(f"   Propriété: {lieux_prop}")
            success = False
    else:
        print(f"   [X] Erreur vérification: {verify_response.status_code}")
        success = False
    
    # 6. Nettoyage (archivage)
    print("\n6. Nettoyage...")
    archive_url = f"https://api.notion.com/v1/pages/{page_id}"
    archive_response = requests.patch(archive_url, headers=headers, json={"archived": True})
    
    if archive_response.status_code == 200:
        print("   [OK] Page archivée")
    else:
        print(f"   [!] Avertissement: impossible d'archiver ({archive_response.status_code})")
    
    return success


if __name__ == "__main__":
    try:
        success = test_complete_workflow()
        
        print("\n" + "="*50)
        if success:
            print("✅ TEST RÉUSSI : Workflow complet fonctionnel !")
        else:
            print("❌ TEST ÉCHOUÉ : Problème détecté")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()

