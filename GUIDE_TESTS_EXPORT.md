# Guide : Tests d'Export Notion

## 🚀 Usage rapide

### Tests pendant le développement (< 1s)
```bash
python tests/run_export_tests.py quick
```
✅ 38 tests en 0.09s  
✅ Pas d'appel API  
✅ Idéal pour itération rapide

### Tests avant commit (~ 10s)
```bash
python tests/run_export_tests.py full
```
✅ Tous les tests (extraction + payload + API)  
✅ Validation complète  
⚠️ Nécessite `NOTION_TOKEN`

---

## 📊 Modes disponibles

| Mode | Durée | API Notion | Usage |
|------|-------|------------|-------|
| `quick` | < 1s | ❌ | **Développement** (défaut) |
| `full` | ~10s | ✅ | **Avant commit** |
| `extract` | < 0.5s | ❌ | Debug extraction |
| `payload` | < 0.5s | ❌ | Debug payload |
| `api` | ~10s | ✅ | Tests d'intégration seulement |

---

## 🎯 Cas d'usage

### ✏️ J'ai modifié l'extraction de champs
```bash
python tests/run_export_tests.py extract
```

### 🔧 J'ai modifié la construction du payload
```bash
python tests/run_export_tests.py payload
```

### 🚀 J'ai modifié l'export complet
```bash
python tests/run_export_tests.py full
```

### 🐛 Un champ n'est pas exporté (ex: "Réponse au problème moral")
```bash
# Tester l'extraction
pytest tests/ -k "morale" -v

# Si extraction OK, tester le payload
pytest tests/test_export_payload.py::TestChampsEssentiels -v

# Si payload OK, tester l'API
pytest tests/test_export_integration.py -v -m integration
```

---

## ✅ Checklist avant commit

```bash
# 1. Tests rapides (< 1s)
python tests/run_export_tests.py quick

# 2. (Optionnel) Tests complets (~ 10s)
python tests/run_export_tests.py full
```

---

## 📝 Ajouter un nouveau champ

### 1. Ajouter le champ dans les fixtures
`tests/test_export_extraction.py` :
```python
@pytest.fixture
def sample_personnage_content():
    return """
    ...
    - **Nouveau Champ**: Valeur test
    ...
    """
```

### 2. Tester l'extraction
```python
def test_extract_nouveau_champ(self, sample_personnage_content):
    valeur = extract_field("Nouveau Champ", sample_personnage_content)
    assert valeur == "Valeur test"
```

### 3. Tester le payload
```python
def test_payload_has_nouveau_champ(self, sample_personnage_content):
    props = build_notion_properties_personnage(sample_personnage_content)
    assert "Nouveau Champ" in props
```

### 4. Exécuter
```bash
python tests/run_export_tests.py quick
```

---

## 🔍 Alternatives (pytest direct)

```bash
# Tests rapides
pytest tests/test_export_extraction.py tests/test_export_payload.py -v

# Tests API seulement
pytest tests/test_export_integration.py -v -m integration

# Test spécifique
pytest tests/ -k "espece" -v

# Voir tous les tests disponibles
pytest tests/ --collect-only
```

---

## 📚 Documentation complète

👉 `tests/README_EXPORT_TESTS.md`

---

## ✨ Principe

**Si un champ n'est pas exporté correctement, un test DOIT échouer.**

Les tests sont :
- ✅ **Rapides** : < 1 seconde (tests unitaires)
- ✅ **Isolés** : Pas de dépendances entre tests
- ✅ **Propres** : Cleanup automatique (intégration)
- ✅ **Extensibles** : Ajouter nouveau champ = quelques lignes
- ✅ **Documentés** : Chaque test a un docstring clair

