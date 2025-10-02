#!/usr/bin/env python3
"""
Configuration du domaine Personnages
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.base.domain_config import (
    DomainConfig, 
    RequiredFieldRule, 
    CoherenceRule,
    RelationRule
)

# Template Notion pour les personnages
PERSONNAGES_TEMPLATE = {
    "Nom": "",
    "Alias": "",
    "Type": "",  # PJ, PNJ, PNJ principal, etc.
    "Occupation": "",
    "Espèce": "",
    "Âge": 0,
    "Genre": "",
    "Archétype littéraire": [],
    "Axe idéologique": "",
    "Qualités": [],
    "Défauts": [],
    "Langage": [],
    "Communautés": [],
    "Lieux de vie": [],
    "Réponse au problème moral": "",
    "État": "Brouillon IA"
}

# Instructions spécifiques au domaine Personnages
PERSONNAGES_INSTRUCTIONS = """
**PRINCIPES POUR LES PERSONNAGES:**

1. **Orthogonalité rôle ↔ profondeur**: La profondeur du personnage ne doit PAS être explicable par son rôle visible seul (sauf indication contraire via intent).

2. **Structure Surface / Profondeur / Monde**:
   - Surface = gestes, objets, micro-règles, répliques brèves SANS backstory
   - Profondeur = indices, artefacts, témoins, lieux, analepses par strates
   - Monde = contraintes institutionnelles/écologiques/économiques

3. **Temporalité IS / WAS / COULD-HAVE-BEEN**: Montrer le présent, un passé concret, ET une voie non empruntée.

4. **Show > Tell**: Privilégier objets, rituels, silences, traces. Réserver l'exposition directe aux rubriques qui l'exigent.

5. **Blancs actifs**: Toute zone d'ombre ouvre une ACTION (parler à X, aller à Y, utiliser Z).

6. **Relations avec enjeux concrets**: Chaque relation doit avoir un prix, une dette, un délai ou un tabou.

7. **Dialogues variés et jouables**: 8-10 répliques de 10-20 mots, sans backstory.
"""

# Instructions spécifiques par rôle
WRITER_INSTRUCTIONS = """
En tant qu'agent écrivain de personnages:
- Créer des personnages cohérents avec l'univers Alteir
- Respecter la structure Caractérisation / Dialogue / Background / Relations / Arcs / Chronologie
- Intégrer les néologismes avec glose brève (5-8 mots) si nécessaire
- Éviter les archétypes omniprésents et l'exposition torrentielle
"""

REVIEWER_INSTRUCTIONS = """
En tant qu'agent relecteur de personnages:
- Vérifier l'orthogonalité rôle ↔ profondeur
- Valider la séparation Surface/Profondeur
- Contrôler la cohérence avec les autres entités (espèces, lieux, communautés)
- Vérifier que chaque relation a un enjeu concret
- S'assurer que les "blancs actifs" ouvrent des actions
"""

CORRECTOR_INSTRUCTIONS = """
En tant qu'agent correcteur de personnages:
- Corriger orthographe/grammaire en français
- Améliorer la clarté sans perdre la richesse
- Respecter le style cru mais non esthétisant pour les violences
- Éviter les anglicismes non nécessaires
- Maintenir les néologismes avec leurs gloses
"""

VALIDATOR_INSTRUCTIONS = """
En tant qu'agent validateur de personnages:
- Vérifier la complétude des champs obligatoires
- Valider les références croisées (espèces, lieux, communautés existants)
- Contrôler la cohérence chronologique (âge, événements, dates)
- S'assurer de la présence d'au moins 1 artefact OU 1 témoin OU 1 lieu actif
- Valider que le personnage respecte les contraintes du domaine
"""

# Règles de validation
PERSONNAGES_VALIDATION_RULES = [
    RequiredFieldRule(["Nom", "Type", "Espèce", "État"]),
    # CoherenceRule("Âge", "Chronologie"),  # TODO: implémenter validator custom
    # RelationRule("Communautés", context_source="communautes"),
    # RelationRule("Espèce", context_source="especes"),
    # RelationRule("Lieux de vie", context_source="lieux"),
]

# Sources de contexte Notion
PERSONNAGES_CONTEXT_SOURCES = {
    "communautes": "collection://1886e4d2-1b45-8145-879b-000b236239de",
    "especes": "collection://1886e4d2-1b45-81dd-9199-000b92800d69",
    "lieux": "collection://1886e4d2-1b45-8163-9932-000bf0d9bccc",
    "chronologie": "collection://2226e4d2-1b45-8059-830f-000b8e38619e",
}

# Exemples de personnages
PERSONNAGES_EXAMPLES = [
    {
        "brief": "Un cartographe solitaire qui cache une autre vocation",
        "result": "Cartographe mystérieuse membre d'un culte ancien..."
    },
    # Ajouter plus d'exemples ici
]

# Paramètres spécifiques aux personnages
PERSONNAGES_SPECIFIC_PARAMS = {
    "intent_modes": ["orthogonal_depth", "vocation_pure", "archetype_assume", "mystere_non_resolu"],
    "dialogue_modes": ["parle", "gestuel", "telepathique", "ecrit_only"],
    "level_options": ["cameo", "standard", "major"],
    "calendar_spec": "cycles",  # ou "fragments", "ères"
    "inspiration_modes": ["off", "lite", "full"],
    "figures_preferences": ["métaphore", "oxymore", "synesthésie", "hypallage", "prosopopée"]
}

# Configuration complète du domaine Personnages
PERSONNAGES_CONFIG = DomainConfig(
    domain="personnages",
    display_name="Personnages",
    template=PERSONNAGES_TEMPLATE,
    domain_instructions=PERSONNAGES_INSTRUCTIONS,
    validation_rules=PERSONNAGES_VALIDATION_RULES,
    context_sources=PERSONNAGES_CONTEXT_SOURCES,
    examples=PERSONNAGES_EXAMPLES,
    specific_params=PERSONNAGES_SPECIFIC_PARAMS,
    role_specific_prompts={
        "writer": WRITER_INSTRUCTIONS,
        "reviewer": REVIEWER_INSTRUCTIONS,
        "corrector": CORRECTOR_INSTRUCTIONS,
        "validator": VALIDATOR_INSTRUCTIONS,
    }
)

