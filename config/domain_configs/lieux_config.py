#!/usr/bin/env python3
"""
Configuration du domaine Lieux
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
LIEUX_SCHEMA = {
    "Nom": "",  # title field
    "Catégorie": "",  # select: Lieu, Région
    "Rôle": "",  # select: Ville, Lieu unique, Lieu militaire, Lieu de culte, Zone magique, Zone naturelle, Lieu commercial, Lieu artisanal
    "Taille": "",  # select: Monde, Pays, Région, District, Secteur, Site, Point d'intérêt
    "Contenu par": [],  # relation vers lieux (parent)
    "Contient": [],  # relation vers lieux (enfants)
    "Zones limitrophes": [],  # relation vers lieux (adjacents)
    "Communautés présentes": [],  # relation vers communautés
    "Personnages présents": [],  # relation vers personnages
    "Faunes & Flores présentes": [],  # relation vers espèces
    "Objets présents": [],  # relation vers objets
    "Scènes": [],  # relation vers scènes
    "Evénements liés": [],  # relation vers chronologie
    "Map": [],  # files
    "État": "Brouillon IA",  # status
    "Sprint": "",  # select
}

# Template narratif Notion pour les lieux
LIEUX_NARRATIVE_TEMPLATE = """
# Résumé du lieu
[Description courte du lieu en 2-3 phrases : essence, fonction, atmosphère]

# Caractéristiques

## Fonction primaire
[Quel est le rôle principal de ce lieu ? Commerce, culte, résidence, passage, etc.]

## Atmosphère dominante
[L'ambiance générale : oppressante, vivante, abandonnée, sacrée, etc.]

## Particularité unique
[Ce qui distingue ce lieu de tous les autres, son élément mémorable]

# Description sensorielle

## Visuel
[Ce qu'on voit : architecture, couleurs, lumière, matériaux]

## Sonore
[Ce qu'on entend : bruits ambiants, sons caractéristiques]

## Olfactif
[Ce qu'on sent : odeurs dominantes, parfums, puanteurs]

## Tactile
[Ce qu'on ressent : température, humidité, textures]

# Structure spatiale

## Zones principales
### [Zone 1]
- **Fonction** : [Usage de cette zone]
- **Accès** : [Comment y accéder]
- **Éléments notables** : [Objets, détails marquants]

### [Zone 2]
- **Fonction** : [Usage de cette zone]
- **Accès** : [Comment y accéder]
- **Éléments notables** : [Objets, détails marquants]

## Points d'intérêt
- [Lieu/objet/élément significatif avec interaction possible]

## Passages et connexions
- **Vers [Lieu A]** : [Comment/où/condition]
- **Vers [Lieu B]** : [Comment/où/condition]

# Histoire du lieu

## Origine
[Comment ce lieu est né, qui l'a créé, pourquoi]

## Évolution
**Passé (WAS)** : [Ce qu'était le lieu autrefois]
**Présent (IS)** : [Ce qu'est le lieu maintenant]
**Potentiel (COULD-BE)** : [Ce que le lieu pourrait devenir]

## Événements marquants
- [Événement historique 1 avec trace visible]
- [Événement historique 2 avec trace visible]

## Traces et stigmates
[Marques physiques du passé : ruines, graffitis, monuments, cicatrices]

# Habitants et présences

## Communautés présentes
- **[Communauté 1]** : [Rôle, quartier, relation au lieu]
- **[Communauté 2]** : [Rôle, quartier, relation au lieu]

## Personnages notables
- **[Personnage 1]** : [Fonction, localisation habituelle]
- **[Personnage 2]** : [Fonction, localisation habituelle]

## Faune & Flore
- [Espèces présentes avec rôle écologique ou narratif]

## Dynamique sociale
[Règles non-écrites, tensions, hiérarchies, tabous du lieu]

# Opportunités narratives

## Actions possibles
- [Action concrète que le joueur peut faire]
- [Interaction avec l'environnement]
- [Découverte ou exploration]

## Quêtes potentielles
- [Objectif lié au lieu]
- [Problème à résoudre]
- [Secret à découvrir]

## Conséquences de présence
- **Si exploration complète** : [Récompense, découverte]
- **Si ignoré** : [Manque, perte d'opportunité]
- **Si profané/détruit** : [Réaction, conséquences]

# Ambiance et détails

## Objets et artefacts
- [Objet notable 1 avec usage/histoire]
- [Objet notable 2 avec usage/histoire]

## Détails immersifs
- [Élément sensoriel ou visuel marquant]
- [Anecdote ou micro-événement observable]

## Dangers et obstacles
- [Péril environnemental ou créature]
- [Contrainte d'accès ou navigation]
"""

# Instructions spécifiques au domaine Lieux
LIEUX_INSTRUCTIONS = """
**PRINCIPES POUR LES LIEUX:**

1. **Spatialité incarnée**: Un lieu n'est pas un décor mais un ACTEUR. Il doit avoir une agency (même passive) : il contraint, révèle, cache, oppose.

2. **Structure : Surface / Profondeur / Monde**:
   - Surface = ce qu'on voit immédiatement (architecture, foule, lumière)
   - Profondeur = ce qu'on découvre (passages secrets, strates historiques, sous-textes)
   - Monde = les forces qui le régissent (économie, écologie, politique)

3. **Temporalité IS / WAS / COULD-BE**: 
   - IS = état présent du lieu
   - WAS = traces visibles du passé (ruines, graffitis, monuments)
   - COULD-BE = potentiel narratif (ce que le lieu pourrait devenir selon les actions)

4. **Échelle et hiérarchie**: Respecter la logique spatiale
   - Monde > Pays > Région > District > Secteur > Site > Point d'intérêt
   - Un lieu "contient" des lieux plus petits
   - Un lieu est "contenu par" un lieu plus grand

5. **Sensoriel > Conceptuel**: Décrire par les sens AVANT d'expliquer
   - Odeurs, sons, textures, lumières PUIS fonction/histoire
   - Montrer les traces physiques du passé (ne pas juste raconter l'histoire)

6. **Opportunités actives**: Chaque lieu doit offrir des ACTIONS concrètes
   - Pas seulement "un temple" mais "un temple où on peut voler une relique, parler au prêtre borgne, ou lire les inscriptions maudites"

7. **Relations spatiales concrètes**: Les connexions doivent être JOUABLES
   - "Passage secret derrière la tapisserie" > "connecté à la chambre"
   - "Pont gardé par deux sentinelles corrompues" > "accès au quartier marchand"

8. **Néologismes contextualisés**: Créer des noms de lieux/zones évocateurs
   - Glose brève (5-8 mots) si le terme est inventé
   - Privilégier les mots qui sonnent et ont du sens dans l'univers
"""

# Instructions spécifiques par rôle
WRITER_INSTRUCTIONS = """
En tant qu'agent écrivain de lieux:
- Créer des lieux mémorables et distincts
- Privilégier le sensoriel et le concret
- Intégrer les contraintes spatiales (taille, hiérarchie, connexions)
- Proposer des opportunités narratives claires (actions, quêtes, découvertes)
- Respecter les relations avec les autres entités (communautés, personnages, événements)
"""

REVIEWER_INSTRUCTIONS = """
En tant qu'agent relecteur de lieux:
- Vérifier la cohérence spatiale (hiérarchie, connexions logiques)
- Valider que le lieu a une "agency" (contraint, révèle, cache)
- Contrôler la présence d'éléments sensoriels (tous les sens si possible)
- S'assurer que les connexions sont JOUABLES (pas juste "lié à")
- Vérifier que les opportunités narratives sont CONCRÈTES
- Valider les relations avec communautés/personnages/objets présents
"""

CORRECTOR_INSTRUCTIONS = """
En tant qu'agent correcteur de lieux:
- Corriger orthographe/grammaire en français
- Améliorer la clarté des descriptions spatiales
- Enrichir les descriptions sensorielles si trop abstraites
- Éviter les clichés de fantasy (le temple mystérieux, la taverne typique)
- Maintenir les néologismes avec leurs gloses
"""

VALIDATOR_INSTRUCTIONS = """
En tant qu'agent validateur de lieux:
- Vérifier la complétude des champs obligatoires (Nom, Catégorie, Rôle, Taille)
- Valider la cohérence de la hiérarchie spatiale (Contenu par / Contient)
- Contrôler que la Taille correspond à la hiérarchie
- S'assurer de la présence d'au moins 3 éléments sensoriels
- Valider qu'il y a au moins 2 actions possibles concrètes
- Vérifier les références croisées (communautés, personnages, objets présents)
"""

# Règles de validation
LIEUX_VALIDATION_RULES = [
    RequiredFieldRule(["Nom", "Catégorie", "Rôle", "Taille", "État"]),
    # CoherenceRule("Taille", "Contenu par"),  # TODO: valider la hiérarchie
    # RelationRule("Communautés présentes", context_source="communautes"),
]

# Sources de contexte Notion
LIEUX_CONTEXT_SOURCES = {
    "communautes": "collection://1886e4d2-1b45-8145-879b-000b236239de",
    "personnages": "collection://1886e4d2-1b45-818c-9937-000b10ce25a0",
    "especes": "collection://1886e4d2-1b45-81dd-9199-000b92800d69",
    "objets": "collection://1886e4d2-1b45-81dc-99d5-000b418446b9",
    "chronologie": "collection://22c6e4d2-1b45-8123-b9cb-000b3a3ecec6",
    "lieux": "collection://1886e4d2-1b45-8163-9932-000bf0d9bccc",  # pour les relations spatiales
}

# Exemples de lieux
LIEUX_EXAMPLES = [
    {
        "brief": "Une bibliothèque souterraine abandonnée qui murmure",
        "result": "Bibliothèque des Échos Morts : archives vivantes sous la ville..."
    },
]

# Options disponibles pour les champs select (basées sur le schéma Notion)
LIEUX_FIELD_OPTIONS = {
    "Catégorie": ["Lieu", "Région"],
    "Rôle": ["Ville", "Lieu unique", "Lieu militaire", "Lieu de culte", "Zone magique", "Zone naturelle", "Lieu commercial", "Lieu artisanal"],
    "Taille": ["Monde", "Pays", "Région", "District", "Secteur", "Site", "Point d'intérêt"],
    "État": ["Pas commencé", "Brouillon IA", "En cours", "À relire", "A implémenter", "Implémenté", "Polished"],
    "Sprint": ["Facultatif", "Plus tard", "Sprint 1", "Sprint 2", "Sprint 3"]
}

# Paramètres spécifiques aux lieux
LIEUX_SPECIFIC_PARAMS = {
    "scale_modes": ["micro", "meso", "macro"],  # échelle de description
    "atmosphere_tags": ["oppressante", "vivante", "sacrée", "corrompue", "abandonnée", "militarisée", "commerciale"],
    "sensory_focus": ["visuel", "sonore", "olfactif", "tactile", "gustatif"],  # sens privilégiés
    "spatial_complexity": ["simple", "moyenne", "complexe", "labyrinthique"],
    "time_layer": ["présent_only", "avec_passé", "full_temporal"],  # profondeur temporelle
}

# Configuration complète du domaine Lieux
LIEUX_CONFIG = DomainConfig(
    domain="lieux",
    display_name="Lieux",
    template=LIEUX_NARRATIVE_TEMPLATE,
    schema=LIEUX_SCHEMA,
    domain_instructions=LIEUX_INSTRUCTIONS,
    validation_rules=LIEUX_VALIDATION_RULES,
    context_sources=LIEUX_CONTEXT_SOURCES,
    examples=LIEUX_EXAMPLES,
    specific_params=LIEUX_SPECIFIC_PARAMS,
    role_specific_prompts={
        "writer": WRITER_INSTRUCTIONS,
        "reviewer": REVIEWER_INSTRUCTIONS,
        "corrector": CORRECTOR_INSTRUCTIONS,
        "validator": VALIDATOR_INSTRUCTIONS,
    }
)

