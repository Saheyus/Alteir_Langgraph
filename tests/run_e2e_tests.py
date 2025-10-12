"""
Script pratique pour exécuter les tests E2E

Usage:
    python tests/run_e2e_tests.py [mode]
    
Modes:
    quick       - Tests rapides seulement (unit, pas E2E)
    full        - Tous les tests (unit + E2E + API)
    e2e-only    - Seulement tests E2E
    e2e-basic   - E2E basiques uniquement (personnage simple)
    e2e-context - E2E avec contexte Notion
    notion      - Tests Notion API uniquement
"""

import sys
import os
import subprocess
from pathlib import Path

# Configurer l'encoding pour Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


TESTS_DIR = Path(__file__).parent

MODES = {
    # Tests rapides (pas d'API)
    "quick": {
        "tests": [
            "test_export_extraction.py",
            "test_export_payload.py",
        ],
        "markers": "unit",
        "description": "Tests unitaires rapides (< 2 secondes)"
    },
    
    # Tests complets (tout)
    "full": {
        "tests": [
            "test_export_extraction.py",
            "test_export_payload.py",
            "test_export_integration.py",
            "test_notion_api.py",
            "test_e2e_workflow_personnage.py",
            "test_e2e_workflow_with_context.py",
            "test_e2e_error_handling.py",
            "test_writer_agent.py",
            "test_structured_outputs_agents.py",
        ],
        "markers": None,
        "description": "Tous les tests (unit + E2E + API) (~3-5 minutes)"
    },
    
    # E2E seulement
    "e2e-only": {
        "tests": [
            "test_e2e_workflow_personnage.py",
            "test_e2e_workflow_with_context.py",
            "test_e2e_error_handling.py",
        ],
        "markers": "e2e",
        "description": "Seulement tests E2E (~2-3 minutes)"
    },
    
    # E2E basiques
    "e2e-basic": {
        "tests": [
            "test_e2e_workflow_personnage.py::TestE2EWorkflowPersonnageBasic",
        ],
        "markers": None,
        "description": "E2E basiques uniquement (~1 minute)"
    },
    
    # E2E avec contexte
    "e2e-context": {
        "tests": [
            "test_e2e_workflow_with_context.py",
        ],
        "markers": None,
        "description": "E2E avec contexte Notion (~1-2 minutes)"
    },
    
    # Tests Notion API
    "notion": {
        "tests": [
            "test_notion_api.py",
            "test_export_integration.py",
        ],
        "markers": "notion_api",
        "description": "Tests API Notion (~30 secondes)"
    },
    
    # Tests Writer
    "writer": {
        "tests": [
            "test_writer_agent.py",
        ],
        "markers": None,
        "description": "Tests WriterAgent (~1 minute)"
    },
}


def print_banner(title):
    """Affiche une bannière"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def run_tests(mode: str = "quick"):
    """Exécute les tests selon le mode choisi"""
    
    if mode not in MODES:
        print(f"❌ Mode inconnu: {mode}")
        print(f"\nModes disponibles:")
        for m, config in MODES.items():
            print(f"  - {m:12} : {config['description']}")
        return 1
    
    config = MODES[mode]
    test_files = config["tests"]
    markers = config["markers"]
    description = config["description"]
    
    print_banner(f"🧪 Tests E2E - Mode: {mode.upper()}")
    print(f"Description: {description}")
    print(f"Tests: {len(test_files)} fichiers")
    
    # Vérifier prérequis
    print("\n📋 Vérification des prérequis...")
    
    # Vérifier .env
    env_file = Path(__file__).parent.parent / ".env"
    if not env_file.exists():
        print("⚠️  Fichier .env non trouvé")
        print("   Certains tests peuvent échouer sans NOTION_TOKEN et OPENAI_API_KEY")
    else:
        print("✓ Fichier .env présent")
    
    # Vérifier tokens
    has_notion = bool(os.getenv("NOTION_TOKEN"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    
    print(f"✓ NOTION_TOKEN: {'Configuré' if has_notion else '❌ Manquant'}")
    print(f"✓ OPENAI_API_KEY: {'Configuré' if has_openai else '❌ Manquant'}")
    
    if not has_notion and "notion" in mode:
        print("\n❌ NOTION_TOKEN requis pour les tests Notion")
        return 1
    
    if not has_openai and ("e2e" in mode or "writer" in mode):
        print("\n❌ OPENAI_API_KEY requis pour les tests E2E/Writer")
        return 1
    
    # Construire la commande pytest
    test_paths = [str(TESTS_DIR / f) for f in test_files]
    
    cmd = ["pytest"] + test_paths + ["-v", "--tb=short", "-s"]
    
    # Ajouter marqueurs si spécifié
    if markers:
        cmd.extend(["-m", markers])
    
    # Afficher commande
    print(f"\n📦 Commande pytest:")
    print(f"   {' '.join(cmd)}\n")
    
    # Exécuter
    print_banner("🚀 Exécution des tests")
    
    try:
        result = subprocess.run(cmd, cwd=TESTS_DIR.parent)
        return result.returncode
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrompus par l'utilisateur")
        return 130
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return 1


def print_help():
    """Affiche l'aide"""
    print("""
🧪 Tests E2E - Système Multi-Agents GDD Alteir

Usage:
    python tests/run_e2e_tests.py [mode]

Modes disponibles:
""")
    
    for mode, config in MODES.items():
        print(f"  {mode:12} - {config['description']}")
    
    print("""
Exemples:

    # Tests rapides (recommandé pour dev)
    python tests/run_e2e_tests.py quick
    
    # Tests E2E complets
    python tests/run_e2e_tests.py e2e-only
    
    # Tout exécuter (avant commit)
    python tests/run_e2e_tests.py full

Prérequis:

    - .env configuré avec:
        NOTION_TOKEN=secret_...
        OPENAI_API_KEY=sk-...
    
    - Dépendances installées:
        pip install -r requirements.txt

Coût estimé:

    - quick      : Gratuit (pas d'API)
    - e2e-basic  : ~$0.01 (2-3 appels LLM)
    - e2e-only   : ~$0.02-0.03 (10-15 appels LLM)
    - full       : ~$0.03-0.05 (15-20 appels LLM)

Alternative:

    # Utiliser pytest directement
    pytest tests/test_e2e_workflow_personnage.py -v -s
    pytest tests/ -m "e2e" -v
    pytest tests/ -m "not slow" -v
""")


def print_summary(exit_code: int, mode: str):
    """Affiche un résumé des résultats"""
    print_banner("📊 Résumé")
    
    if exit_code == 0:
        print(f"✅ Tous les tests {mode.upper()} ont réussi !")
        print(f"\nProchaines étapes:")
        
        if mode == "quick":
            print(f"  → Lancer tests E2E: python tests/run_e2e_tests.py e2e-basic")
        elif mode == "e2e-basic":
            print(f"  → Lancer tous les E2E: python tests/run_e2e_tests.py e2e-only")
        elif mode == "e2e-only":
            print(f"  → Lancer suite complète: python tests/run_e2e_tests.py full")
        else:
            print(f"  → Tous les tests passent, prêt pour commit !")
    else:
        print(f"❌ Certains tests {mode.upper()} ont échoué")
        print(f"\nActions suggérées:")
        print(f"  1. Vérifier les logs d'erreur ci-dessus")
        print(f"  2. Lancer le test spécifique: pytest tests/test_xxx.py::test_name -v -s")
        print(f"  3. Vérifier .env et tokens API")


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
    
    # Résumé
    print_summary(exit_code, mode)
    
    sys.exit(exit_code)

