# Tests de Récupération Récursive du Contenu Notion

## 📋 Vue d'ensemble

Le fichier `test_notion_recursive_fetch.py` contient des tests unitaires pour valider la récupération **récursive** du contenu des pages Notion, y compris les blocs enfants (toggles, sections repliables, etc.).

## 🐛 Problème Résolu

**Avant le fix** : Le `NotionContextFetcher` ne récupérait que le premier niveau de blocs des pages Notion. Les pages avec des sections repliables (heading toggles) apparaissaient vides (seulement les titres de sections, pas le contenu).

**Après le fix** : Récupération **récursive** de tous les niveaux de blocs, préservant la structure et l'indentation.

## 🧪 Tests Disponibles

### 1. `test_recursive_fetch_simple_nested`
**Objectif** : Vérifier la récupération d'une structure simple imbriquée.

**Structure testée** :
```
Page Root
└── Heading 1: "Section principale"
    └── Toggle: "Détails cachés"
        ├── Paragraph: "Contenu du toggle ligne 1"
        └── Paragraph: "Contenu du toggle ligne 2"
```

**Vérifie** :
- Tous les niveaux sont récupérés
- Le formatage est correct (headings, toggles)
- L'indentation est préservée

---

### 2. `test_recursive_fetch_complex_nested`
**Objectif** : Valider la récupération d'une structure complexe à plusieurs niveaux.

**Structure testée** :
```
Page Root
├── Heading 1: "Identité & Vue d'ensemble"
│   ├── Paragraph: "Description générale"
│   └── Heading 2: "Sous-section"
│       └── Bulleted list: "Item 1"
└── Heading 1: "Géographie & Environnement"
    └── Callout: "Note importante"
        └── Paragraph: "Détail de la note"
```

**Vérifie** :
- Récupération correcte sur 3+ niveaux d'imbrication
- Tous les types de blocs sont présents
- La hiérarchie est maintenue

---

### 3. `test_recursive_fetch_empty_page`
**Objectif** : Vérifier le comportement avec une page vide.

**Vérifie** :
- Aucune erreur n'est levée
- Le contenu retourné est une chaîne vide
- Le fetcher gère correctement l'absence de blocs

---

### 4. `test_recursive_fetch_only_headings`
**Objectif** : Tester le cas problématique initial (headings sans contenu).

**Structure testée** :
```
Page Root
├── Heading 1: "Identité & Vue d'ensemble" (sans enfants)
└── Heading 1: "Géographie & Environnement" (sans enfants)
```

**Vérifie** :
- Les headings vides sont récupérés
- Le contenu est court (pas de faux-positifs)
- Correspond au comportement observé **avant** le fix

---

### 5. `test_recursive_fetch_handles_errors`
**Objectif** : Valider la résilience face aux erreurs de récupération.

**Vérifie** :
- Le fetcher continue même si un bloc enfant n'est pas accessible
- Les blocs valides sont tout de même récupérés
- Pas de crash sur erreur partielle

---

### 6. `test_block_types_formatting`
**Objectif** : Vérifier le formatage de tous les types de blocs supportés.

**Types testés** :
- `paragraph` → texte simple
- `heading_1` → `# Titre`
- `heading_2` → `## Titre`
- `heading_3` → `### Titre`
- `bulleted_list_item` → `- Item`
- `numbered_list_item` → `1. Item`
- `quote` → `> Citation`
- `callout` → `💡 Callout`
- `toggle` → `▶ Toggle`

**Vérifie** :
- Tous les types sont correctement formatés en Markdown
- Les symboles spéciaux sont présents

---

### 7. `test_indentation_preserved`
**Objectif** : Valider la préservation de l'indentation pour la hiérarchie.

**Structure testée** :
```
Niveau 0 (0 espaces)
└── Niveau 1 (2 espaces)
    └── Niveau 2 (4 espaces)
```

**Vérifie** :
- L'indentation augmente de 2 espaces par niveau
- La hiérarchie visuelle est préservée
- Facilite la lecture du contexte par l'IA

---

### 8. `test_preview_with_content_summary`
**Objectif** : Vérifier que le summary est généré depuis le contenu si absent des propriétés Notion.

**Vérifie** :
- Le summary est extrait du contenu de la page (premiers ~150 caractères)
- Les premiers mots du contenu apparaissent dans le summary
- Le summary est correctement tronqué avec "..."
- Fonctionne même si les propriétés "Alias" ou "Description" sont vides

---

### 9. `test_token_estimate_based_on_content`
**Objectif** : Valider que l'estimation des tokens est basée sur le contenu réel, pas sur une valeur fixe.

**Vérifie** :
- L'estimation reflète la taille réelle du contenu
- Pour ~200 mots, l'estimation est > 250 tokens
- L'estimation est raisonnable (pas trop élevée)
- Meilleure précision qu'avec l'ancien système (800 tokens fixes)

---

### 10. `test_extract_first_words_cleans_markdown`
**Objectif** : Tester la fonction de nettoyage du markdown pour les aperçus.

**Vérifie** :
- Les headers markdown (#, ##, ###) sont ignorés
- Les symboles markdown (-, >, 💡, ▶) sont retirés
- Le contenu réel est extrait proprement
- Le texte est tronqué intelligemment au dernier espace
- Le résultat est lisible et informatif

---

## 🏗️ Architecture des Tests

### Fixtures

#### `clear_global_cache` (autouse=True)
Nettoie le cache global entre chaque test pour éviter les interférences.

#### Structures de données
- `simple_nested_structure` : Structure simple pour tests de base
- `complex_nested_structure` : Structure complexe multi-niveaux
- `empty_page_structure` : Page vide
- `only_headings_structure` : Headings sans contenu

### Client Mocké

La fonction `create_mock_client` crée un client Notion factice qui :
- Simule la structure de blocs imbriqués
- Implémente la récupération récursive
- Retourne du contenu formaté en Markdown
- Ne fait **aucun appel** à l'API Notion réelle

---

## 🚀 Exécution des Tests

### Tous les tests
```bash
python -m pytest tests/test_notion_recursive_fetch.py -v
```

### Un test spécifique
```bash
python -m pytest tests/test_notion_recursive_fetch.py::test_recursive_fetch_simple_nested -v
```

### Avec couverture de code
```bash
python -m pytest tests/test_notion_recursive_fetch.py --cov=agents.notion_context_fetcher --cov-report=html
```

---

## 📊 Résultats Attendus

```
tests/test_notion_recursive_fetch.py::test_recursive_fetch_simple_nested PASSED [ 10%]
tests/test_notion_recursive_fetch.py::test_recursive_fetch_complex_nested PASSED [ 20%]
tests/test_notion_recursive_fetch.py::test_recursive_fetch_empty_page PASSED [ 30%]
tests/test_notion_recursive_fetch.py::test_recursive_fetch_only_headings PASSED [ 40%]
tests/test_notion_recursive_fetch.py::test_recursive_fetch_handles_errors PASSED [ 50%]
tests/test_notion_recursive_fetch.py::test_block_types_formatting PASSED [ 60%]
tests/test_notion_recursive_fetch.py::test_indentation_preserved PASSED  [ 70%]
tests/test_notion_recursive_fetch.py::test_preview_with_content_summary PASSED [ 80%]
tests/test_notion_recursive_fetch.py::test_token_estimate_based_on_content PASSED [ 90%]
tests/test_notion_recursive_fetch.py::test_extract_first_words_cleans_markdown PASSED [100%]

============================== 10 passed in 0.10s ==============================
```

---

## 🔧 Maintenance

### Ajouter un nouveau type de bloc

1. Ajouter le cas dans `create_mock_client.retrieve_page_content`
2. Créer un test dans `test_block_types_formatting`
3. Vérifier que le formatage est correct

### Ajouter un nouveau test

1. Créer une fixture de structure si nécessaire
2. Écrire le test en utilisant `create_mock_client`
3. Vérifier que le cache est correctement nettoyé (autouse fixture)

---

## 📝 Notes Importantes

1. **Cache** : La fixture `clear_global_cache` est **critique** pour éviter les interférences entre tests
2. **Client Mocké** : Les tests n'appellent **jamais** l'API Notion réelle
3. **Indentation** : 2 espaces par niveau d'imbrication
4. **Formatage** : Markdown standard + symboles spéciaux (💡, ▶)

---

## 🔗 Fichiers Liés

- **Code testé** : `agents/notion_context_fetcher.py`
- **Méthode clé** : `DirectNotionClient.retrieve_page_content` (récursive)
- **Config** : `config/context_cache.py`
- **Tests d'intégration** : `tests/test_context_selection_backend.py`

---

## 📅 Historique

- **2025-10-04** : Création des tests après fix de la récupération récursive
- **Problème initial** : Pages Notion avec toggles apparaissaient vides (272 caractères au lieu de plusieurs milliers)
- **Solution** : Récupération récursive des blocs enfants avec préservation de l'indentation

