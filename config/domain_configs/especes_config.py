#!/usr/bin/env python3
"""
Configuration du domaine Espèces
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.base.domain_config import (
    DomainConfig,
    RequiredFieldRule,
    CoherenceRule,
    RelationRule,
)

# Schéma des colonnes Notion (pour les métadonnées)
ESPECES_SCHEMA = {
    "Nom": "",  # title field
    "Type": "",  # select: Espèce, Sous-espèce, Entité
    "Morphologie": "",  # select / rich_text (selon base finale)
    "Habitat": "",  # select: Biome / Environnement dominant
    "Comportement": "",  # select
    "Intelligence": "",  # select: Instinctive, Sociale, Sophistiquée, Transcendante
    "Communication": "",  # select: Gestuelle, Vocale, Télépathique, Chimique, Rituelle
    "Faiblesses": [],  # multi_select
    "Rang trophique": "",  # select: Détritivore, Herbivore, Omnivore, Prédateur, Apex
    "Aire de répartition": [],  # relation vers lieux
    "Communautés associées": [],  # relation vers communautés
    "Spécimens notables": [],  # relation vers personnages
    "État": "Brouillon IA",  # status
}

# Template narratif Notion pour les espèces (structure de contenu)
ESPECES_NARRATIVE_TEMPLATE = """
# Résumé de l'espèce
[Description synthétique, traits distinctifs, niche écologique]

# Biologie & Morphologie
## Anatomie
[Forme, organes spécifiques, variations, dimorphisme]
## Capacités
[Forces, aptitudes particulières, limites]

# Écologie
## Habitat naturel
[Biomes, conditions requises, zones d'occurrence]
## Cycle de vie
[Reproduction, croissance, longévité, métamorphoses]
## Interactions
[Prédation, symbioses, parasitisme, coévolutions]

# Comportement & Culture
## Structure sociale
[Solitaire, meute, ruche, clan, caste]
## Communication
[Canaux, codes, rituels]
## Artefacts/Traces
[Objets, constructions, empreintes dans le monde]

# Relations avec le monde d'Alteir
## Lieux clés
[Zones de présence, sanctuaires, territoires]
## Communautés impliquées
[Groupes qui protègent, exploitent ou vénèrent l'espèce]
## Figures notables
[Individus marquants, mythes, légendes]
"""

# Instructions spécifiques au domaine Espèces
ESPECES_INSTRUCTIONS = """
Rappels pour les espèces:
- Décrire par indices concrets (empreintes, outils, sécrétions) avant l'explication.
- Toujours relier l'espèce à un habitat, une ressource et une contrainte.
- Montrer des comportements observables et leurs déclencheurs (odeur, lumière, cycles).
- Penser interactions: proies, prédateurs, symbioses, parasites, humains.
"""

WRITER_INSTRUCTIONS = """
En tant qu'agent écrivain d'espèces:
- Rendre l'espèce MEMORABLE par 1-2 mécanismes clairs
- Conserver une cohérence écologique (ressource ↔ comportement ↔ morphologie)
- Décrire des scènes observables (trace, rituel, chasse, soin)
"""

REVIEWER_INSTRUCTIONS = """
En tant qu'agent relecteur d'espèces:
- Valider cohérence biologie ↔ habitat ↔ comportement
- Vérifier présence d'interactions claires avec lieux/communautés/personnages
- Éviter anthropocentrisme gratuit (garder l'altérité)
"""

CORRECTOR_INSTRUCTIONS = """
En tant qu'agent correcteur d'espèces:
- Clarifier descriptions anatomiques et écologiques
- Maintenir sobriété du style, gloses brèves pour néologismes
"""

VALIDATOR_INSTRUCTIONS = """
En tant qu'agent validateur d'espèces:
- Champs requis présents (Nom, Type, Habitat, Intelligence, État)
- Au moins 1 lieu référencé ou un habitat précis
- Pas de contradiction majeure avec le contexte Notion
"""

# Règles de validation
ESPECES_VALIDATION_RULES = [
    RequiredFieldRule(["Nom", "Type", "Habitat", "Intelligence", "État"]),
    # RelationRule("Aire de répartition", context_source="lieux"),
]

# Sources de contexte Notion (cross-ref)
ESPECES_CONTEXT_SOURCES = {
    "lieux": "collection://1886e4d2-1b45-81e5-aaaa-000bcccccccc",
    "communautes": "collection://1886e4d2-1b45-8145-879b-000b236239de",
    "personnages": "collection://1886e4d2-1b45-818c-9937-000b10ce25a0",
}

ESPECES_EXAMPLES = [
    {
        "brief": "Grand prédateur photophore des forêts de corail",
        "result": "Kephrasite nocturne : cuirasse translucide, traque à pulsations lumineuses...",
    }
]

ESPECES_SPECIFIC_PARAMS = {
    "level_options": ["simple", "standard", "detail"],
}

ESPECES_CONFIG = DomainConfig(
    domain="especes",
    display_name="Espèces",
    template=ESPECES_NARRATIVE_TEMPLATE,
    schema=ESPECES_SCHEMA,
    domain_instructions=ESPECES_INSTRUCTIONS,
    validation_rules=ESPECES_VALIDATION_RULES,
    context_sources=ESPECES_CONTEXT_SOURCES,
    examples=ESPECES_EXAMPLES,
    specific_params=ESPECES_SPECIFIC_PARAMS,
    role_specific_prompts={
        "writer": WRITER_INSTRUCTIONS,
        "reviewer": REVIEWER_INSTRUCTIONS,
        "corrector": CORRECTOR_INSTRUCTIONS,
        "validator": VALIDATOR_INSTRUCTIONS,
    },
)



