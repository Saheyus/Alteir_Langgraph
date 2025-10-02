#!/usr/bin/env python3
"""
Tests pour le template narratif des personnages
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Import optionnel de dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

console = Console()

def test_narrative_template_structure():
    """Test: Vérifier que le template narratif contient toutes les sections requises"""
    console.print(Panel("[bold cyan]=== Test: Structure Template Narratif ===[/bold cyan]", expand=False))
    
    try:
        from config.domain_configs.personnages_config import PERSONNAGES_NARRATIVE_TEMPLATE
        
        # Sections obligatoires du template narratif
        required_sections = [
            "# Résumé de la fiche",
            "# Caractérisation",
            "## Faiblesse",
            "## Compulsion", 
            "## Désir",
            "# Background",
            "## Contexte",
            "## Apparence",
            "## Évènements marquants",
            "## Relations",
            "## Centres d'intérêt",
            "## Fluff",
            "# Arcs Narratifs",
            "## Actions concrètes",
            "## Quêtes annexes",
            "## Conséquences de la Révélation",
            "# Dialogue Type",
            "## [Thème] du jeu",
            "## Registre de langage du personnage",
            "## Champs lexicaux utilisés",
            "## Expressions courantes",
            "# Dialogue du personnage",
            "## Rencontre initiale",
            "## Exemples de dialogues"
        ]
        
        template = PERSONNAGES_NARRATIVE_TEMPLATE
        missing_sections = []
        present_sections = []
        
        for section in required_sections:
            if section in template:
                present_sections.append(section)
                console.print(f"[green][OK][/green] {section}")
            else:
                missing_sections.append(section)
                console.print(f"[red][MANQUANT][/red] {section}")
        
        console.print(f"\n[bold]Résumé:[/bold]")
        console.print(f"  • Sections présentes: {len(present_sections)}/{len(required_sections)}")
        console.print(f"  • Sections manquantes: {len(missing_sections)}")
        
        if missing_sections:
            console.print(f"\n[red]Sections manquantes:[/red] {missing_sections}")
            return False
        else:
            console.print("\n[bold green][SUCCES] Toutes les sections du template narratif sont présentes![/bold green]")
            return True
            
    except Exception as e:
        console.print(f"[bold red][ERREUR] {e}[/bold red]")
        return False

def test_domain_config_integration():
    """Test: Vérifier que la DomainConfig utilise bien le template narratif"""
    console.print(Panel("[bold cyan]=== Test: Intégration DomainConfig ===[/bold cyan]", expand=False))
    
    try:
        from config.domain_configs.personnages_config import PERSONNAGES_CONFIG
        
        # Vérifier que le template est bien une string (narratif)
        template = PERSONNAGES_CONFIG.template
        if not isinstance(template, str):
            console.print(f"[red][ERREUR] Template doit être une string, reçu: {type(template)}[/red]")
            return False
        
        # Vérifier que le schéma est bien un dict (métadonnées)
        schema = PERSONNAGES_CONFIG.schema
        if not isinstance(schema, dict):
            console.print(f"[red][ERREUR] Schema doit être un dict, reçu: {type(schema)}[/red]")
            return False
        
        # Vérifier que le template contient des sections clés
        key_sections = ["# Résumé de la fiche", "# Caractérisation", "# Background"]
        for section in key_sections:
            if section not in template:
                console.print(f"[red][ERREUR] Section manquante dans template: {section}[/red]")
                return False
        
        # Vérifier que le schéma contient des champs clés
        key_fields = ["Nom", "Type", "Espèce", "État"]
        for field in key_fields:
            if field not in schema:
                console.print(f"[red][ERREUR] Champ manquant dans schéma: {field}[/red]")
                return False
        
        console.print("[green][OK] Template narratif correctement configuré[/green]")
        console.print("[green][OK] Schéma des colonnes correctement configuré[/green]")
        console.print(f"[green][OK] Template contient {len(template.split())} mots[/green]")
        console.print(f"[green][OK] Schéma contient {len(schema)} champs[/green]")
        
        return True
        
    except Exception as e:
        console.print(f"[bold red][ERREUR] {e}[/bold red]")
        return False

def test_character_agent_template_usage():
    """Test: Vérifier que l'agent utilise bien le template narratif"""
    console.print(Panel("[bold cyan]=== Test: Agent Template Usage ===[/bold cyan]", expand=False))
    
    try:
        from agents.character_writer_agent import CharacterWriterAgent, CharacterWriterConfig
        
        # Créer l'agent
        config = CharacterWriterConfig(
            intent="orthogonal_depth",
            level="standard",
            dialogue_mode="parle"
        )
        agent = CharacterWriterAgent(config)
        
        # Vérifier que l'agent a bien chargé le template narratif
        if not hasattr(agent, 'narrative_template'):
            console.print("[red][ERREUR] Agent n'a pas d'attribut narrative_template[/red]")
            return False
        
        if not hasattr(agent, 'character_schema'):
            console.print("[red][ERREUR] Agent n'a pas d'attribut character_schema[/red]")
            return False
        
        # Vérifier que le template narratif est bien une string
        if not isinstance(agent.narrative_template, str):
            console.print(f"[red][ERREUR] narrative_template doit être une string, reçu: {type(agent.narrative_template)}[/red]")
            return False
        
        # Vérifier que le schéma est bien un dict
        if not isinstance(agent.character_schema, dict):
            console.print(f"[red][ERREUR] character_schema doit être un dict, reçu: {type(agent.character_schema)}[/red]")
            return False
        
        # Vérifier que le template contient des sections clés
        key_sections = ["# Résumé de la fiche", "# Caractérisation"]
        for section in key_sections:
            if section not in agent.narrative_template:
                console.print(f"[red][ERREUR] Section manquante: {section}[/red]")
                return False
        
        console.print("[green][OK] Agent correctement configuré avec template narratif[/green]")
        console.print(f"[green][OK] Template narratif: {len(agent.narrative_template)} caractères[/green]")
        console.print(f"[green][OK] Schéma: {len(agent.character_schema)} champs[/green]")
        
        return True
        
    except Exception as e:
        console.print(f"[bold red][ERREUR] {e}[/bold red]")
        return False

def run_narrative_template_tests():
    """Exécute tous les tests du template narratif"""
    console.print(Panel(
        "[bold cyan]TESTS TEMPLATE NARRATIF PERSONNAGES[/bold cyan]",
        expand=False
    ))
    
    results = []
    
    # Test 1: Structure du template
    results.append(("Structure Template", test_narrative_template_structure()))
    
    # Test 2: Intégration DomainConfig
    results.append(("DomainConfig Integration", test_domain_config_integration()))
    
    # Test 3: Usage dans l'agent
    results.append(("Agent Template Usage", test_character_agent_template_usage()))
    
    # Résumé global
    console.print("\n" + "=" * 70)
    console.print("[bold cyan]RÉSUMÉ GLOBAL[/bold cyan]")
    console.print("=" * 70)
    
    for test_name, success in results:
        status = "[green][OK][/green]" if success else "[red][ECHEC][/red]"
        console.print(f"{status} {test_name}")
    
    total = len(results)
    passed = sum(1 for _, s in results if s)
    
    console.print(f"\n[bold]Total:[/bold] {passed}/{total} tests réussis")
    
    if passed == total:
        console.print("\n[bold green][SUCCES] Tous les tests du template narratif sont passés![/bold green]")
    else:
        console.print(f"\n[bold red][ATTENTION] {total - passed} test(s) ont échoué[/bold red]")

if __name__ == "__main__":
    run_narrative_template_tests()
