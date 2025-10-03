#!/usr/bin/env python3
"""
Démonstration complète du workflow multi-agents avec visualisation détaillée
"""
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree
from rich import print as rprint

from config.logging_config import get_logger

sys.path.append(str(Path(__file__).parent))

from workflows.content_workflow import ContentWorkflow, WorkflowState
from agents.writer_agent import WriterConfig
from config.domain_configs.personnages_config import PERSONNAGES_CONFIG

console = Console()
logger = get_logger(__name__)

def display_header():
    """Affiche l'en-tête"""
    console.print(Panel.fit(
        "[bold cyan]Systeme Multi-Agents GDD Alteir[/bold cyan]\n"
        "[dim]Workflow: Writer > Reviewer > Corrector > Validator[/dim]",
        border_style="cyan"
    ))

def display_config(brief: str, writer_config: WriterConfig):
    """Affiche la configuration"""
    table = Table(title="Configuration", show_header=True, header_style="bold magenta")
    table.add_column("Paramètre", style="cyan")
    table.add_column("Valeur", style="yellow")
    
    table.add_row("Domaine", PERSONNAGES_CONFIG.display_name)
    table.add_row("Brief", brief[:80] + "..." if len(brief) > 80 else brief)
    table.add_row("Intent", str(writer_config.intent))
    table.add_row("Level", str(writer_config.level))
    table.add_row("Dialogue Mode", str(writer_config.dialogue_mode))
    table.add_row("Créativité", str(writer_config.creativity))
    
    console.print(table)

def display_history(state: WorkflowState):
    """Affiche l'historique du workflow"""
    tree = Tree("[bold]Historique du Workflow[/bold]")
    
    for entry in state.get("history", []):
        step_style = {
            "writer": "green",
            "reviewer": "blue",
            "corrector": "yellow",
            "validator": "magenta"
        }.get(entry["step"], "white")
        
        tree.add(f"[{step_style}]{entry['step'].upper()}[/{step_style}]: {entry['summary']}")
    
    console.print(tree)

def display_scores(state: WorkflowState):
    """Affiche les scores"""
    table = Table(title="Metriques de Qualite", show_header=True, header_style="bold green")
    table.add_column("Metrique", style="cyan")
    table.add_column("Score", justify="right", style="yellow")
    table.add_column("Statut", justify="center")
    
    def get_status(score):
        if score >= 0.8:
            return "[green][OK] Excellent[/green]"
        elif score >= 0.6:
            return "[yellow][~] Bon[/yellow]"
        else:
            return "[red][X] A ameliorer[/red]"
    
    table.add_row("Coherence", f"{state['coherence_score']:.2f}", get_status(state['coherence_score']))
    table.add_row("Completude", f"{state['completeness_score']:.2f}", get_status(state['completeness_score']))
    table.add_row("Qualite", f"{state['quality_score']:.2f}", get_status(state['quality_score']))
    
    console.print(table)

def display_issues(state: WorkflowState):
    """Affiche les problèmes et corrections"""
    if state.get("review_issues"):
        table = Table(title="Problemes Identifies", show_header=True, header_style="bold yellow")
        table.add_column("Severite", style="red")
        table.add_column("Description", style="white")
        
        for issue in state["review_issues"][:5]:  # Limiter à 5
            severity_icon = "[!]" if issue["severity"] == "critical" else "[~]"
            table.add_row(f"{severity_icon} {issue['severity']}", issue["description"][:80])
        
        if len(state["review_issues"]) > 5:
            table.add_row("...", f"[dim]+ {len(state['review_issues']) - 5} autres problemes[/dim]")
        
        console.print(table)
    
    if state.get("corrections"):
        table = Table(title="Corrections Appliquees", show_header=True, header_style="bold blue")
        table.add_column("Type", style="cyan")
        table.add_column("Original > Corrige", style="white")
        
        for corr in state["corrections"][:5]:  # Limiter à 5
            table.add_row(corr["type"], f"{corr['original']} > {corr['corrected']}")
        
        if len(state["corrections"]) > 5:
            table.add_row("...", f"[dim]+ {len(state['corrections']) - 5} autres corrections[/dim]")
        
        console.print(table)

def display_content(state: WorkflowState):
    """Affiche le contenu final"""
    content = state["content"]
    
    # Limiter à 500 caractères pour l'affichage
    display_content = content[:500] + "..." if len(content) > 500 else content
    
    console.print(Panel(
        display_content,
        title=f"[bold]Contenu Final ({len(content)} caractères)[/bold]",
        border_style="green" if state["is_valid"] else "red"
    ))

def display_final_status(state: WorkflowState):
    """Affiche le statut final"""
    is_valid = state["is_valid"]
    ready = state["ready_for_publication"]
    
    status_color = "green" if ready else ("yellow" if is_valid else "red")
    status_text = "[OK] Pret pour Publication" if ready else ("[~] Valide mais a ameliorer" if is_valid else "[X] Necessite revision")
    
    console.print(Panel.fit(
        f"[bold {status_color}]{status_text}[/bold {status_color}]\n"
        f"[dim]Valide: {is_valid} | Publication: {ready}[/dim]",
        border_style=status_color
    ))

def main():
    """Démo avec visualisation Rich"""

    logger.info("Démarrage de la démonstration du workflow")
    display_header()
    console.print()
    
    # Configuration
    brief = """Un marchand d'ombres qui vend des souvenirs volés sous forme de fragments cristallins.
    Genre: Masculin. Espèce: Croc d'Améthyste. Âge: 157 cycles.
    Opère depuis un marché flottant dans les Vertèbres du Monde.
    Cache un secret : il cherche son propre souvenir perdu."""
    
    writer_config = WriterConfig(
        intent="mystere_non_resolu",
        level="major",
        dialogue_mode="parle",
        creativity=0.8
    )
    
    display_config(brief, writer_config)
    console.print()
    
    # Créer et exécuter le workflow
    workflow = ContentWorkflow(PERSONNAGES_CONFIG)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Exécution du workflow...", total=None)
        final_state = workflow.run(brief, writer_config)
        progress.update(task, completed=True)

    logger.info(
        "Démonstration terminée | valid=%s | ready=%s",
        final_state["is_valid"],
        final_state["ready_for_publication"],
    )
    
    console.print()
    
    # Afficher les résultats
    display_history(final_state)
    console.print()
    
    display_scores(final_state)
    console.print()
    
    display_issues(final_state)
    console.print()
    
    display_content(final_state)
    console.print()
    
    display_final_status(final_state)
    console.print()
    
    # Sauvegarder
    json_file, md_file = workflow.save_results(final_state)
    
    console.print(Panel(
        f"[green][OK][/green] Resultats sauvegardes:\n"
        f"  [cyan]JSON:[/cyan] {json_file}\n"
        f"  [cyan]Markdown:[/cyan] {md_file}",
        title="Sauvegarde",
        border_style="green"
    ))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Workflow interrompu[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Erreur: {e}[/red]")

