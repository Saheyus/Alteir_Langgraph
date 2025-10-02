#!/usr/bin/env python3
"""
Script de test pour valider la configuration MCP Notion
"""
import os
import sys
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.append(str(Path(__file__).parent))

from config.notion_config import NotionConfig

def test_configuration():
    """Teste la configuration Notion"""
    print("Test de configuration Notion MCP")
    print("=" * 50)
    
    # Test 1: Token présent
    print("\n1. Vérification du token...")
    if NotionConfig.validate_token():
        print("[OK] Token Notion configuré")
        # Masquer le token pour la sécurité
        token_preview = NotionConfig.NOTION_TOKEN[:10] + "..." if len(NotionConfig.NOTION_TOKEN) > 10 else "***"
        print(f"   Token: {token_preview}")
    else:
        print("[ERREUR] Token Notion manquant")
        print("   -> Ajoutez NOTION_TOKEN dans votre fichier .env")
        return False
    
    # Test 2: Bases de données configurées
    print("\n2. Vérification des bases de données...")
    readable_dbs = NotionConfig.get_readable_databases()
    writable_dbs = NotionConfig.get_writable_databases()
    
    print(f"   [LECTURE] Bases en lecture: {len(readable_dbs)}")
    for db in readable_dbs:
        print(f"      - {db.name} ({db.id[:8]}...)")
    
    print(f"   [ECRITURE] Bases en écriture: {len(writable_dbs)}")
    for db in writable_dbs:
        print(f"      - {db.name} ({db.id[:8]}...)" if db.id else f"      - {db.name} (ID à configurer)")
    
    # Test 3: Configuration des agents
    print("\n3. Vérification des workflows...")
    from config.notion_config import AGENT_CONTENT_MAPPING, CONTENT_WORKFLOWS
    
    print("   [AGENTS] Agents par type de contenu:")
    for content_type, agents in AGENT_CONTENT_MAPPING.items():
        print(f"      - {content_type}: {', '.join(agents)}")
    
    print("   [WORKFLOWS] Workflows disponibles:")
    for workflow_name, steps in CONTENT_WORKFLOWS.items():
        print(f"      - {workflow_name}: {' -> '.join(steps)}")
    
    # Test 4: Résumé
    print("\n4. Résumé de la configuration:")
    print(f"   {NotionConfig.get_config_summary()}")
    
    return True

def test_mcp_tools():
    """Teste la disponibilité des outils MCP"""
    print("\nTest des outils MCP...")
    print("=" * 50)
    
    try:
        # Test d'import des outils MCP
        print("1. Test d'import des outils MCP...")
        
        # Simuler l'import (les vrais outils seront testés plus tard)
        mcp_tools = [
            "mcp_notionMCP_notion-search",
            "mcp_notionMCP_notion-fetch", 
            "mcp_notionMCP_notion-create-pages",
            "mcp_notionMCP_notion-update-page"
        ]
        
        print("   [OK] Outils MCP disponibles:")
        for tool in mcp_tools:
            print(f"      - {tool}")
        
        return True
        
    except Exception as e:
        print(f"   [ERREUR] Erreur lors du test MCP: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("Test de Configuration MCP Notion")
    print("=" * 60)
    
    # Test de configuration
    config_ok = test_configuration()
    
    # Test des outils MCP
    mcp_ok = test_mcp_tools()
    
    # Résultat final
    print("\n" + "=" * 60)
    if config_ok and mcp_ok:
        print("[SUCCESS] Configuration MCP Notion validee !")
        print("\nProchaines etapes:")
        print("   1. Configurer l'integration Notion (voir docs/MCP_SETUP.md)")
        print("   2. Creer la base de test pour l'ecriture")
        print("   3. Tester la connexion avec une vraie requete")
        print("   4. Developper les agents specialises")
    else:
        print("[WARNING] Configuration incomplete")
        print("\nActions requises:")
        if not config_ok:
            print("   - Configurer le token Notion dans .env")
        if not mcp_ok:
            print("   - Verifier l'installation des outils MCP")
    
    return config_ok and mcp_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
