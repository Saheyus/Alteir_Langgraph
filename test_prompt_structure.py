#!/usr/bin/env python3
"""Test de la structure du prompt"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from agents.writer_agent import WriterAgent
from config.domain_configs.personnages_config import PERSONNAGES_CONFIG

agent = WriterAgent(PERSONNAGES_CONFIG)
prompt = agent._build_prompt('Test', {})

print('=== VERIFICATION STRUCTURE PROMPT ===\n')
print('[OK] Template narratif present:', '# Résumé' in prompt)
print('[OK] Caracterisation presente:', '# Caractérisation' in prompt)
print('[OK] Background present:', '# Background' in prompt)
print('[OK] Champs Notion presents:', '**CHAMPS NOTION' in prompt)

print(f'\nLongueur totale: {len(prompt)} caractères')

print('\n=== APERÇU CHAMPS NOTION ===\n')
# Extraire la section champs Notion
if '**CHAMPS NOTION' in prompt:
    start = prompt.index('**CHAMPS NOTION')
    section = prompt[start:start+800]
    print(section)

