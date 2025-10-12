# Tests End-to-End (E2E) - Système Multi-Agents

Documentation complète des tests E2E pour le système multi-agents GDD Alteir.

---

## 📋 Vue d'Ensemble

Les tests E2E valident le **workflow complet** :  
`Brief → Writer → Reviewer → Corrector → Validator → Export Notion`

### Structure des Tests

```
tests/
├── conftest.py                         # Fixtures partagées
├── run_e2e_tests.py                    # Script runner pratique
│
├── test_e2e_workflow_personnage.py     # E2E personnages (basique + profils)
├── test_e2e_workflow_with_context.py   # E2E avec contexte Notion
├── test_e2e_error_handling.py          # Gestion d'erreurs
│
├── test_writer_agent.py                # Tests WriterAgent (unit + integration)
├── test_structured_outputs_agents.py   # Tests structured outputs
│
├── test_notion_api.py                  # Tests API Notion consolidés
├── test_export_integration.py          # Tests export (existants)
└── README_E2E_TESTS.md                 # Cette documentation
```

---

## 🚀 Exécution Rapide

### Tests Rapides (Recommandé pour Dev)
```bash
# Unitaires uniquement (< 2 secondes)
python tests/run_e2e_tests.py quick
```

### Tests E2E Basiques
```bash
# E2E simples (~ 1 minute)
python tests/run_e2e_tests.py e2e-basic
```

### Tests E2E Complets
```bash
# Tous les E2E (~ 2-3 minutes)
python tests/run_e2e_tests.py e2e-only
```

### Suite Complète
```bash
# Tous les tests (~ 3-5 minutes)
python tests/run_e2e_tests.py full
```

---

## 📊 Types de Tests E2E

### 1. **test_e2e_workflow_personnage.py** ⚡ E2E Core

**Objectif** : Tester le workflow complet pour personnages

#### Tests Inclus

##### `TestE2EWorkflowPersonnageBasic`
- `test_e2e_personnage_minimal` : Workflow basique sans export
- `test_e2e_personnage_with_notion_export` : Workflow + export Notion sandbox

##### `TestE2EWorkflowLieu`
- `test_e2e_lieu_minimal` : Workflow complet pour un lieu

##### `TestE2EWriterProfiles`
- `test_e2e_orthogonal_depth` : Profil orthogonal_depth + major
- `test_e2e_vocation_pure` : Profil vocation_pure + supporting
- `test_e2e_mystere_non_resolu` : Profil mystere_non_resolu + minor

**Assertions** :
- ✅ Chaque agent retourne `success=True`
- ✅ Scores > seuils (coherence, completeness, quality)
- ✅ Page Notion créée avec propriétés correctes
- ✅ Outputs JSON + MD sauvegardés

**Temps** : ~30-60 secondes par test  
**Coût** : ~$0.005-0.01 par test (GPT-4o-mini)

**Exécution** :
```bash
# Tous les tests personnage
pytest tests/test_e2e_workflow_personnage.py -v -s

# Un test spécifique
pytest tests/test_e2e_workflow_personnage.py::TestE2EWorkflowPersonnageBasic::test_e2e_personnage_minimal -v -s
```

---

### 2. **test_e2e_workflow_with_context.py** 🔗 E2E Contexte

**Objectif** : Tester workflow avec récupération de contexte Notion

#### Tests Inclus

##### `TestE2EWorkflowWithContext`
- `test_e2e_with_communaute_context` : Référence "Les Murmurateurs"
- `test_e2e_with_lieu_context` : Référence "La Vieille Ville"
- `test_e2e_with_espece_context` : Référence "Humain modifié"
- `test_e2e_with_multi_context` : Références multiples (communauté + lieu + espèce)

##### `TestE2EContextCache`
- `test_context_cache_performance` : Vérifier accélération cache (2x minimum)

**Assertions** :
- ✅ Contexte récupéré depuis Notion
- ✅ Références présentes dans le contenu généré
- ✅ Relations Notion correctement définies
- ✅ Cache améliore performances (speedup > 2x)

**Temps** : ~60-90 secondes par test  
**Coût** : ~$0.01-0.02 par test

**Exécution** :
```bash
# Tous les tests contexte
pytest tests/test_e2e_workflow_with_context.py -v -s

# Test cache uniquement
pytest tests/test_e2e_workflow_with_context.py::TestE2EContextCache -v -s
```

---

### 3. **test_e2e_error_handling.py** ⚠️ Gestion d'Erreurs

**Objectif** : Tester résilience et gestion d'erreurs

#### Tests Inclus

##### `TestE2EErrorHandling`
- `test_e2e_brief_vide` : Brief vide → erreur claire
- `test_e2e_brief_trop_court` : Brief vague → score complétude bas
- `test_e2e_validation_failed_no_export` : Validation échouée → pas d'export
- `test_e2e_notion_api_error_simulation` : Erreur API Notion → message clair

##### `TestE2EResilience`
- `test_e2e_contenu_incomplet_detection` : Détection champs manquants
- `test_e2e_workflow_state_consistency` : État workflow cohérent

**Assertions** :
- ✅ Erreurs détectées proprement (pas de crash)
- ✅ Messages d'erreur clairs
- ✅ État workflow reste cohérent
- ✅ Validation bloque export si invalide

**Temps** : ~10-30 secondes par test (certains rapides)  
**Coût** : ~$0.005 par test

**Exécution** :
```bash
# Tous les tests erreurs
pytest tests/test_e2e_error_handling.py -v -s
```

---

### 4. **test_writer_agent.py** ✍️ Tests WriterAgent

**Objectif** : Tester WriterAgent isolément

#### Tests Inclus

##### `TestWriterAgentBasic`
- `test_writer_generate_personnage` : Génération personnage basique
- `test_writer_generate_lieu` : Génération lieu basique

##### `TestWriterAgentFormat`
- `test_writer_markdown_structure_personnage` : Vérifier structure markdown
- `test_writer_markdown_structure_lieu` : Vérifier sections lieu

##### `TestWriterAgentConfig`
- `test_writer_orthogonal_depth` : Config orthogonal_depth
- `test_writer_vocation_pure` : Config vocation_pure
- `test_writer_mystere_non_resolu` : Config mystere_non_resolu

##### `TestWriterAgentWithContext`
- `test_writer_with_notion_context` : Génération avec contexte
- `test_writer_without_context` : Génération sans contexte (baseline)

**Assertions** :
- ✅ Contenu généré > 100 caractères
- ✅ Structure markdown valide
- ✅ Champs essentiels présents
- ✅ Métadonnées complètes (intent, level, dialogue_mode)

**Temps** : ~15-30 secondes par test  
**Coût** : ~$0.003-0.005 par test

**Exécution** :
```bash
# Tous les tests WriterAgent
pytest tests/test_writer_agent.py -v -s

# Tests config uniquement
pytest tests/test_writer_agent.py::TestWriterAgentConfig -v -s
```

---

## ⚙️ Configuration

### Prérequis

1. **Variables d'environnement** (fichier `.env`)
```bash
NOTION_TOKEN=secret_...
OPENAI_API_KEY=sk-...
```

2. **Dépendances installées**
```bash
pip install -r requirements.txt
```

3. **Accès bases Notion**
   - **Sandbox** (écriture) : Personnages (1), Lieux (1)
   - **Principales** (lecture) : Personnages, Lieux, Communautés, Espèces

### Fixtures Partagées (`conftest.py`)

- `notion_token` : Token Notion (skip si absent)
- `notion_headers` : Headers pour API Notion
- `sandbox_databases` : IDs des bases sandbox
- `main_databases` : IDs des bases principales
- `test_llm` : LLM configuré (GPT-4o-mini)
- `test_llm_fast` : LLM rapide (tokens réduits)
- `notion_page_tracker` : Cleanup automatique des pages créées
- `temp_output_dir` : Répertoire temporaire pour outputs
- `sample_brief_personnage` : Brief test personnage
- `sample_brief_lieu` : Brief test lieu

---

## 🎯 Stratégie de Test

### Pyramide de Tests

```
         🔺 E2E (lents, coûteux)
        /    \
       /      \  
      / Intég  \
     /   (API)  \
    /____________\
   Unit (rapides)
```

### Quand Lancer Quels Tests ?

#### Développement Actif
```bash
# Tests rapides à chaque changement
python tests/run_e2e_tests.py quick
```

#### Avant Commit Local
```bash
# E2E basiques pour validation rapide
python tests/run_e2e_tests.py e2e-basic
```

#### Avant Push / PR
```bash
# Suite complète
python tests/run_e2e_tests.py full
```

#### CI/CD
```bash
# Stratégie deux étapes:
# 1. Fast check (unit)
pytest tests/ -m "unit" -v --tb=short

# 2. Full check si unit pass
pytest tests/ -v --tb=short
```

---

## 💰 Coût LLM Estimé

| Mode | Appels LLM | Coût (GPT-4o-mini) | Temps |
|------|------------|-------------------|-------|
| `quick` | 0 | $0 | < 2s |
| `e2e-basic` | 2-3 | ~$0.01 | ~1 min |
| `e2e-only` | 10-15 | ~$0.02-0.03 | ~2-3 min |
| `full` | 15-20 | ~$0.03-0.05 | ~3-5 min |

**Note** : Coûts basés sur GPT-4o-mini (~$0.15/1M input tokens, ~$0.60/1M output tokens)

---

## 🔍 Marqueurs Pytest

Les tests utilisent des marqueurs pour filtrage :

```ini
markers =
    e2e          : Tests end-to-end complets
    slow         : Tests lents (> 10 secondes)
    llm_api      : Tests utilisant API LLM réelle
    notion_api   : Tests utilisant API Notion réelle
    unit         : Tests unitaires rapides
    integration  : Tests d'intégration
```

### Exemples de Filtrage

```bash
# Seulement tests rapides
pytest tests/ -m "unit" -v

# Tout sauf les lents
pytest tests/ -m "not slow" -v

# Seulement E2E
pytest tests/ -m "e2e" -v

# E2E sans API Notion
pytest tests/ -m "e2e and not notion_api" -v
```

---

## 🐛 Debug

### Afficher les sorties print
```bash
pytest tests/test_e2e_workflow_personnage.py -v -s
```

### Afficher traceback complet
```bash
pytest tests/ -v --tb=long
```

### Arrêter au premier échec
```bash
pytest tests/ -v -x
```

### Lancer un test spécifique
```bash
pytest tests/test_e2e_workflow_personnage.py::TestE2EWorkflowPersonnageBasic::test_e2e_personnage_minimal -v -s
```

### Voir les tests disponibles
```bash
pytest tests/ --collect-only
```

---

## 🧹 Cleanup Automatique

Les tests utilisent la fixture `notion_page_tracker` pour cleanup automatique :

```python
def test_something(notion_page_tracker):
    # Créer page
    page_id = create_page(...)
    
    # Ajouter au tracker
    notion_page_tracker.append(page_id)
    
    # La page sera automatiquement archivée après le test
```

**Cleanup manuel** (si test échoue avant cleanup) :

1. Aller dans Notion → Bac à sable
2. Filtrer par nom commençant par `TEST_`
3. Archiver manuellement

---

## ✅ Checklist Avant Commit

- [ ] `python tests/run_e2e_tests.py quick` ✅ (< 2s)
- [ ] `python tests/run_e2e_tests.py e2e-basic` ✅ (~1 min)
- [ ] Code review des changements
- [ ] Documentation à jour si nécessaire

**Checklist complète avant PR** :

- [ ] `python tests/run_e2e_tests.py full` ✅ (~3-5 min)
- [ ] Linter passes (`read_lints` si applicable)
- [ ] CHANGELOG.md mis à jour
- [ ] Tests nouveaux/modifiés documentés

---

## 📈 Métriques

### Temps d'Exécution (Estimations)

| Fichier Test | Tests | Temps Moyen |
|--------------|-------|-------------|
| `test_e2e_workflow_personnage.py` | 6 | ~3-4 min |
| `test_e2e_workflow_with_context.py` | 5 | ~3-5 min |
| `test_e2e_error_handling.py` | 6 | ~1-2 min |
| `test_writer_agent.py` | 10 | ~2-3 min |
| `test_notion_api.py` | 12 | ~30-60s |

**Total suite E2E complète** : ~10-15 minutes

---

## 🔧 Maintenance

### Ajouter un Nouveau Test E2E

1. **Choisir le fichier approprié** :
   - Workflow basique → `test_e2e_workflow_personnage.py`
   - Avec contexte → `test_e2e_workflow_with_context.py`
   - Gestion erreur → `test_e2e_error_handling.py`

2. **Créer le test** :
```python
@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.llm_api
def test_mon_nouveau_cas(test_llm, temp_output_dir):
    """Description claire du test"""
    brief = "..."
    workflow = ContentWorkflow(PERSONNAGES_CONFIG, llm=test_llm)
    state = workflow.run(brief)
    
    assert state["validator_metadata"]["is_valid"]
    # ... autres assertions
```

3. **Tester** :
```bash
pytest tests/test_e2e_workflow_personnage.py::test_mon_nouveau_cas -v -s
```

4. **Documenter** : Ajouter dans cette doc si nécessaire

---

## 📝 Bonnes Pratiques

### ✅ DO

- Utiliser `test_llm` fixture pour LLM réel
- Utiliser `notion_page_tracker` pour cleanup automatique
- Marquer tests avec `@pytest.mark.e2e`, `@pytest.mark.slow`, etc.
- Afficher logs utiles avec `print()` (visible avec `-s`)
- Assertions claires avec messages d'erreur explicites
- Documenter le but du test dans le docstring

### ❌ DON'T

- Ne PAS créer pages Notion sans cleanup
- Ne PAS oublier les marqueurs pytest
- Ne PAS faire de tests trop longs (> 2 min)
- Ne PAS écrire dans bases principales (lecture seule)
- Ne PAS hardcoder les IDs de bases (utiliser fixtures)

---

## 🔗 Références

- **Tests Export** : `README_EXPORT_TESTS.md`
- **Tests Notion** : `README_NOTION_TESTS.md`
- **Config Pytest** : `pytest.ini`
- **Fixtures** : `conftest.py`
- **Stratégie Testing** : `.cursor/rules/testing-strategy-v1.mdc`

