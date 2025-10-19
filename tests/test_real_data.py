#!/usr/bin/env python3
"""
Tests avec données réelles du GDD Alteir
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from workflows.content_workflow import ContentWorkflow
from agents.writer_agent import WriterConfig
from config.domain_configs.personnages_config import PERSONNAGES_CONFIG
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
import json

console = Console()

import pytest


@pytest.mark.slow
def test_brief_1_valen():
    """Test avec Valen Arkan (alchimiste des émotions)"""
    console.print(Panel("[bold cyan]=== Test 1: Valen Arkan ===[/bold cyan]", expand=False))
    
    brief = """
    Créer un alchimiste qui transforme les émotions en substances physiques.
    
    Détails:
    - Nom: Valen Arkan
    - Alias: Le Transmuteur
    - Type: PNJ principal
    - Espèce: Humain modifié
    - Âge: 38 cycles
    - Genre: Non défini
    - Occupation: Fabricant d'émotions
    
    Profondeur:
    - Dépendant à ses propres créations (mélancolie distillée)
    - Cherche à comprendre l'essence de l'âme humaine
    - Caché dans un atelier sous les ruines d'un ancien temple
    
    Relations:
    - Elara: Ancienne amie devenue rivale, désapprouve ses méthodes
    - Korin: Jeune apprenti intrigué mais méfiant
    - Guilde des Alchimistes: Lui accorde un statut mais surveille ses excès
    """
    
    writer_config = WriterConfig(
        intent="orthogonal_depth",
        level="major",
        dialogue_mode="parle",
        creativity=0.8
    )
    
    run_test(brief, writer_config, "valen_arkan")

@pytest.mark.slow
def test_brief_2_kira():
    """Test avec Kira (voleuse orthogonale)"""
    console.print(Panel("[bold cyan]=== Test 2: Kira l'Entailleuse ===[/bold cyan]", expand=False))
    
    brief = """
    Créer une voleuse discrète avec une profondeur inattendue.
    
    Détails:
    - Nom: Kira l'Entailleuse
    - Type: PNJ recrutable
    - Espèce: Croc d'Améthyste
    - Âge: 145 cycles
    - Genre: Féminin
    - Occupation: Cartographe (surface), membre d'un culte cherchant des ossements divins (profondeur)
    
    Profondeur orthogonale:
    - Sa cartographie sert en réalité à localiser des reliques sacrées
    - Utilise un compas en os qui vibre près des ossements divins
    - Ancien partenaire: Dette de 2 cycles de protection, tabou = ne jamais mentionner l'expédition des Vertèbres
    
    Temporalité:
    - IS: Cartographe respectée
    - WAS: Exploratrice ayant découvert un secret terrible
    - COULD-HAVE-BEEN: Aurait pu devenir grande prêtresse
    """
    
    writer_config = WriterConfig(
        intent="orthogonal_depth",
        level="standard",
        dialogue_mode="parle",
        creativity=1.0
    )
    
    run_test(brief, writer_config, "kira_entailleuse")

@pytest.mark.slow
def test_brief_3_cameo():
    """Test avec personnage cameo"""
    console.print(Panel("[bold cyan]=== Test 3: Marchand Cameo ===[/bold cyan]", expand=False))
    
    brief = """
    Un marchand d'artefacts qui apparaît brièvement.
    
    Détails:
    - Nom: Torvak le Glaneur
    - Type: PNJ secondaire
    - Espèce: Gedroth
    - Occupation: Vendeur d'artefacts suspects
    
    Présence minimale mais mémorable:
    - Objet signature: Une balance qui pèse les regrets
    - Un seul secret: Il recherche un objet spécifique depuis des décennies
    """
    
    writer_config = WriterConfig(
        intent="mystere_non_resolu",
        level="cameo",
        dialogue_mode="parle",
        creativity=0.6
    )
    
    run_test(brief, writer_config, "torvak_cameo")

@pytest.mark.slow
def test_brief_4_archetype():
    """Test avec archétype assumé"""
    console.print(Panel("[bold cyan]=== Test 4: Guerrière Archétype ===[/bold cyan]", expand=False))
    
    brief = """
    Une guerrière qui assume pleinement son archétype.
    
    Détails:
    - Nom: Zara la Lame
    - Type: PNJ recrutable
    - Espèce: Humain modifié
    - Archétype: Guerrière / Surhomme (assumé)
    - Âge: 32 cycles
    
    Vocation pure:
    - Née pour le combat, formée dès l'enfance
    - Sa profondeur ALIGNÉE au rôle visible
    - Code d'honneur strict mais personnel
    - Cicatrices racontent son histoire
    """
    
    writer_config = WriterConfig(
        intent="archetype_assume",
        level="standard",
        dialogue_mode="parle",
        creativity=0.65
    )
    
    run_test(brief, writer_config, "zara_lame")

def run_test(brief: str, writer_config: WriterConfig, test_name: str):
    """Exécute un test et affiche les résultats"""
    
    console.print(f"\n[bold]Brief:[/bold] {brief[:100]}...")
    console.print(f"[bold]Config:[/bold] intent={writer_config.intent}, level={writer_config.level}, creativity={writer_config.creativity}")
    
    workflow = ContentWorkflow(PERSONNAGES_CONFIG)
    
    console.print("\n[yellow]Génération en cours...[/yellow]")
    
    try:
        result = workflow.run(brief, writer_config)
        
        # Sauvegarder
        json_file, md_file = workflow.save_results(result, prefix=f"test_{test_name}")
        
        # Afficher résumé
        console.print("\n" + "=" * 70)
        console.print(f"[bold green]RÉSULTATS - {test_name.upper()}[/bold green]")
        console.print("=" * 70)
        
        # Table des scores
        table = Table(title="Scores")
        table.add_column("Métrique", style="cyan")
        table.add_column("Valeur", style="magenta")
        table.add_column("Status", style="green")
        
        table.add_row(
            "Cohérence",
            f"{result['coherence_score']:.2f}",
            "✓" if result['coherence_score'] >= 0.7 else "✗"
        )
        table.add_row(
            "Complétude",
            f"{result['completeness_score']:.2f}",
            "✓" if result['completeness_score'] >= 0.8 else "✗"
        )
        table.add_row(
            "Qualité",
            f"{result['quality_score']:.2f}",
            "✓" if result['quality_score'] >= 0.7 else "✗"
        )
        
        console.print(table)
        
        # Statut
        if result['ready_for_publication']:
            console.print("\n[bold green]✓ Prêt pour publication[/bold green]")
        else:
            console.print("\n[bold yellow]⚠ Nécessite révision[/bold yellow]")
        
        # Problèmes
        if result['review_issues']:
            console.print(f"\n[bold yellow]Problèmes ({len(result['review_issues'])}):[/bold yellow]")
            for issue in result['review_issues'][:3]:  # Limiter à 3
                severity_color = "red" if issue['severity'] == 'critical' else "yellow"
                console.print(f"  [{severity_color}]•[/{severity_color}] {issue['description']}")
        
        # Fichiers
        console.print(f"\n[bold]Fichiers:[/bold]")
        console.print(f"  • JSON: {json_file}")
        console.print(f"  • MD: {md_file}")
        
        console.print("\n" + "=" * 70 + "\n")
        
        return result
        
    except Exception as e:
        console.print(f"[bold red]Erreur:[/bold red] {e}")
        return None

def run_all_tests():
    """Exécute tous les tests"""
    console.print(Panel(
        "[bold cyan]TESTS AVEC DONNÉES RÉELLES DU GDD ALTEIR[/bold cyan]",
        expand=False
    ))
    
    results = []
    
    # Test 1: Valen (major, orthogonal)
    results.append(test_brief_1_valen())
    
    # Test 2: Kira (standard, orthogonal)
    results.append(test_brief_2_kira())
    
    # Test 3: Torvak (cameo, mystère)
    results.append(test_brief_3_cameo())
    
    # Test 4: Zara (standard, archétype assumé)
    results.append(test_brief_4_archetype())
    
    # Résumé global
    console.print("\n" + "=" * 70)
    console.print("[bold cyan]RÉSUMÉ GLOBAL DES TESTS[/bold cyan]")
    console.print("=" * 70)
    
    summary_table = Table()
    summary_table.add_column("Test", style="cyan")
    summary_table.add_column("Cohérence", style="magenta")
    summary_table.add_column("Complétude", style="magenta")
    summary_table.add_column("Qualité", style="magenta")
    summary_table.add_column("Publication", style="green")
    
    test_names = ["Valen", "Kira", "Torvak", "Zara"]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        if result:
            summary_table.add_row(
                name,
                f"{result['coherence_score']:.2f}",
                f"{result['completeness_score']:.2f}",
                f"{result['quality_score']:.2f}",
                "✓" if result['ready_for_publication'] else "✗"
            )
    
    console.print(summary_table)
    
    # Statistiques
    valid_results = [r for r in results if r]
    if valid_results:
        avg_coherence = sum(r['coherence_score'] for r in valid_results) / len(valid_results)
        avg_completeness = sum(r['completeness_score'] for r in valid_results) / len(valid_results)
        avg_quality = sum(r['quality_score'] for r in valid_results) / len(valid_results)
        
        console.print(f"\n[bold]Moyennes:[/bold]")
        console.print(f"  • Cohérence: {avg_coherence:.2f}")
        console.print(f"  • Complétude: {avg_completeness:.2f}")
        console.print(f"  • Qualité: {avg_quality:.2f}")

if __name__ == "__main__":
    run_all_tests()

