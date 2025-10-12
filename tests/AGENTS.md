# Architecture Tests - Système Multi-Agents

## Organisation

### Pyramide de Tests
```
         🔺 E2E
        /    \
       / Intég \
      /  (API)  \
     /___________\
    Unit (rapide)
```

**Ratio** : 70% Unit / 20% Integration / 10% E2E

### Structure Complète

```
tests/
├── conftest.py                         # Fixtures partagées (llm, notion, cleanup)
├── pytest.ini                          # Config pytest + marqueurs
│
├── run_export_tests.py                 # Runner tests export
├── run_e2e_tests.py                    # Runner tests E2E
│
├── test_export_extraction.py           # Unit : Extraction markdown (22 tests)
├── test_export_payload.py              # Unit : Construction payload (16 tests)
├── test_export_integration.py          # Integration : API Notion export (7 tests)
│
├── test_notion_api.py                  # Integration : API Notion consolidée
│
├── test_e2e_workflow_personnage.py     # E2E : Workflow personnages
├── test_e2e_workflow_with_context.py   # E2E : Workflow + contexte Notion
├── test_e2e_error_handling.py          # E2E : Gestion d'erreurs
│
├── test_writer_agent.py                # Integration : WriterAgent
├── test_structured_outputs_agents.py   # Integration : Structured outputs
│
├── README_EXPORT_TESTS.md              # Doc tests export
├── README_E2E_TESTS.md                 # Doc tests E2E (COMPLET)
└── AGENTS.md                           # Ce fichier
```

## Exécution Rapide

### Tests Quotidiens (Dev)
```bash
# Rapides uniquement (< 2s)
python tests/run_e2e_tests.py quick

# Ou exports uniquement
python tests/run_export_tests.py quick
```

### Tests E2E
```bash
# E2E basiques (~1 min)
python tests/run_e2e_tests.py e2e-basic

# Tous les E2E (~3 min, ~$0.03)
python tests/run_e2e_tests.py e2e-only

# Suite complète (~5 min, ~$0.05)
python tests/run_e2e_tests.py full
```

### Tests par Marqueur
```bash
# Unit seulement
pytest tests/ -m "unit" -v

# Tout sauf lents
pytest tests/ -m "not slow" -v

# E2E uniquement
pytest tests/ -m "e2e" -v
```

## Marqueurs Pytest

| Marqueur | Usage | Temps | Coût |
|----------|-------|-------|------|
| `@pytest.mark.unit` | Tests rapides, pas d'API | < 1s | $0 |
| `@pytest.mark.integration` | Tests agents individuels | 5-30s | ~$0.005 |
| `@pytest.mark.e2e` | Workflow complet | 30-90s | ~$0.01 |
| `@pytest.mark.slow` | Tests > 10s | Variable | Variable |
| `@pytest.mark.llm_api` | Utilise API LLM | Variable | ~$0.003+ |
| `@pytest.mark.notion_api` | Utilise API Notion | Variable | $0 |

**Règle** : TOUS les tests doivent avoir au moins un marqueur.

## Fixtures Partagées (`conftest.py`)

### Notion
- `notion_token` : Token Notion (skip si absent)
- `notion_headers` : Headers API Notion
- `sandbox_databases` : IDs bases sandbox (écriture)
- `main_databases` : IDs bases principales (lecture)
- `notion_page_tracker` : Cleanup automatique pages créées

### LLM
- `test_llm` : GPT-4o-mini pour tests
- `test_llm_fast` : Version rapide (tokens réduits)

### Helpers
- `temp_output_dir` : Répertoire temporaire outputs
- `sample_brief_personnage` : Brief test personnage
- `sample_brief_lieu` : Brief test lieu

## Règles Critiques

### ✅ TOUJOURS
- Utiliser fixtures du `conftest.py`
- Ajouter marqueurs pytest appropriés
- Cleanup automatique ressources créées
- Docstring clair pour chaque test
- Assertions avec messages d'erreur explicites

### ❌ JAMAIS
- Créer fichiers temporaires (test_temp.py, debug_*.py)
- Créer pages Notion sans cleanup (`notion_page_tracker`)
- Écrire dans bases Notion principales (lecture seule)
- Hardcoder LLM (utiliser fixture `test_llm`)
- Tests E2E > 2 minutes
- Oublier les marqueurs pytest

## Ajouter un Nouveau Test

### Test Unit (Extraction, Parsing)
```python
@pytest.mark.unit
def test_extract_nouveau_champ():
    """Extraction du nouveau champ"""
    content = "**NouveauChamp**: valeur"
    
    result = extract_field("NouveauChamp", content)
    
    assert result == "valeur"
```

### Test Integration (Agent)
```python
@pytest.mark.integration
@pytest.mark.llm_api
@pytest.mark.slow
def test_writer_nouveau_cas(test_llm):
    """WriterAgent avec nouveau cas"""
    brief = "..."
    
    writer = WriterAgent(CONFIG, llm=test_llm)
    result = writer.process(brief)
    
    assert result.success
    assert len(result.content) > 100
```

### Test E2E (Workflow)
```python
@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.llm_api
@pytest.mark.notion_api
def test_e2e_nouveau_scenario(
    test_llm,
    notion_page_tracker,
    temp_output_dir
):
    """E2E : nouveau scénario"""
    brief = "..."
    
    workflow = ContentWorkflow(CONFIG, llm=test_llm)
    state = workflow.run(brief)
    
    assert state["validator_metadata"]["is_valid"]
    
    # Export avec cleanup
    page_id = export_to_notion(state, sandbox_db)
    notion_page_tracker.append(page_id)
```

## Checklist Avant Commit

- [ ] Tests rapides : `python tests/run_e2e_tests.py quick` ✅
- [ ] E2E basiques : `python tests/run_e2e_tests.py e2e-basic` ✅
- [ ] Tous marqueurs présents
- [ ] Cleanup automatique activé

## Références

- **Tests E2E complets** : `README_E2E_TESTS.md`
- **Tests Export** : `README_EXPORT_TESTS.md`
- **Stratégie Tests** : `.cursor/rules/testing-strategy-v1.mdc`
- **Config Pytest** : `pytest.ini`

## Principe

**Si un champ n'est pas exporté, un test DOIT échouer.**  
**Si un workflow ne fonctionne pas E2E, un test DOIT échouer.**

