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

# Schéma des colonnes Notion (pour les métadonnées)
PERSONNAGES_SCHEMA = {
    "Nom": "",  # title field
    "Alias": "",
    "Type": "",  # select: PJ, PNJ, PNJ principal, PNJ recrutable, PNJ secondaire, PNJ historique, Entité supérieure
    "Occupation": "",
    "Espèce": "",  # relation vers collection espèces
    "Âge": 0,  # number
    "Genre": "",  # select: Féminin, Masculin, Non défini, Non Binaire, Pluriel, Zim (incubateur), Fluide, Multimod (ultrafluide)
    "Archétype littéraire": [],  # multi_select: Artiste/Cynique, Amoureuse/Faire-valoir, etc.
    "Axe idéologique": "",  # select: Retrait, Destruction, Rébellion, Connexion, Subversion, Contrôle
    "Qualités": [],  # multi_select: Confiante, Conciliante, Courageuse, etc.
    "Défauts": [],  # multi_select: Autoritaire, Colérique, Cynique, etc.
    "Langage": [],  # multi_select: Abraldique ancien, Principit, Kesh-Varash, etc.
    "Communautés": [],  # relation vers collection communautés
    "Lieux de vie": [],  # relation vers collection lieux
    "Réponse au problème moral": "",
    "État": "Brouillon IA",  # status: Pas commencé, Brouillon IA, En cours, A relire, A implémenter, Implémenté, Polished
    "Sprint": "",  # select: Facultatif, Plus tard, Sprint 1, Sprint 2, Sprint 3
    "Détient": [],  # relation vers collection objets
}

# Template narratif Notion pour les personnages (structure de contenu)
PERSONNAGES_NARRATIVE_TEMPLATE = """
# Résumé de la fiche
[Description générale]

# Caractérisation

## Faiblesse
[Point faible du personnage, ce qui le rend vulnérable]

## Compulsion
[Ce qui le pousse à agir, son moteur interne]

## Désir
[Ce qu'il veut vraiment, son objectif profond]

# Background

## Contexte
[Environnement, situation sociale, position dans le monde]

## Apparence
[Description physique, vêtements, objets portés]

## Évènements marquants
**De sa vie d'enfant :**
- [3-5 Événements significatifs]
**De sa vie d'ado :**
- [3-5 Événements significatifs]
**De sa vie d'adulte :**
- [3-5 Événements significatifs]

## Relations
**À sa famille :**
- [Relations familiales avec enjeu concret]
**Aux autres :**
- [Relations avec prix/dette/délai/tabou]

## Centres d'intérêt
- [Passions, hobbies, domaines d'expertise]

## Fluff
- [Détails colorés, anecdotes, particularités]

# Arcs Narratifs

## Actions concrètes
[Ce que le personnage fait activement dans l'histoire]

## Quêtes annexes
[Missions secondaires, objectifs à court terme]

## Conséquences de la Révélation
- **Si besoin résolu :** [État final positif]
- **Si besoin non résolu :** [État final négatif]
- **Si le besoin empire :** [État final critique]

# Dialogue Type

## [Thème] du jeu
[Comment le personnage aborde le thème central]

## Registre de langage du personnage
[Niveau de langue, style de communication]

## Champs lexicaux utilisés
[Mots-clés, domaines de vocabulaire privilégiés]

## Expressions courantes
- [Phrases typiques du personnage]

# Dialogue du personnage

## Rencontre initiale
[Première impression, accroche]

## Exemples de dialogues
[8-10 répliques variées de 10-20 mots chacune]
"""

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

# Options disponibles pour les champs select/multi_select (basées sur le schéma Notion)
PERSONNAGES_FIELD_OPTIONS = {
    "Type": ["PJ", "PNJ", "PNJ principal", "PNJ recrutable", "PNJ secondaire", "PNJ historique", "Entité supérieure"],
    "Genre": ["Féminin", "Masculin", "Non défini", "Non Binaire", "Pluriel", "Zim (incubateur)", "Fluide", "Multimod (ultrafluide)"],
    "Archétype littéraire": ["Artiste / Cynique", "Amoureuse / Faire-valoir", "Magicienne / Sorcier", "Rebelle / Destructeur", "Guerrière / Surhomme", "Friponne / Menteur", "Mentor / Gourou", "Reine / Tyran"],
    "Axe idéologique": ["Retrait", "Destruction", "Rébellion", "Connexion", "Subversion", "Contrôle"],
    "Qualités": ["Confiante", "Conciliante", "Courageuse", "Décent", "Détachée", "Diplomate", "Discrète", "Empathique", "Energique", "Fiable", "Généreuse", "Honnête", "Humble", "Ingénieuse", "Lucide", "Idéaliste", "Loyale", "Modeste", "Organisée", "Ouverte", "Patiente", "Persévérante", "Posée", "Prudente", "Rigoureuse", "Respectueuse", "Responsable", "Sincère", "Tempérée", "Tolérante"],
    "Défauts": ["Autoritaire", "Colérique", "Cynique", "Manipulatrice", "Obstinée", "Désordonnée", "Égoïste", "Incompétent", "Provocatrice", "Prétentieuse", "Insensible", "Défaitiste", "Irresponsable", "Intolérante", "Indiscrète", "Imprudente", "Irrespectueuse", "Impatiente", "Instable", "Lâche", "Malhonnête", "Méfiante", "Naïve", "Négligente", "Orgueilleuse", "Paresseuse", "Sensuelle", "Susceptible", "Traîtresse"],
    "Langage": ["Abraldique ancien", "Principit", "Kesh-Varash", "Néo-Frémissant", "Langage vertebral", "Mécanaqueux", "Acqueux", "Abyssal"],
    "État": ["Pas commencé", "Brouillon IA", "En cours", "A relire", "A implémenter", "Implémenté", "Polished"],
    "Sprint": ["Facultatif", "Plus tard", "Sprint 1", "Sprint 2", "Sprint 3"]
}

# Paramètres spécifiques aux personnages (techniques uniquement)
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
    template=PERSONNAGES_NARRATIVE_TEMPLATE,  # Template narratif
    schema=PERSONNAGES_SCHEMA,  # Schéma de colonnes
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

