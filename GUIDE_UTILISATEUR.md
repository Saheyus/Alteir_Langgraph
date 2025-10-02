# 📘 Guide Utilisateur - Système Multi-Agents GDD Alteir

## 🎯 Vue d'Ensemble

Le système multi-agents GDD Alteir est un outil de génération assistée par IA pour créer du contenu narratif cohérent et de qualité. Il orchestre 4 agents spécialisés :

1. **Writer** → Génère le contenu initial
2. **Reviewer** → Analyse la cohérence narrative
3. **Corrector** → Corrige la forme (grammaire, style)
4. **Validator** → Validation finale et scores

## 🚀 Démarrage Rapide

### Installation

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Configurer l'environnement
cp env.example .env
# Éditer .env avec vos clés API

# 3. Lancer l'interface Streamlit
streamlit run app_streamlit.py
```

### Première Utilisation

1. **Ouvrir l'interface** : `streamlit run app_streamlit.py`
2. **Remplir le brief** : Description du personnage à créer
3. **Configurer les paramètres** :
   - **Intent** : Type de profondeur narrative
   - **Level** : Niveau de détail (cameo/standard/major)
   - **Dialogue** : Mode de communication
   - **Créativité** : Température du LLM (0-1)
4. **Générer** : Cliquer sur "Générer le Personnage"
5. **Consulter** : Voir les résultats, scores et fichiers générés

## 📊 Paramètres Détaillés

### Intent (Intention Narrative)

| Intent | Description | Usage |
|--------|-------------|-------|
| `orthogonal_depth` | Profondeur NON alignée au rôle | **Recommandé** - Personnages originaux |
| `vocation_pure` | Profondeur alignée au rôle | Archétypes classiques assumés |
| `archetype_assume` | Archétype assumé, show > tell | Guerriers, héros traditionnels |
| `mystere_non_resolu` | Profondeur elliptique | Personnages mystérieux, cameos |

### Level (Niveau de Détail)

| Level | Répliques | Relations | Artefacts | Usage |
|-------|-----------|-----------|-----------|-------|
| `cameo` | 4-6 | 0-1 | 0-1 | PNJ secondaires, apparitions brèves |
| `standard` | 8-10 | 1-3 | 1-2 | **Défaut** - PNJ principaux |
| `major` | 10-12 | 2-4 | 2-3 | Personnages centraux, PJ |

### Dialogue Mode

| Mode | Description | Exemple |
|------|-------------|---------|
| `parle` | Dialogues oraux | **Défaut** - Communication classique |
| `gestuel` | Communication gestuelle | Espèces non-verbales |
| `telepathique` | Communication mentale | Entités psioniques |
| `ecrit_only` | Messages écrits uniquement | Correspondances, archives |

### Créativité (Température)

- **0.0-0.4** : Déterministe, prévisible
- **0.5-0.7** : **Équilibré (recommandé)**
- **0.8-1.0** : Très créatif, imprévisible

## 📂 Outputs Générés

### Fichiers

Chaque génération crée 2 fichiers dans `outputs/` :

1. **JSON** (`personnages_YYYYMMDD_HHMMSS.json`)
   - État complet du workflow
   - Métadonnées de chaque agent
   - Historique des étapes
   - Scores détaillés

2. **Markdown** (`personnages_YYYYMMDD_HHMMSS.md`)
   - Contenu formaté lisible
   - Métriques en en-tête
   - Sections structurées

### Scores

#### Cohérence (0.0-1.0)
- **≥ 0.7** : Bon
- **0.5-0.6** : Acceptable
- **< 0.5** : À revoir

*Évalue : Cohérence narrative, respect des principes, structure*

#### Complétude (0.0-1.0)
- **≥ 0.8** : Complet
- **0.6-0.7** : Incomplet
- **< 0.6** : Très incomplet

*Évalue : Champs obligatoires, richesse du contenu*

#### Qualité (0.0-1.0)
- **≥ 0.7** : Bon
- **0.5-0.6** : Acceptable
- **< 0.5** : À améliorer

*Évalue : Style, correction linguistique, clarté*

### Statut Publication

- ✅ **Prêt pour publication** : Tous les critères validés
- ⚠️ **Nécessite révision** : Problèmes à corriger

## 🎨 Principes Narratifs

### 1. Orthogonalité Rôle ↔ Profondeur

La profondeur du personnage ne doit **PAS** être explicable par son rôle seul.

**Exemple :**
- ❌ Alchimiste obsédé par l'alchimie
- ✅ Cartographe membre d'un culte cherchant des ossements divins

### 2. Structure Surface / Profondeur / Monde

- **Surface** : Visible (gestes, objets, apparence)
- **Profondeur** : Caché (motivations, secrets, passé)
- **Monde** : Contraintes externes (institutions, lois, ressources)

### 3. Temporalité IS / WAS / COULD-HAVE-BEEN

- **IS** : État présent
- **WAS** : Passé concret
- **COULD-HAVE-BEEN** : Voie non empruntée

### 4. Show > Tell

Privilégier :
- Objets porteurs de sens
- Rituels quotidiens
- Silences et non-dits
- Traces physiques

### 5. Relations Concrètes

Chaque relation doit avoir au moins :
- **Prix** : Coût pour maintenir
- **Dette** : Obligation mutuelle
- **Délai** : Urgence temporelle
- **Tabou** : Limite à ne pas franchir

## 🔧 Interfaces Disponibles

### 1. Streamlit (Recommandé)

```bash
streamlit run app_streamlit.py
```

**Avantages :**
- Interface graphique moderne
- Visualisation temps réel
- Métriques détaillées
- Navigation facile

### 2. CLI

```bash
python app_cli.py
```

**Avantages :**
- Ligne de commande
- Menu interactif
- Pas de navigateur

### 3. LangGraph Studio

```bash
pip install langgraph-cli
langgraph dev
```

**Avantages :**
- Visualisation du workflow
- Debug étape par étape
- Inspection d'état

### 4. Script Direct

```bash
python demo_workflow.py
```

**Avantages :**
- Affichage Rich dans terminal
- Rapide pour tests
- Scriptable

## 🧪 Tests

### Tests Données Réelles

```bash
python tests/test_real_data.py
```

Teste 4 personnages types :
1. Valen Arkan (major, orthogonal)
2. Kira l'Entailleuse (standard, orthogonal)
3. Torvak (cameo, mystère)
4. Zara (standard, archétype assumé)

### Tests Intégration Notion

```bash
python tests/test_notion_integration.py
```

Teste :
- Fetch bac à sable
- Search dans data source
- Create page (optionnel)
- Fetch bases principales

## 🔌 Notion Integration

### Configuration

1. **Token Notion** : Dans `.env`
   ```
   NOTION_TOKEN=secret_...
   ```

2. **Bases de données** :
   - **Lecture** : Lieux, Personnages, Communautés, Espèces
   - **Écriture** : Bac à sable (test)

### Utilisation

Le système peut :
- ✅ Lire contexte depuis Notion (espèces, lieux, etc.)
- ✅ Valider références croisées
- ✅ Créer pages dans le bac à sable
- ⚠️ **Pas de création directe** dans bases principales

## 🤖 Multi-Provider LLM

### Providers Supportés

1. **OpenAI** (Défaut)
   - GPT-5-nano (recommandé)
   - Structured Outputs natif

2. **Anthropic**
   - Claude 3.5, 4
   - JSON mode

3. **Mistral**
   - Mistral Large, Medium
   - JSON mode

4. **Ollama (Local)**
   - Llama 3, Mixtral
   - Fallback JSON parsing

### Configuration Provider

Dans `.env` :
```bash
LLM_PROVIDER=openai  # ou anthropic, mistral, ollama
OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=...
# MISTRAL_API_KEY=...
```

## 📋 Workflow Complet

```
1. BRIEF UTILISATEUR
   ↓
2. WRITER AGENT
   - Génère contenu initial
   - Applique principes narratifs
   - Structure selon template
   ↓
3. REVIEWER AGENT
   - Analyse cohérence
   - Identifie problèmes
   - Propose améliorations
   ↓
4. CORRECTOR AGENT
   - Corrige grammaire/orthographe
   - Améliore clarté
   - Uniformise style
   ↓
5. VALIDATOR AGENT
   - Validation finale
   - Calcul scores
   - Statut publication
   ↓
6. SAUVEGARDE
   - JSON (complet)
   - Markdown (lisible)
```

## 🛠️ Dépannage

### Erreur "Token Notion invalide"

```bash
# Vérifier .env
cat .env | grep NOTION_TOKEN

# Tester connexion
python test_notion_connection.py
```

### Erreur "LLM Provider non configuré"

```bash
# Vérifier provider dans .env
echo $LLM_PROVIDER

# Vérifier clé API
echo $OPENAI_API_KEY
```

### Structured Outputs ne fonctionne pas

Le système a 3 niveaux de fallback :
1. Structured Outputs natif (OpenAI)
2. JSON mode (Anthropic, Mistral)
3. Parser JSON manuel (Ollama)

Si erreur persistante, vérifier :
- Version du package `langchain-openai >= 0.2.0`
- Modèle supporte structured outputs
- Format Pydantic correct

### Scores toujours bas

Vérifier :
- **Brief** : Assez détaillé ?
- **Intent** : Adapté au personnage ?
- **Créativité** : Pas trop basse (< 0.5) ni trop haute (> 0.9)
- **Contexte** : Notion accessible ?

## 📖 Ressources

### Documentation
- `docs/AGENT_ARCHITECTURE.md` - Architecture détaillée
- `docs/MCP_SETUP.md` - Configuration Notion
- `docs/MULTI_PROVIDER_GUIDE.md` - Support multi-provider
- `.cursor/rules/*.mdc` - Règles Cursor AI

### Exemples
- `examples/corrector_structured_example.py` - Structured outputs
- `demo_workflow.py` - Workflow complet
- `tests/test_real_data.py` - Personnages types

### Configuration
- `config/domain_configs/personnages_config.py` - Config personnages
- `config/notion_config.py` - Config Notion
- `env.example` - Template variables

## 🎯 Prochaines Étapes

1. **Domaines Supplémentaires**
   - Lieux (config à créer)
   - Communautés (config à créer)
   - Objets (config à créer)

2. **Fonctionnalités**
   - Export direct vers Notion (bases principales)
   - Génération par lot
   - Templates personnalisés

3. **Optimisations**
   - Cache résultats LLM
   - Parallélisation agents
   - Fine-tuning modèles

---

**Support** : Consulter `README.md` ou ouvrir une issue GitHub
**Version** : 1.0.0
**Dernière mise à jour** : Octobre 2025

