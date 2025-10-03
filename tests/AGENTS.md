# Instructions Tests

## Organisation
- Tests unitaires : rapides (< 1s), pas d'API
- Tests intégration : lents (~10s), API réelle, cleanup auto

## Structure Export
- `test_export_extraction.py` : Markdown → données (22 tests)
- `test_export_payload.py` : Données → payload Notion (16 tests)
- `test_export_integration.py` : Payload → API Notion (7 tests)

## Exécution
```bash
# Rapide (38 tests, < 1s)
python tests/run_export_tests.py quick

# Complet (45 tests, ~10s)
python tests/run_export_tests.py full

# Spécifique
pytest tests/ -k "espece" -v
```

## Règles Critiques
- **JAMAIS** créer de fichiers temporaires (test_temp.py, debug_*.py)
- Utiliser `python -c "..."` pour tests rapides
- Ou `if __name__ == "__main__":` dans les modules
- Cleanup automatique pour tests API (pas de pollution sandbox)

## Ajouter un Test
1. Fixture dans `test_export_extraction.py`
2. Test extraction : `assert extract_field("Champ") == "valeur"`
3. Test payload : `assert "Champ" in properties`
4. Relancer : `python tests/run_export_tests.py quick`

## Principe
**Si un champ n'est pas exporté, un test DOIT échouer.**

