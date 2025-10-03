# Tests d'Export Notion

Suite de tests **modulaire et durable** pour valider l'export Notion.

## 📋 Structure

```
tests/
├── test_export_extraction.py      # Tests unitaires (extraction markdown)
├── test_export_payload.py          # Tests unitaires (construction payload Notion)
├── test_export_integration.py      # Tests d'intégration (API réelle)
└── README_EXPORT_TESTS.md          # Cette documentation
```

---

## 🚀 Exécution rapide

### Tests rapides (sans API Notion)
```bash
# Extraction + Payload uniquement (< 1 seconde)
pytest tests/test_export_extraction.py tests/test_export_payload.py -v
```

### Tests d'intégration (avec API Notion)
```bash
# Tests réels avec création/suppression de pages (~ 10 secondes)
pytest tests/test_export_integration.py -v -m integration
```

### Tout exécuter
```bash
# Tous les tests (extraction + payload + intégration)
pytest tests/test_export_*.py -v
```

---

## 📊 Types de tests

### 1. **test_export_extraction.py** ✅ Rapide
**Objectif :** Vérifier que les champs sont correctement extraits du markdown

**Ce qui est testé :**
- Extraction des champs simples (Nom, Type, Genre...)
- Extraction des relations (Espèce, Communautés, Lieux de vie...)
- Extraction des multi-valeurs (Qualités, Défauts, Archétype...)
- Extraction de rich text long (Réponse au problème moral)
- Parsing et split des valeurs multiples

**Cas de test :**
- Format personnages (`**Champ**: valeur`)
- Format lieux (sous `CHAMPS NOTION`)
- Champs manquants
- Valeurs multiples (`,` et `;` comme séparateurs)

**Exécution :**
```bash
pytest tests/test_export_extraction.py -v
```

---

### 2. **test_export_payload.py** ✅ Rapide
**Objectif :** Vérifier que le payload Notion est correctement construit

**Ce qui est testé :**
- Structure des propriétés (`title`, `select`, `multi_select`, `rich_text`, `number`)
- Présence de tous les champs essentiels
- Format correct pour l'API Notion
- Validation selon le domaine (personnages vs lieux)

**Cas de test :**
- Tous les types de propriétés Notion
- Champs obligatoires présents
- Structure JSON valide
- Valeurs par défaut (État = "Brouillon IA")

**Exécution :**
```bash
pytest tests/test_export_payload.py -v
```

---

### 3. **test_export_integration.py** ⚠️ Lent (API réelle)
**Objectif :** Vérifier que l'export fonctionne end-to-end dans Notion

**Ce qui est testé :**
- Création réelle de pages dans le sandbox
- Sauvegarde correcte des propriétés
- Multi-selects persistés
- Rich text correctement formaté
- Cleanup automatique après chaque test

**⚠️ Prérequis :**
- Variable d'environnement `NOTION_TOKEN` configurée
- Accès aux bases sandbox (Personnages (1), Lieux (1))

**Cleanup automatique :**
- Toutes les pages créées sont automatiquement archivées après chaque test
- Pas de pollution du sandbox

**Exécution :**
```bash
# Tous les tests d'intégration
pytest tests/test_export_integration.py -v -m integration

# Un test spécifique
pytest tests/test_export_integration.py::TestExportPersonnageIntegration::test_create_personnage_basic -v
```

---

## 🔍 Exécution sélective

### Par marqueur
```bash
# Tests rapides uniquement (unit)
pytest tests/ -v -m "not integration"

# Tests lents uniquement (integration)
pytest tests/ -v -m "integration and slow"
```

### Par classe
```bash
# Tests d'extraction des relations
pytest tests/test_export_extraction.py::TestExtractionRelations -v

# Tests de payload personnage
pytest tests/test_export_payload.py::TestPayloadPersonnage -v

# Tests d'export lieu
pytest tests/test_export_integration.py::TestExportLieuIntegration -v
```

### Par nom de test
```bash
# Tests contenant "espece"
pytest tests/ -k "espece" -v

# Tests contenant "multiselect"
pytest tests/ -k "multiselect" -v

# Tests contenant "lieu"
pytest tests/ -k "lieu" -v
```

---

## 🎯 Cas d'usage

### Développement : Vérifier l'extraction
```bash
# Rapide, pas d'API
pytest tests/test_export_extraction.py -v
```

### Développement : Vérifier le payload
```bash
# Rapide, pas d'API
pytest tests/test_export_payload.py -v
```

### Debug : Tester un champ spécifique
```bash
# Ex: problème avec "Réponse au problème moral"
pytest tests/ -k "morale" -v
```

### Validation : Export complet
```bash
# Tous les tests, y compris API réelle
pytest tests/test_export_*.py -v
```

### CI/CD : Tests rapides
```bash
# Seulement extraction + payload (< 2 secondes)
pytest tests/test_export_extraction.py tests/test_export_payload.py -v --tb=short
```

### CI/CD : Tests complets
```bash
# Tous les tests, y compris intégration (~ 15 secondes)
pytest tests/test_export_*.py -v --tb=short
```

---

## 📈 Ajouter de nouveaux tests

### Nouveau champ à tester

**1. Ajouter le champ dans les fixtures :**
```python
# tests/test_export_extraction.py
@pytest.fixture
def sample_personnage_content():
    return """
    ...
    - **Nouveau Champ**: Valeur test
    ...
    """
```

**2. Tester l'extraction :**
```python
def test_extract_nouveau_champ(self, sample_personnage_content):
    valeur = extract_field("Nouveau Champ", sample_personnage_content)
    assert valeur == "Valeur test"
```

**3. Tester le payload :**
```python
def test_payload_has_nouveau_champ(self, sample_personnage_content):
    props = build_notion_properties_personnage(sample_personnage_content)
    assert "Nouveau Champ" in props
```

**4. Tester l'intégration :**
```python
def test_nouveau_champ_saved(self, notion_headers, sample_personnage_content):
    # ... create page ...
    saved_props = get_page_properties(page_data["id"], notion_headers)
    assert saved_props["Nouveau Champ"]["type"]["value"] == "attendu"
```

---

## ⚙️ Configuration pytest

Ajouter dans `pytest.ini` (optionnel) :
```ini
[pytest]
markers =
    integration: Tests with real Notion API calls
    slow: Slow running tests
    unit: Fast unit tests
```

---

## 🐛 Debug

### Afficher les sorties print
```bash
pytest tests/ -v -s
```

### Afficher le traceback complet
```bash
pytest tests/ -v --tb=long
```

### Arrêter au premier échec
```bash
pytest tests/ -v -x
```

### Voir les tests disponibles
```bash
pytest tests/ --collect-only
```

---

## ✅ Checklist avant commit

- [ ] `pytest tests/test_export_extraction.py -v` ✅ (rapide)
- [ ] `pytest tests/test_export_payload.py -v` ✅ (rapide)
- [ ] `pytest tests/test_export_integration.py -v -m integration` ✅ (lent, optionnel)

---

## 📝 Exemples de sortie

### Succès
```bash
$ pytest tests/test_export_extraction.py -v

tests/test_export_extraction.py::TestExtractionBasique::test_extract_nom_personnage PASSED
tests/test_export_extraction.py::TestExtractionRelations::test_extract_espece PASSED
...
======================== 25 passed in 0.42s ========================
```

### Échec (exemple)
```bash
$ pytest tests/test_export_extraction.py::TestExtractionRelations::test_extract_espece -v

AssertionError: assert 'Humain' == 'Humain modifié'
  - Humain modifié
  + Humain
```

---

## 🔧 Maintenance

Ces tests sont conçus pour être :
- ✅ **Rapides** : Tests unitaires < 1 seconde
- ✅ **Isolés** : Pas de dépendances entre tests
- ✅ **Propres** : Cleanup automatique (intégration)
- ✅ **Extensibles** : Ajouter nouveau champ = quelques lignes
- ✅ **Documentés** : Chaque test a un docstring clair

**Principe :** Si un champ n'est pas exporté correctement, un test **doit** échouer.

