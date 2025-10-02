# Tests d'Export Notion

Tests pour valider l'export des fiches générées vers Notion.

## 📁 Structure

```
tests/
├── test_notion_export.py              # Tests unitaires (rapides)
├── test_notion_export_integration.py  # Tests d'intégration (lents, API réelle)
└── README_NOTION_TESTS.md            # Cette doc
```

## 🧪 Types de Tests

### Tests Unitaires (`test_notion_export.py`)

Tests **rapides** et **sans dépendances externes** :

- ✅ Extraction de métadonnées depuis markdown
- ✅ Construction des propriétés Notion
- ✅ Validation des types de propriétés
- ✅ Mapping domaine → database ID

**Lancer :**
```bash
pytest tests/test_notion_export.py -v
# ou seulement les unitaires
pytest tests/test_notion_export.py -v -m unit
```

### Tests d'Intégration (`test_notion_export_integration.py`)

Tests **lents** qui utilisent l'**API Notion réelle** :

- ✅ Création de pages personnages
- ✅ Création de pages lieux
- ✅ Validation du type `Rôle` (select vs rich_text)
- ✅ Ajout de contenu (blocks)
- ✅ Vérification des propriétés créées
- 🧹 Cleanup automatique (archive les pages)

**Lancer :**
```bash
# Nécessite NOTION_TOKEN dans .env
pytest tests/test_notion_export_integration.py -v -s
# ou seulement les tests d'intégration
pytest tests/ -v -m integration
```

## ⚙️ Configuration

### Variables d'environnement

```bash
# .env
NOTION_TOKEN=secret_...
```

### Bases Sandbox Utilisées

Les tests créent des pages dans les bases **BAC À SABLE uniquement** :

- **Personnages (1)** : `2806e4d21b458012a744d8d6723c8be1`
- **Lieux (1)** : `2806e4d21b4580969f1cd7463a4c889c`

⚠️ **Jamais dans les bases principales !**

## 📊 Couverture des Tests

### ✅ Ce qui est testé

#### Extraction Métadonnées
- Format `**Nom**: valeur` (gras markdown)
- Format `Nom: valeur` (sans gras)
- Champs manquants (fallback)

#### Propriétés Notion - Personnages
- `Nom` (title) ✅
- `Type` (select) ✅
- `Genre` (select) ✅
- `Alias` (rich_text) ✅
- `Occupation` (rich_text) ✅
- `Âge` (number) ✅
- `État` (status) ✅

#### Propriétés Notion - Lieux
- `Nom` (title) ✅
- `Catégorie` (select) ✅
- `Rôle` (select) ✅ **← CRITIQUE !**
- `Taille` (select) ✅
- `État` (status) ✅

#### API Notion
- POST `/pages` (création) ✅
- PATCH `/blocks/{id}/children` (contenu) ✅
- GET `/pages/{id}` (vérification) ✅
- PATCH `/pages/{id}` (archive) ✅

### ❌ Tests d'échec attendus

- `test_create_lieu_with_wrong_role_type_fails` : Vérifie que `Rôle` en `rich_text` **échoue bien** (doit être `select`)

## 🚀 Utilisation

### Développement rapide (unitaires seulement)

```bash
pytest tests/test_notion_export.py -v
```

### Avant commit (avec intégration)

```bash
# Tous les tests
pytest tests/ -v

# Seulement rapides + intégration critique
pytest tests/ -v -m "unit or integration"
```

### Debug d'un test spécifique

```bash
# Avec affichage des print()
pytest tests/test_notion_export_integration.py::test_create_personnage_with_all_properties -v -s

# Avec traceback complet
pytest tests/test_notion_export_integration.py -v --tb=long
```

## 🧹 Cleanup

Les tests d'intégration **archivent automatiquement** les pages créées.

Si un test échoue avant le cleanup :

1. Aller dans Notion → "Personnages (1)" ou "Lieux (1)"
2. Filtrer par nom commençant par `TEST_`
3. Archiver manuellement

Ou via script :

```python
import requests
import os

NOTION_TOKEN = os.getenv('NOTION_TOKEN')
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28"
}

# Archiver une page
page_id = "..."
requests.patch(
    f"https://api.notion.com/v1/pages/{page_id}",
    headers=headers,
    json={"archived": True}
)
```

## 📝 Ajouter un Nouveau Test

### 1. Test Unitaire

```python
# tests/test_notion_export.py

@pytest.mark.unit
def test_mon_extraction():
    """Test extraction d'un nouveau champ"""
    content = "- **Nouveau**: valeur"
    
    def extract_field(field_name, content):
        # ... logique d'extraction
        pass
    
    result = extract_field("Nouveau", content)
    assert result == "valeur"
```

### 2. Test d'Intégration

```python
# tests/test_notion_export_integration.py

@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.skipif(not NOTION_TOKEN, reason="NOTION_TOKEN not set")
def test_ma_nouvelle_propriete():
    """Test création avec nouvelle propriété"""
    properties = {
        "Nom": {"title": [{"text": {"content": "Test"}}]},
        "NouvelleProp": {"select": {"name": "Valeur"}}
    }
    
    page = create_test_page(DATABASE_ID, properties)
    
    try:
        retrieved = verify_page_properties(page['id'], properties)
        assert retrieved['properties']['NouvelleProp']['select']['name'] == "Valeur"
    finally:
        delete_test_page(page['id'])
```

## 🐛 Problèmes Courants

### `NOTION_TOKEN not set`

Solution :
```bash
# Copier .env.example vers .env
cp .env.example .env
# Ajouter votre token
echo "NOTION_TOKEN=secret_..." >> .env
```

### `API Error: Rôle is expected to be select`

**Cause** : Le champ `Rôle` pour les Lieux est de type `select`, pas `rich_text`.

**Solution** : Utiliser `{"select": {"name": "..."}}` au lieu de `{"rich_text": [...]}`

### Pages non archivées

**Cause** : Test échoué avant le cleanup `finally:`

**Solution** : Filtrer et archiver manuellement les pages `TEST_*` dans Notion

## 📈 Métriques

Lancer avec coverage :

```bash
pytest tests/test_notion_export.py --cov=app_streamlit --cov-report=html
# Ouvrir htmlcov/index.html
```

## 🔗 Références

- [Notion API - Create Page](https://developers.notion.com/reference/post-page)
- [Notion API - Append Block Children](https://developers.notion.com/reference/patch-block-children)
- [Property Types](https://developers.notion.com/reference/property-object)

