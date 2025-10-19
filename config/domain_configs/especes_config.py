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
# Aligné sur la base Espèces (1) — sandbox
# Source (MCP): collection://28d6e4d2-1b45-8104-ba48-000b7bbf8207
ESPECES_SCHEMA = {
    "Nom": "",  # title
    "État": "Pas commencé",  # status: Pas commencé, En cours, A implémenter, Implémenté, Polished
    "Type": "",  # select: Espèce civilisée, Faune, Flore, Autre
    "Présence dans Escelion": "",  # select: Unique, Rare, Courant, etc.
    "Biologie": "",  # select: Avancée, Moyenne, Faible, Nulle
    "Culture": "",  # select: Avancée, Moyenne, Faible, Nulle
    "Surnaturel": "",  # select: Avancée, Moyenne, Faible, Nulle
    "Technologie": "",  # select: Avancée, Moyenne, Faible, Nulle
    "Espérance de vie": 0.0,  # number
    "Lieux de vie": [],  # relation → Lieux
    "Représentants": [],  # relation → Personnages
    "Références visuelles": [],  # relation (assets)
    "Evénements liés": [],  # relation → Chronologie
    "Règne": [],  # relation (single) vers taxonomie
    "Sprint": "",  # select
}

# Template narratif Notion pour les espèces (structure de contenu)
ESPECES_NARRATIVE_TEMPLATE = """
# Résumé de l'espèce
[Description synthétique, traits distinctifs, niche écologique]

# Biologie & Capacités
## Biologie
[Fonctionnement, contraintes, adaptations]  
## Capacités
[Forces, limites, coûts]

# Écologie
## Présence dans Escelion
[Distribution: Unique/Rare/Peu courant/Courant/Très courant/Endémique/Invasif]  
## Lieux de vie
[Zones, habitats, conditions requises]

# Culture & Signe de l'espèce
## Culture
[Rituels, transmissions, symboles]
## Surnaturel / Technologie
[Degré, manifestations, artefacts]

# Relations & Figures
## Représentants
[2–3 individus ou lignées notables]
## Événements liés
[Moments clés, interactions avec l'histoire]

# Indices du monde
## Traces observables
[Objets, empreintes, architectures, chants]
"""

# Instructions spécifiques au domaine Espèces
ESPECES_INSTRUCTIONS = """
Rappels pour les espèces:
- Décrire par indices concrets (empreintes, outils, sécrétions) avant l'explication.
- Ancrer la présence (où, à quel coût) et les lieux de vie.
- Utiliser les catégories de la base (Biologie/Culture/Surnaturel/Technologie) quand pertinentes.
- Penser interactions: lieux, personnages (représentants), événements.
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
- Champs requis présents (Nom, État)
- Valeurs cohérentes pour Type / Présence / Biologie / Culture si renseignées
- Lieux de vie et Représentants optionnels mais validés si fournis
"""

# Règles de validation (alignées sur la base sandbox)
ESPECES_VALIDATION_RULES = [
    RequiredFieldRule(["Nom", "État"]),
    # RelationRule("Lieux de vie", context_source="lieux"),
]

# Sources de contexte Notion (cross-ref)
ESPECES_CONTEXT_SOURCES = {
    "lieux": "collection://1886e4d2-1b45-8163-9932-000bf0d9bccc",
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



