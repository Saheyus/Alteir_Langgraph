"""
Script pratique pour exécuter les tests d'export

Usage:
    python tests/run_export_tests.py [mode]
    
Modes:
    quick    - Tests rapides seulement (extraction + payload)
    full     - Tous les tests (y compris intégration API)
    extract  - Extraction seulement
    payload  - Payload seulement
    api      - Intégration API seulement
"""

import sys
import os
import subprocess

# Configurer l'encoding pour Windows
sys.stdout.reconfigure(encoding='utf-8')


TESTS_DIR = os.path.dirname(os.path.abspath(__file__))

MODES = {
    "quick": [
        "test_export_extraction.py",
        "test_export_payload.py"
    ],
    "full": [
        "test_export_extraction.py",
        "test_export_payload.py",
        "test_export_integration.py"
    ],
    "extract": ["test_export_extraction.py"],
    "payload": ["test_export_payload.py"],
    "api": ["test_export_integration.py"],
}


def run_tests(mode: str = "quick"):
    """Exécute les tests selon le mode choisi"""
    
    if mode not in MODES:
        print(f"❌ Mode inconnu: {mode}")
        print(f"Modes disponibles: {', '.join(MODES.keys())}")
        return 1
    
    test_files = MODES[mode]
    test_paths = [os.path.join(TESTS_DIR, f) for f in test_files]
    
    print(f"\n{'='*60}")
    print(f"🧪 Mode: {mode.upper()}")
    print(f"📁 Tests: {', '.join(test_files)}")
    print(f"{'='*60}\n")
    
    # Construire la commande pytest
    cmd = ["pytest"] + test_paths + ["-v", "--tb=short"]
    
    # Ajouter marqueurs selon le mode
    if mode == "api":
        cmd.extend(["-m", "integration"])
    
    # Exécuter
    try:
        result = subprocess.run(cmd, cwd=os.path.dirname(TESTS_DIR))
        return result.returncode
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrompus par l'utilisateur")
        return 130
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return 1


def print_help():
    """Affiche l'aide"""
    print("""
🧪 Tests d'Export Notion

Usage:
    python tests/run_export_tests.py [mode]

Modes disponibles:
    quick    - Tests rapides (extraction + payload) [défaut]
               ⏱️  < 1 seconde
               ✅ Pas d'API Notion
    
    full     - Tous les tests (extraction + payload + API)
               ⏱️  ~ 10 secondes
               ⚠️  Utilise l'API Notion
    
    extract  - Tests d'extraction seulement
               ⏱️  < 0.5 seconde
               ✅ Pas d'API Notion
    
    payload  - Tests de payload seulement
               ⏱️  < 0.5 seconde
               ✅ Pas d'API Notion
    
    api      - Tests d'intégration API seulement
               ⏱️  ~ 10 secondes
               ⚠️  Utilise l'API Notion

Exemples:
    # Tests rapides (recommandé pour dev)
    python tests/run_export_tests.py quick
    
    # Tests complets (avant commit)
    python tests/run_export_tests.py full
    
    # Tester seulement l'extraction
    python tests/run_export_tests.py extract

Alternative:
    # Utiliser pytest directement
    pytest tests/test_export_extraction.py -v
    pytest tests/test_export_payload.py -v
    pytest tests/test_export_integration.py -v -m integration
""")


if __name__ == "__main__":
    # Parser les arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["-h", "--help", "help"]:
            print_help()
            sys.exit(0)
        mode = arg
    else:
        mode = "quick"
    
    # Exécuter
    exit_code = run_tests(mode)
    
    # Message de fin
    if exit_code == 0:
        print(f"\n✅ Tous les tests {mode.upper()} ont réussi !")
    else:
        print(f"\n❌ Certains tests {mode.upper()} ont échoué")
    
    sys.exit(exit_code)

