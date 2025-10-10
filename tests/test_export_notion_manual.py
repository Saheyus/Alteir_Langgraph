#!/usr/bin/env python3
"""
Test manuel de l'export Notion pour débugger les problèmes
Usage: python tests/test_export_notion_manual.py
"""
import sys
from pathlib import Path
import json
import logging

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

from config.notion_config import NotionConfig

def test_config():
    """Test la configuration Notion"""
    print("="*60)
    print("TEST CONFIGURATION NOTION")
    print("="*60)
    print(f"Token présent: {bool(NotionConfig.NOTION_TOKEN)}")
    print(f"Token (10 premiers car): {NotionConfig.NOTION_TOKEN[:10] if NotionConfig.NOTION_TOKEN else 'VIDE'}")
    print(f"API Version: {NotionConfig.API_VERSION}")
    print(f"DRY_RUN: {NotionConfig.DRY_RUN}")
    print(f"Sandbox Personnages: {NotionConfig.SANDBOX_DATABASE_IDS['personnages']}")
    print(f"Sandbox Lieux: {NotionConfig.SANDBOX_DATABASE_IDS['lieux']}")
    print()

def test_export_function():
    """Test l'export avec un résultat fictif"""
    print("="*60)
    print("TEST EXPORT FUNCTION")
    print("="*60)
    
    # Charger un vrai résultat si disponible
    outputs_dir = Path("outputs")
    json_files = list(outputs_dir.glob("personnages_*.json"))
    
    if not json_files:
        print("❌ Aucun fichier de résultat trouvé dans outputs/")
        return
    
    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
    print(f"📄 Fichier de test: {latest_file.name}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        result = json.load(f)
    
    print(f"  - Domain: {result.get('domain')}")
    print(f"  - Brief: {result.get('brief', '')[:80]}")
    print(f"  - Content length: {len(result.get('content', ''))} chars")
    print()
    
    # Simuler l'export (mode dry-run forcé pour le test)
    original_dry_run = NotionConfig.DRY_RUN
    NotionConfig.DRY_RUN = False  # Forcer l'export réel
    
    print("🚀 Lancement export (DRY_RUN forcé à False)...")
    
    try:
        from app.streamlit_app.results import export_to_notion
        
        # Mock container pour éviter erreur Streamlit
        class MockContainer:
            def markdown(self, *args, **kwargs):
                print(f"  [MARKDOWN] {args[0][:100]}...")
            def error(self, msg):
                print(f"  [ERROR] {msg}")
            def exception(self, exc):
                print(f"  [EXCEPTION] {exc}")
        
        # Créer un mock de streamlit pour éviter l'erreur
        import streamlit as st_mock
        
        result_export = export_to_notion(result)
        
        print()
        print("="*60)
        print("RÉSULTAT EXPORT")
        print("="*60)
        print(json.dumps(result_export, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ Erreur lors de l'export: {e}")
        import traceback
        traceback.print_exc()
    finally:
        NotionConfig.DRY_RUN = original_dry_run

if __name__ == "__main__":
    test_config()
    test_export_function()

