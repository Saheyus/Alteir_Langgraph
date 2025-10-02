#!/usr/bin/env python3
"""
Tests d'intégration avec Notion
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import os
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv()

console = Console()

def test_mcp_fetch_sandbox():
    """Test: Fetch du bac à sable"""
    console.print(Panel("[bold cyan]=== Test: Fetch Bac à Sable ===[/bold cyan]", expand=False))
    
    try:
        from mcp_notionMCP_notion_fetch import mcp_notionMCP_notion_fetch
        
        sandbox_id = "2806e4d21b4580eab1a2def9831bdc80"
        
        console.print(f"\n[yellow]Récupération database {sandbox_id}...[/yellow]")
        
        result = mcp_notionMCP_notion_fetch(id=sandbox_id)
        
        console.print("\n[bold green]✓ Fetch réussi[/bold green]")
        console.print(f"\n[bold]Structure:[/bold]")
        console.print(f"  • Titre: {result.get('title', 'N/A')}")
        console.print(f"  • Type: {result.get('type', 'N/A')}")
        
        if 'data_sources' in result:
            console.print(f"  • Data sources: {len(result['data_sources'])}")
            for ds in result['data_sources']:
                console.print(f"    - {ds.get('url', 'N/A')}")
        
        return True
        
    except Exception as e:
        console.print(f"[bold red]✗ Erreur:[/bold red] {e}")
        return False

def test_mcp_search_sandbox():
    """Test: Search dans le bac à sable"""
    console.print(Panel("[bold cyan]=== Test: Search Bac à Sable ===[/bold cyan]", expand=False))
    
    try:
        from mcp_notionMCP_notion_search import mcp_notionMCP_notion_search
        
        data_source_url = "collection://2806e4d2-1b45-811b-b079-000bda28ed01"
        
        console.print(f"\n[yellow]Recherche dans {data_source_url}...[/yellow]")
        
        result = mcp_notionMCP_notion_search(
            query="personnage",
            data_source_url=data_source_url
        )
        
        console.print("\n[bold green]✓ Search réussi[/bold green]")
        
        if 'results' in result:
            console.print(f"\n[bold]Résultats:[/bold] {len(result['results'])} trouvé(s)")
            
            table = Table()
            table.add_column("Titre", style="cyan")
            table.add_column("URL", style="dim")
            
            for r in result['results'][:5]:  # Limiter à 5
                table.add_row(
                    r.get('title', 'N/A'),
                    r.get('url', 'N/A')[:50] + "..."
                )
            
            console.print(table)
        
        return True
        
    except Exception as e:
        console.print(f"[bold red]✗ Erreur:[/bold red] {e}")
        return False

def test_mcp_create_page():
    """Test: Création d'une page de test"""
    console.print(Panel("[bold cyan]=== Test: Create Page ===[/bold cyan]", expand=False))
    
    try:
        from mcp_notionMCP_notion_create_pages import mcp_notionMCP_notion_create_pages
        
        data_source_id = "2806e4d2-1b45-811b-b079-000bda28ed01"
        
        test_page = {
            "properties": {
                "Nom": "Test Personnage Auto",
                "Type": "PNJ secondaire",
                "Espèce": "Humain modifié",
                "État": "Brouillon IA"
            },
            "content": """
# Test Personnage

Ceci est un personnage de test créé automatiquement.

**Artefacts:**
1. Objet de test

**Dialogues:**
1. "Ceci est un test."
            """
        }
        
        console.print(f"\n[yellow]Création page dans data_source {data_source_id}...[/yellow]")
        
        result = mcp_notionMCP_notion_create_pages(
            parent={"data_source_id": data_source_id},
            pages=[test_page]
        )
        
        console.print("\n[bold green]✓ Création réussie[/bold green]")
        console.print(f"\n[bold]Page créée:[/bold]")
        console.print(f"  • ID: {result.get('id', 'N/A')}")
        console.print(f"  • URL: {result.get('url', 'N/A')}")
        
        return True
        
    except Exception as e:
        console.print(f"[bold red]✗ Erreur:[/bold red] {e}")
        return False

def test_fetch_main_databases():
    """Test: Fetch des bases principales (lecture seule)"""
    console.print(Panel("[bold cyan]=== Test: Fetch Bases Principales ===[/bold cyan]", expand=False))
    
    databases = {
        "Lieux": "1886e4d21b4581eda022ea4e0f1aba5f",
        "Personnages": "1886e4d21b4581a29340f77f5f2e5885",
        "Communautés": "1886e4d21b4581dea4f4d01beb5e1be2",
        "Espèces": "1886e4d21b4581e9a768df06185c1aea"
    }
    
    results = []
    
    for name, db_id in databases.items():
        try:
            from mcp_notionMCP_notion_fetch import mcp_notionMCP_notion_fetch
            
            console.print(f"\n[yellow]Fetch {name}...[/yellow]")
            
            result = mcp_notionMCP_notion_fetch(id=db_id)
            
            nb_sources = len(result.get('data_sources', []))
            console.print(f"[green]✓ {name}:[/green] {nb_sources} data source(s)")
            
            results.append((name, True, nb_sources))
            
        except Exception as e:
            console.print(f"[red]✗ {name}:[/red] {e}")
            results.append((name, False, 0))
    
    # Résumé
    console.print("\n[bold]Résumé:[/bold]")
    table = Table()
    table.add_column("Database", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Data Sources", style="magenta")
    
    for name, success, nb_sources in results:
        table.add_row(
            name,
            "✓" if success else "✗",
            str(nb_sources)
        )
    
    console.print(table)
    
    return all(s for _, s, _ in results)

def run_all_integration_tests():
    """Exécute tous les tests d'intégration"""
    console.print(Panel(
        "[bold cyan]TESTS D'INTÉGRATION NOTION[/bold cyan]",
        expand=False
    ))
    
    # Vérifier token
    notion_token = os.getenv('NOTION_TOKEN')
    if not notion_token:
        console.print("[bold red]✗ NOTION_TOKEN non configuré dans .env[/bold red]")
        return
    
    console.print(f"[green]✓ Token Notion configuré[/green] ({notion_token[:10]}...)")
    
    results = []
    
    # Test 1: Fetch sandbox
    results.append(("Fetch Sandbox", test_mcp_fetch_sandbox()))
    
    # Test 2: Search sandbox
    results.append(("Search Sandbox", test_mcp_search_sandbox()))
    
    # Test 3: Create page (écriture)
    create_confirm = console.input("\n[yellow]Tester la création de page? (o/N):[/yellow] ")
    if create_confirm.lower() == 'o':
        results.append(("Create Page", test_mcp_create_page()))
    
    # Test 4: Fetch bases principales
    results.append(("Fetch Bases", test_fetch_main_databases()))
    
    # Résumé global
    console.print("\n" + "=" * 70)
    console.print("[bold cyan]RÉSUMÉ GLOBAL[/bold cyan]")
    console.print("=" * 70)
    
    for test_name, success in results:
        status = "[green]✓[/green]" if success else "[red]✗[/red]"
        console.print(f"{status} {test_name}")
    
    total = len(results)
    passed = sum(1 for _, s in results if s)
    
    console.print(f"\n[bold]Total:[/bold] {passed}/{total} tests réussis")

if __name__ == "__main__":
    run_all_integration_tests()

