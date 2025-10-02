#!/usr/bin/env python3
"""
Test du template narratif avec la limite de tokens augmentée
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from agents.character_writer_agent import CharacterWriterAgent, CharacterWriterConfig

def test_template_tokens():
    """Test avec la limite de tokens augmentée (8000 tokens)"""
    print("=== Test Template Narratif avec 8000 tokens ===\n")
    
    # Configuration de test
    config = CharacterWriterConfig(
        intent="orthogonal_depth",
        level="standard",
        dialogue_mode="parle"
    )
    
    # Créer l'agent
    agent = CharacterWriterAgent(config)
    
    # Brief de test
    brief = """Un musicien itinérant qui collecte les souvenirs des morts. 
    Genre: Neutre. Espèce: Champignon anthropophage. 
    Âge: Inconnu (semble avoir plusieurs siècles)."""
    
    print(f"Brief: {brief}\n")
    print("Génération avec template narratif complet (8000 tokens)...\n")
    
    # Générer le personnage
    result = agent.generate_character(brief)
    
    print("=" * 80)
    print("RÉSULTAT:")
    print("=" * 80)
    print(result["text"])
    print("\n" + "=" * 80)
    print(f"Longueur: {len(result['text'])} caractères")
    print(f"Configuration: {result['config']}")

if __name__ == "__main__":
    test_template_tokens()
