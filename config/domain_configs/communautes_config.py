#!/usr/bin/env python3
"""
Configuration du domaine Communautés
"""

import sys
from pathlib import Path

# Allow imports from project root when executed directly
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.base.domain_config import (  # noqa: E402
    DomainConfig,
    RequiredFieldRule,
    CoherenceRule,
    RelationRule,
)


# Schéma des colonnes Notion (pour les métadonnées)
# Aligné sur la base Communautés (lecture seule) actuelle
# Source (MCP): collection://1886e4d2-1b45-8145-879b-000b236239de
COMMUNAUTES_SCHEMA = {
    "Nom": "",  # title
    "État": "Brouillon IA",  # status: Pas commencé, Brouillon IA, En cours, A implémenter, Implémenté, Polished
    "Sprint": "",  # select: Facultatif, Plus tard, Sprint 1, Sprint 2, Sprint 3
    "Démographie": "",  # select: 1 à 10, 11 à 30, ..., + de 10 000
    "Condition de vie": "",  # select: Mauvaise, Passable, Bonne, Parfaite
    "Niveau d'éducation": "",  # select: Aucun, Faible, Moyen, Important, Avancé
    "Lieux de vie": [],  # relation → Lieux
    "Personnages présents": [],  # relation → Personnages
    "Objets créés": [],  # relation → Objets
    "Dates majeures": [],  # relation → Chronologie
}


# Template narratif Notion pour les communautés (structure de contenu)
COMMUNAUTES_NARRATIVE_TEMPLATE = """
# Résumé de la communauté
[Description synthétique : rôle, méthodes, ancrage]

# Besoin de l’intrigue
## Origine
[2–3 faits marquants (WAS) + objet/lieu-témoin concret]
## Histoire
[Événements structurants, scissions, dettes fondatrices]
## Trajectoires possibles (COULD)
[2–3 évolutions conditionnelles selon actions du joueur]

# Identité & Gouvernance
## Gouvernance & pouvoirs
[Mode de décision, succession, sanctions, contre-pouvoirs]
## Slogan / dicton
[1 phrase réellement utilisée en scène]
## Tabou principal
[Interdit + effet observable en cas de transgression]
## Membres notables
[2–3 profils: rôle, contradiction, geste-signature]

# Objectifs & Méthodes
## Objectif principal (+ secondaires)
[Formulé opérationnellement, mesurable dans le monde]
## Méthodes privilégiées
[Ce qu’ils font concrètement: troc, soin, espionnage, rituel…]
## Ressources clés
[Ce qui rend l’action possible: archives, artefacts, réseau…]
## Indicateurs de réussite/échec
[Signes visibles in‑world]

# Territoires & Accès
## Lieux d’influence
[2–4 zones actives + portes d’entrée]
## Contrôle vs contestation
[Qui y a droit, à quel prix/délai/tabou]

# Relations extérieures
## Alliances (pactes/dettes/échéances)
[Contreparties claires et datées]
## Rivalités (motifs/terrains de friction)
[Conflits localisés et jouables]

# Culture & Signes matériels
## Valeurs & éthique
[Conflits internes tolérés/interdits]
## Esthétique & architecture
[Marques, vêtements, architectures-signatures]
## Subsistance & logistique
[Produire/importer; contraintes de flux]
## Créations majeures
[Artisanales/industrielles/artistiques]

# Implémentations concrètes
## Hooks concrets (5–7)
- [Action] — Prérequis | Prix/Dette | Risque
## Indices du monde (traces)
- [Indice/objet/rumeur/signaux] — Où le voir / comment l’obtenir *5
## Lexique (néologismes)
- [Terme] — [Glose] *3-8
"""


# Instructions spécifiques au domaine Communautés
COMMUNAUTES_INSTRUCTIONS = """
Principes pour les communautés:

1. Montrer des pratiques observables avant d'expliquer la doctrine.
2. Préférer dettes/pactes/rituels à des idéaux vagues : chaque lien engage.
3. Toujours relier Objectif ↔ Méthodes ↔ Ressource clé (cohérence opératoire).
4. Territoire actif: un lieu n'est pas décor; il contraint et révèle des usages.
5. Blancs actifs: tout non-dit ouvre une action possible (parler à X, voler Y).
6. Langue concrète: éviter slogans, privilégier signes, gestes, objets, délais.
"""


# Instructions spécifiques par rôle
WRITER_INSTRUCTIONS = """
En tant qu'agent écrivain de communautés:
- Définir un objectif clair ET des méthodes vérifiables sur le terrain
- Ancrer la communauté dans des lieux, avec rituels et signes matériels
- Décrire dettes/pactes/échanges qui créent des leviers narratifs
- Éviter les abstractions générales; donner des indices et actions jouables
"""

REVIEWER_INSTRUCTIONS = """
En tant qu'agent relecteur de communautés:
- Vérifier cohérence Objectif ↔ Méthodes ↔ Ressource clé
- Contrôler présence de lieux d'influence et de relations concrètes
- Exiger des actions jouables (pas seulement une doctrine)
- Identifier tabous/codes réellement opérants dans les scènes
"""

CORRECTOR_INSTRUCTIONS = """
En tant qu'agent correcteur de communautés:
- Clarifier les termes rituels et les gloses (5-8 mots)
- Alléger l'abstraction, renforcer concrétude et précision
- Maintenir le style cru sans esthétisation des violences
"""

VALIDATOR_INSTRUCTIONS = """
En tant qu'agent validateur de communautés:
- Champs requis présents (Nom, État)
- Au moins 1 relation utile (Lieux de vie, Personnages présents ou Dates majeures)
- Valeurs cohérentes pour Démographie / Condition de vie / Niveau d'éducation si renseignées
- Références croisées valides avec lieux/personnages/objets existants
"""


# Règles de validation (minimum viables pour export sur la base actuelle)
COMMUNAUTES_VALIDATION_RULES = [
    RequiredFieldRule(["Nom", "État"]),
    # RelationRule("Lieux de vie", context_source="lieux"),
]


# Sources de contexte Notion (cross-ref)
COMMUNAUTES_CONTEXT_SOURCES = {
    "lieux": "collection://1886e4d2-1b45-8163-9932-000bf0d9bccc",
    "personnages": "collection://1886e4d2-1b45-818c-9937-000b10ce25a0",
    "communautes": "collection://1886e4d2-1b45-8145-879b-000b236239de",
    "especes": "collection://1886e4d2-1b45-81dd-9199-000b92800d69",
}


# Exemples
COMMUNAUTES_EXAMPLES = [
    {
        "brief": "Confrérie cellulaire pratiquant le soin discret contre serment de sel",
        "result": "Confrérie des Albes: cellules de trois, rituel d'initiation au sel, réseaux d'herboristes...",
    }
]


# Paramètres spécifiques au domaine (techniques)
COMMUNAUTES_SPECIFIC_PARAMS = {
    "intent_modes": ["influence_locale", "réseau_occulté", "ordre_dominant"],
    "level_options": ["cellule", "chapitre", "ordre"],
}


# Configuration complète du domaine Communautés
COMMUNAUTES_CONFIG = DomainConfig(
    domain="communautes",
    display_name="Communautés",
    template=COMMUNAUTES_NARRATIVE_TEMPLATE,
    schema=COMMUNAUTES_SCHEMA,
    domain_instructions=COMMUNAUTES_INSTRUCTIONS,
    validation_rules=COMMUNAUTES_VALIDATION_RULES,
    context_sources=COMMUNAUTES_CONTEXT_SOURCES,
    examples=COMMUNAUTES_EXAMPLES,
    specific_params=COMMUNAUTES_SPECIFIC_PARAMS,
    role_specific_prompts={
        "writer": WRITER_INSTRUCTIONS,
        "reviewer": REVIEWER_INSTRUCTIONS,
        "corrector": CORRECTOR_INSTRUCTIONS,
        "validator": VALIDATOR_INSTRUCTIONS,
    },
)


