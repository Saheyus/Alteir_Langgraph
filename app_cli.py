#!/usr/bin/env python3
"""
Interface CLI pour le système multi-agents GDD Alteir
"""
import sys
import os
from pathlib import Path
try:
    # Load .env for CLI runs as well
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass
from typing import Optional

from config.logging_config import get_logger

sys.path.append(str(Path(__file__).parent))

from workflows.content_workflow import ContentWorkflow
from agents.writer_agent import WriterConfig
from config.domain_configs.personnages_config import PERSONNAGES_CONFIG

logger = get_logger(__name__)

def clear_screen():
    """Nettoie l'écran"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Affiche l'en-tête"""
    print("=" * 70)
    print(" " * 15 + "SYSTEME MULTI-AGENTS GDD ALTEIR")
    print("=" * 70)
    print()

def print_menu():
    """Affiche le menu principal"""
    print("\n" + "=" * 70)
    print("MENU PRINCIPAL")
    print("=" * 70)
    print("\n1. Creer un personnage")
    print("2. Voir les resultats generes")
    print("3. Configuration")
    print("4. Quitter")
    print()

def get_user_input(prompt: str, default: str = None) -> str:
    """Demande une saisie utilisateur"""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    
    value = input(prompt).strip()
    return value if value else default

def get_choice(options: list, prompt: str = "Votre choix") -> str:
    """Demande un choix parmi une liste"""
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")
    
    while True:
        choice = input(f"\n{prompt} (1-{len(options)}): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            pass
        print("Choix invalide, reessayez.")

def create_character():
    """Assistant de création de personnage"""
    clear_screen()
    print_header()
    print("=== CREATION DE PERSONNAGE ===\n")
    logger.info("Lancement de l'assistant de création de personnage")
    
    # Brief
    print("Decrivez le personnage a creer:")
    print("(Incluez: role, espece, age, particularites...)\n")
    brief = input("> ").strip()

    if not brief:
        print("\n[ERREUR] Le brief ne peut pas etre vide.")
        logger.warning("Brief vide fourni, annulation de la génération")
        input("\nAppuyez sur Entree pour continuer...")
        return
    
    # Intent
    print("\n--- INTENTION NARRATIVE ---")
    intents = [
        "orthogonal_depth - Profondeur NON alignee au role",
        "vocation_pure - Profondeur alignee au role",
        "archetype_assume - Archetype assumé",
        "mystere_non_resolu - Profondeur elliptique"
    ]
    intent_choice = get_choice(intents, "Intention")
    intent = intent_choice.split(" - ")[0]
    
    # Level
    print("\n--- NIVEAU DE DETAIL ---")
    levels = [
        "cameo - 4-6 repliques, minimal",
        "standard - 8-10 repliques, moyen",
        "major - 10-12 repliques, complet"
    ]
    level_choice = get_choice(levels, "Niveau")
    level = level_choice.split(" - ")[0]
    
    # Dialogue mode
    print("\n--- MODE DIALOGUE ---")
    modes = [
        "parle - Dialogues oraux",
        "gestuel - Communication gestuelle",
        "telepathique - Communication mentale",
        "ecrit_only - Messages ecrits uniquement"
    ]
    mode_choice = get_choice(modes, "Mode")
    dialogue_mode = mode_choice.split(" - ")[0]
    
    # Créativité
    print("\n--- CREATIVITE ---")
    creativity = float(get_user_input("Temperature (0.0-1.0)", "0.7"))
    
    # Récapitulatif
    print("\n" + "=" * 70)
    print("RECAPITULATIF")
    print("=" * 70)
    print(f"\nBrief: {brief}")
    print(f"Intent: {intent}")
    print(f"Niveau: {level}")
    print(f"Dialogue: {dialogue_mode}")
    print(f"Creativite: {creativity}")
    
    confirm = get_user_input("\nLancer la generation? (o/N)", "o")

    if confirm.lower() != 'o':
        print("\nAnnule.")
        logger.info("Génération annulée par l'utilisateur")
        input("\nAppuyez sur Entree pour continuer...")
        return
    
    # Génération
    print("\n" + "=" * 70)
    print("GENERATION EN COURS...")
    print("=" * 70)
    
    writer_config = WriterConfig(
        intent=intent,
        level=level,
        dialogue_mode=dialogue_mode,
        creativity=creativity
    )
    
    workflow = ContentWorkflow(PERSONNAGES_CONFIG)

    try:
        logger.info("Début de génération pour le domaine %s", PERSONNAGES_CONFIG.display_name)

        # Streaming display (simple STDOUT live)
        print("\n--- STREAMING ---\n")
        # Inject Vision page into context for CLI as well
        context_payload = None
        try:
            from config.notion_config import NotionConfig
            from agents.notion_context_fetcher import NotionContextFetcher
            fetcher = NotionContextFetcher()
            vision_page = fetcher.fetch_page_full(NotionConfig.VISION_PAGE_ID, domain="vision")
            vision_page_dict = {
                "id": vision_page.id,
                "title": vision_page.title,
                "domain": vision_page.domain,
                "summary": vision_page.summary,
                "content": vision_page.content,
                "properties": vision_page.properties,
                "token_estimate": vision_page.token_estimate,
                "last_edited": vision_page.last_edited,
            }
            context_payload = {
                "selected_ids": [vision_page.id],
                "pages": [vision_page_dict],
                "formatted": fetcher.format_context_for_llm([vision_page]),
                "token_estimate": vision_page.token_estimate,
                "previews": [],
            }
            print("\n[CTX] Contexte primaire ajouté: Vision")
        except Exception:
            pass

        buffers = {"writer": [], "reviewer": [], "corrector": [], "validator": []}
        for event, payload in workflow.run_iter_live(brief, writer_config, context=context_payload):
            if event.endswith(":start"):
                step = event.split(":")[0]
                print(f"[{step.upper()}] En cours...")
            elif event.endswith(":delta"):
                step = event.split(":")[0]
                text = payload.get("text", "")
                if text:
                    buffers[step].append(text)
                    # Print last chunk without newline to simulate live
                    print(text, end="", flush=True)
            elif event.endswith(":done"):
                step = event.split(":")[0]
                print("\n")
                # payload is the current state; keep it until loop ends
                result = payload

        # Persist once
        json_file, md_file = workflow.save_results(result)
        logger.info("Résultats enregistrés | json=%s | markdown=%s", json_file, md_file)

        # Afficher résumé
        print("\n" + "=" * 70)
        print("GENERATION TERMINEE !")
        print("=" * 70)
        print(f"\nScores:")
        print(f"  - Coherence: {result['coherence_score']:.2f}")
        print(f"  - Completude: {result['completeness_score']:.2f}")
        print(f"  - Qualite: {result['quality_score']:.2f}")
        print(f"\nStatut:")
        print(f"  - Valide: {'OUI' if result['is_valid'] else 'NON'}")
        print(f"  - Pret publication: {'OUI' if result['ready_for_publication'] else 'NON'}")
        print(f"\nFichiers:")
        print(f"  - JSON: {json_file}")
        print(f"  - Markdown: {md_file}")

        open_file = get_user_input("\nOuvrir le fichier Markdown? (o/N)", "n")
        if open_file.lower() == 'o':
            os.system(f'notepad {md_file}' if os.name == 'nt' else f'open {md_file}')

    except Exception as e:
        logger.exception("Erreur lors de la génération CLI")
        print(f"\n[ERREUR] {e}")

    input("\nAppuyez sur Entree pour continuer...")

def view_results():
    """Affiche les résultats générés"""
    clear_screen()
    print_header()
    print("=== RESULTATS GENERES ===\n")
    
    outputs_dir = Path("outputs")
    
    if not outputs_dir.exists():
        print("Aucun resultat trouve.")
        logger.info("Consultation des résultats: aucun répertoire outputs")
        input("\nAppuyez sur Entree pour continuer...")
        return
    
    # Lister les fichiers markdown
    md_files = sorted(outputs_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    if not md_files:
        print("Aucun resultat trouve.")
        logger.info("Consultation des résultats: aucun fichier Markdown")
        input("\nAppuyez sur Entree pour continuer...")
        return
    
    print(f"Fichiers disponibles ({len(md_files)}):\n")
    
    for i, file in enumerate(md_files[:10], 1):  # Limiter à 10
        timestamp = file.stem.split('_')[-2:]
        date = f"{timestamp[0][-2:]}/{timestamp[0][-4:-2]}/{timestamp[0][:4]}"
        time = f"{timestamp[1][:2]}:{timestamp[1][2:4]}"
        print(f"{i}. {file.stem.rsplit('_', 2)[0]} - {date} {time}")
    
    print(f"\n0. Retour")
    
    choice = input("\nOuvrir le fichier (0-10): ").strip()
    
    try:
        idx = int(choice)
        if idx == 0:
            return
        if 1 <= idx <= len(md_files[:10]):
            file_to_open = md_files[idx - 1]
            logger.info("Ouverture d'un résultat: %s", file_to_open)
            os.system(f'notepad {file_to_open}' if os.name == 'nt' else f'open {file_to_open}')
    except ValueError:
        pass
    
    input("\nAppuyez sur Entree pour continuer...")

def show_config():
    """Affiche la configuration"""
    clear_screen()
    print_header()
    print("=== CONFIGURATION ===\n")
    logger.info("Affichage de la configuration CLI")
    
    print("Modele LLM:")
    print(f"  Provider: {os.getenv('LLM_PROVIDER', 'openai')}")
    print(f"  Modele: gpt-5-nano")
    
    print("\nNotion:")
    notion_token = os.getenv('NOTION_TOKEN', '')
    if notion_token:
        print(f"  Token: {notion_token[:10]}... (configure)")
    else:
        print("  Token: [NON CONFIGURE]")
    
    print("\nDomaines disponibles:")
    print("  - Personnages (actif)")
    print("  - Lieux (a venir)")
    print("  - Communautes (a venir)")
    
    print("\nAgents:")
    print("  - WriterAgent (actif)")
    print("  - ReviewerAgent (actif)")
    print("  - CorrectorAgent (actif)")
    print("  - ValidatorAgent (actif)")
    
    input("\nAppuyez sur Entree pour continuer...")

def main():
    """Boucle principale"""
    logger.info("Démarrage de l'interface CLI")
    while True:
        clear_screen()
        print_header()
        print_menu()

        choice = input("Votre choix: ").strip()
        logger.debug("Choix utilisateur: %s", choice)
        
        if choice == '1':
            create_character()
        elif choice == '2':
            view_results()
        elif choice == '3':
            show_config()
        elif choice == '4':
            print("\nAu revoir !")
            logger.info("Fermeture de l'interface CLI sur demande utilisateur")
            break
        else:
            print("\nChoix invalide.")
            input("\nAppuyez sur Entree pour continuer...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Arrêt manuel via Ctrl+C")
        print("\n\nInterrompu par l'utilisateur. Au revoir !")
    except Exception as e:
        logger.exception("Erreur fatale dans la CLI")
        print(f"\n[ERREUR FATALE] {e}")
        input("\nAppuyez sur Entree pour quitter...")

