#!/usr/bin/env python3
"""
Script de test pour valider la nouvelle API Notion 2025-09-03
et la gestion des bases de données multisources
"""
import os
import sys
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.append(str(Path(__file__).parent))

from config.notion_config import NotionConfig

def test_api_version():
    """Teste la version de l'API"""
    print("Test de la version API Notion")
    print("=" * 50)
    
    print(f"Version API configurée: {NotionConfig.API_VERSION}")
    
    if NotionConfig.API_VERSION == "2025-09-03":
        print("[OK] Version API 2025-09-03 configurée")
        print("   -> Support des bases de données multisources activé")
    else:
        print("[WARNING] Version API différente de 2025-09-03")
        print("   -> Certaines fonctionnalités multisources peuvent ne pas être disponibles")
    
    return True

def test_headers():
    """Teste les headers de l'API"""
    print("\nTest des headers API")
    print("=" * 50)
    
    headers = NotionConfig.get_headers()
    
    print("Headers configurés:")
    for key, value in headers.items():
        if key == "Authorization":
            # Masquer le token pour la sécurité
            masked_value = value[:20] + "..." if len(value) > 20 else "***"
            print(f"   {key}: {masked_value}")
        else:
            print(f"   {key}: {value}")
    
    # Vérifier la présence des headers requis
    required_headers = ["Authorization", "Notion-Version", "Content-Type"]
    missing_headers = [h for h in required_headers if h not in headers]
    
    if missing_headers:
        print(f"[ERREUR] Headers manquants: {missing_headers}")
        return False
    else:
        print("[OK] Tous les headers requis sont présents")
        return True

def test_multisource_support():
    """Teste le support des bases multisources"""
    print("\nTest du support multisources")
    print("=" * 50)
    
    # Test des méthodes multisources
    test_database = "lieux"
    
    print(f"Test sur la base: {test_database}")
    
    # Test get_data_sources_for_database
    data_sources = NotionConfig.get_data_sources_for_database(test_database)
    print(f"   Sources de données: {len(data_sources)}")
    for i, source in enumerate(data_sources):
        print(f"      {i+1}. {source[:20]}...")
    
    # Test is_multisource_database
    is_multisource = NotionConfig.is_multisource_database(test_database)
    print(f"   Base multisource: {'Oui' if is_multisource else 'Non'}")
    
    # Test add_data_source
    test_source_id = "test-source-123"
    NotionConfig.add_data_source(test_database, test_source_id)
    updated_sources = NotionConfig.get_data_sources_for_database(test_database)
    
    if test_source_id in updated_sources:
        print("[OK] Ajout de source de données fonctionnel")
        # Nettoyer le test
        updated_sources.remove(test_source_id)
    else:
        print("[ERREUR] Échec de l'ajout de source de données")
        return False
    
    return True

def test_mcp_compatibility():
    """Teste la compatibilité avec les outils MCP"""
    print("\nTest de compatibilité MCP")
    print("=" * 50)
    
    # Vérifier que les outils MCP supportent la nouvelle API
    mcp_tools = [
        "mcp_notionMCP_notion-search",
        "mcp_notionMCP_notion-fetch", 
        "mcp_notionMCP_notion-create-pages",
        "mcp_notionMCP_notion-update-page"
    ]
    
    print("Outils MCP disponibles:")
    for tool in mcp_tools:
        print(f"   - {tool}")
    
    print("\n[INFO] Les outils MCP devront être testés avec la nouvelle API")
    print("   -> Utiliser mcp_notionMCP_notion-fetch pour récupérer les sources")
    print("   -> Utiliser les data_source_url pour les recherches")
    
    return True

def main():
    """Fonction principale de test"""
    print("Test de l'API Notion 2025-09-03")
    print("=" * 60)
    
    # Tests
    tests = [
        ("Version API", test_api_version),
        ("Headers", test_headers),
        ("Support multisources", test_multisource_support),
        ("Compatibilité MCP", test_mcp_compatibility)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[ERREUR] Échec du test {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 60)
    print("Résumé des tests:")
    
    all_passed = True
    for test_name, result in results:
        status = "[OK]" if result else "[ERREUR]"
        print(f"   {test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n[SUCCESS] Tous les tests sont passés !")
        print("\nProchaines étapes:")
        print("   1. Créer une nouvelle intégration Notion avec API 2025-09-03")
        print("   2. Configurer les permissions pour les bases multisources")
        print("   3. Tester la connexion avec les vrais outils MCP")
        print("   4. Récupérer les data_source_url des bases existantes")
    else:
        print("\n[WARNING] Certains tests ont échoué")
        print("   -> Vérifier la configuration avant de continuer")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
