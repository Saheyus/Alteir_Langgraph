# Architecture - app/streamlit_app

## Vue d'ensemble

Package modulaire pour l'interface Streamlit du système multi-agents GDD Alteir.
Refactorisation de `app_streamlit.py` (1701 lignes) en 9 modules spécialisés.

## Structure

```
app/streamlit_app/
├── __init__.py       # Exports publics (run_app)
├── app.py            # Point d'entrée, configuration page Streamlit
├── cache.py          # Fonctions de cache (@st.cache_data)
├── constants.py      # Constantes (MODELS, PROFILS, BRIEF_EXAMPLES)
├── creation.py       # Interface de création (formulaire brief + params)
├── generation.py     # Logique de génération de contenu
├── graph.py          # Visualisation de graphes de relations
├── layout.py         # Composants de mise en page réutilisables
└── results.py        # Affichage et export des résultats
```

## Modules

### `app.py` - Point d'entrée principal
**Responsabilité :** Configuration de la page Streamlit, navigation entre tabs

**Fonctions :**
- `run_app()` : Lance l'application, gère les tabs (Créer, Résultats, Graphes)

**Dépendances :**
- `creation.show_creation_form()`
- `results.show_results()`
- `graph.show_graph()`

---

### `cache.py` - Gestion du cache
**Responsabilité :** Fonctions de cache pour optimiser les performances

**Fonctions :**
- `count_output_files()` : Compte les fichiers JSON dans `outputs/`
- `list_output_files()` : Liste les fichiers de résultats triés par date
- `load_result_file(file_stem)` : Charge un fichier JSON de résultat

**Cache Streamlit :** Utilise `@st.cache_data` pour éviter rechargements inutiles

---

### `constants.py` - Constantes de l'application
**Responsabilité :** Définitions centralisées des modèles, profils, exemples

**Constantes principales :**
- `MODELS` : Configuration des modèles LLM (GPT-4, GPT-5, Mistral, Ollama)
- `PROFILS` : Profils prédéfinis par domaine (Personnages/Lieux)
- `BRIEF_EXAMPLES` : Exemples de briefs par domaine
- `BRIEF_PLACEHOLDERS` : Textes d'aide pour les briefs

**Format MODELS :**
```python
{
    "gpt-4o-mini": {
        "name": "GPT-4o Mini",
        "provider": "openai",
        "uses_reasoning": False,
        "icon": "🚀",
        "default_creativity": 0.7
    },
    "gpt-5-nano": {
        "name": "GPT-5 Nano (Reasoning)",
        "provider": "openai", 
        "uses_reasoning": True,
        "icon": "⚡",
        "default_reasoning": "minimal"
    }
}
```

**Format PROFILS :**
```python
{
    "Minimal": {
        "intent": "zone_exploration",
        "level": "site",
        "atmosphere": "neutre",
        "creativity": 0.5
    }
}
```

---

### `creation.py` - Interface de création
**Responsabilité :** Formulaire de création de contenu (brief + paramètres)

**Fonctions :**
- `get_domain_header(domain)` : Retourne l'en-tête selon le domaine
- `show_creation_form()` : Affiche le formulaire complet

**Session State géré :**
- `brief` : Texte du brief utilisateur
- `intent`, `level`, `atmosphere`, `dialogue_mode` : Paramètres narratifs
- `creativity`, `reasoning_effort`, `max_tokens` : Paramètres LLM
- `selected_profile` : Profil prédéfini sélectionné
- `last_domain` : Mémorisation du dernier domaine (reset profil)
- `random_seed` : Compteur pour forcer rerenders

**Features :**
- Brief aléatoire (🎲)
- Profils prédéfinis (Minimal, Standard, Détaillé)
- Randomisation individuelle ou globale des paramètres
- Adaptation automatique selon le modèle (GPT-4 vs GPT-5)

**Callbacks optimisés :** Utilise callbacks `on_click` pour éviter reruns inutiles

---

### `generation.py` - Génération de contenu
**Responsabilité :** Logique de génération via workflow LangGraph

**Fonctions :**
- `generate_content()` : Lance le workflow, sauvegarde résultats, affiche preview

**Workflow :**
1. Validation du brief
2. Création du workflow LangGraph (`ContentWorkflow`)
3. Configuration du contexte (domaine, brief, paramètres)
4. Exécution du workflow multi-agents
5. Sauvegarde JSON + Markdown dans `outputs/`
6. Affichage des métriques (cohérence, complétude, qualité)

**Outputs :**
- `outputs/<domain>_<nom>_<timestamp>.json` : Données complètes
- `outputs/<domain>_<nom>_<timestamp>.md` : Contenu formaté

**Actions post-génération :**
- Export vers Notion (bac à sable)
- Téléchargement JSON persistant

---

### `results.py` - Affichage et export
**Responsabilité :** Visualisation des résultats générés, export Notion

**Fonctions :**
- `export_to_notion(result)` : Exporte vers Notion avec résolution de relations
- `show_results()` : Liste et affiche les résultats sauvegardés

**Export Notion :**
- ✅ Extraction automatique des champs Notion depuis le contenu
- 🔗 Résolution fuzzy des relations (Espèce, Communautés, Alliés, etc.)
- 📊 Statistiques de résolution (resolved/unresolved)
- ⚠️ **BAC À SABLE UNIQUEMENT** (voir `.cursor/rules/export-notion.mdc`)

**Bases bac à sable :**
- Personnages (1) : `2806e4d21b458012a744d8d6723c8be1`
- Lieux (1) : `2806e4d21b4580969f1cd7463a4c889c`

**Affichage résultats :**
- Métriques (cohérence, complétude, qualité)
- Modèle utilisé
- Contenu formaté (Markdown)
- Problèmes identifiés (par sévérité)
- Corrections appliquées
- Métadonnées complètes (JSON)

---

### `graph.py` - Visualisation de graphes
**Responsabilité :** Génération et affichage de graphes de relations

**Fonctions :**
- `create_relation_graph(domain, filter_types)` : Crée graphe NetworkX
- `create_plotly_graph(graph, layout, width, height)` : Visualisation Plotly
- `create_stats_chart(graph)` : Graphique de statistiques
- `show_graph()` : Interface complète de visualisation

**Features :**
- Layouts : spring, circular, hierarchical, kamada-kawai
- Filtrage par type de relations
- Affichage/masquage des labels
- Statistiques du graphe (nœuds, arêtes, densité)

**Dépendances :**
- `agents.relation_graph.RelationGraph`
- NetworkX, Plotly

---

### `layout.py` - Composants de mise en page
**Responsabilité :** Composants UI réutilisables

**Fonctions :**
- `show_header()` : En-tête de l'application
- `show_footer()` : Pied de page avec crédits

**Style :** CSS customisé injecté via `st.markdown(..., unsafe_allow_html=True)`

---

## Flux de Données

### Création de contenu

```
User input (brief + params)
    ↓
creation.show_creation_form()
    ↓ [Bouton "Générer"]
generation.generate_content()
    ↓
ContentWorkflow (LangGraph)
    ↓ [Writer → Reviewer → Corrector → Validator]
Sauvegarde outputs/*.{json,md}
    ↓
Affichage résultats + export
```

### Consultation de résultats

```
results.show_results()
    ↓
cache.list_output_files()
    ↓
User sélection
    ↓
cache.load_result_file(stem)
    ↓
Affichage + actions (Export Notion, Download JSON)
```

### Visualisation de graphes

```
graph.show_graph()
    ↓
create_relation_graph(domain, filters)
    ↓
RelationGraph.build_graph()
    ↓
create_plotly_graph(layout, filters)
    ↓
Affichage interactif
```

## Session State

### Variables clés

| Variable | Type | Usage |
|----------|------|-------|
| `brief` | str | Texte du brief utilisateur |
| `intent` | str | Intention narrative |
| `level` | str | Niveau de détail |
| `atmosphere` | str | Atmosphère (lieux) |
| `dialogue_mode` | str | Mode dialogue (personnages) |
| `creativity` | float | Créativité GPT-4 (0.0-1.0) |
| `reasoning_effort` | str | Effort GPT-5 (minimal/low/medium/high) |
| `max_tokens` | int | Limite tokens (1000-30000) |
| `selected_profile` | str | Profil prédéfini sélectionné |
| `last_domain` | str | Dernier domaine (détection changement) |
| `random_seed` | int | Compteur pour forcer rerenders |

### Initialisation

Chaque variable est initialisée si absente dans `creation.show_creation_form()`.

**Comportement spécial :**
- `selected_profile` : Reset à "Personnalisé" si domaine change
- `intent`, `level` : Reset si domaine change (valeurs par défaut différentes)
- `random_seed` : Incrémenté à chaque randomisation (force rerender)

## Conventions

### Imports
```python
from __future__ import annotations  # Type hints futurs
import streamlit as st
from pathlib import Path
```

### Docstrings
```python
def my_function(param: str) -> dict:
    """Description courte.
    
    Args:
        param: Description
        
    Returns:
        Description du retour
    """
```

### Gestion d'erreurs
```python
try:
    # Opération risquée
except Exception as exc:
    st.error(f"❌ Erreur : {exc}")
    st.exception(exc)  # Traceback détaillé
```

## Migration depuis app_streamlit.py

**Avant (monolithique) :**
- 1 fichier de 1701 lignes
- Toutes responsabilités mélangées
- Difficile à maintenir et tester

**Après (modulaire) :**
- 10 fichiers spécialisés
- Séparation claire des responsabilités
- Point d'entrée de 19 lignes (`app_streamlit.py`)
- Testable individuellement

**Aucune régression fonctionnelle** : Tous les features existants sont préservés.

## Tests

### Compilation
```bash
python -m compileall app/streamlit_app
```

### Import
```python
from app.streamlit_app import run_app
run_app()
```

### Lancement
```bash
streamlit run app_streamlit.py
# ou
python lancer_app.cmd
```

## Dépendances

**Agents :**
- `workflows.content_workflow.ContentWorkflow`
- `agents.relation_graph.RelationGraph`
- `agents.notion_relation_resolver.NotionRelationResolver`

**Librairies :**
- `streamlit` : Interface web
- `plotly` : Graphiques interactifs
- `networkx` : Graphes de relations
- `requests` : API Notion

## Références

- **Workflow principal :** `workflows/content_workflow.py`
- **Configuration domaines :** `config/domain_configs/`
- **Export Notion :** `.cursor/rules/export-notion.mdc`
- **Guide utilisateur :** `GUIDE_UTILISATEUR.md`

## Changelog

### 2025-10-03 - Refactorisation initiale (PR #1)
- Création du package modulaire
- Séparation en 9 modules spécialisés
- Fix brief picker session state
- Fix boutons JSON download
- Fix reset profil lors changement domaine
- Architecture maintenable et testable

