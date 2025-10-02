# 🤖 Système Multi-Agents GDD Alteir

Système local d'écriture, relecture et correction pour le Game Design Document Alteir, utilisant LangGraph et MCP Notion.

## 📋 Vue d'Ensemble

### Architecture Hybride
- **4 agents génériques** configurés par domaine :
  - **WriterAgent** : Génération de contenu original
  - **ReviewerAgent** : Analyse de cohérence narrative
  - **CorrectorAgent** : Correction linguistique
  - **ValidatorAgent** : Validation finale

- **6+ domaines de contenu** :
  - Personnages
  - Lieux
  - Communautés
  - Espèces
  - Objets
  - Chronologie

### Workflow Standard
```
Brief → Writer → Reviewer → Corrector → Validator → Publication
```

## 🚀 Démarrage Rapide

### 1. Installation

```bash
# Cloner le projet
git clone <url>
cd "Langgraph Alteir"

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp env.example .env
# Éditer .env avec vos clés API
```

### 2. Utiliser l'Interface

#### Option A : Interface Web Streamlit (Recommandé)
```bash
streamlit run app_streamlit.py
```
Interface graphique avec :
- Formulaire de création de personnage
- Configuration des paramètres (intent, level, dialogue, créativité)
- Visualisation en temps réel
- Consultation des résultats générés
- Métriques et scores détaillés

#### Option B : Interface CLI
```bash
python app_cli.py
```
Interface en ligne de commande avec :
- Menu interactif
- Assistant de création
- Visualisation des résultats
- Configuration

#### Option C : LangGraph Studio
```bash
# Installer LangGraph CLI
pip install langgraph-cli

# Lancer le studio
langgraph dev

# Ouvrir http://localhost:8000
```
Interface visuelle avec :
- Graphe du workflow
- Exécution pas à pas
- Inspection des états
- Historique complet

#### Option C : Workflow Simple
```bash
python workflows/content_workflow.py
```
Exécution basique avec sortie console et fichiers générés.

### 3. Tester un Agent Individuel

```bash
# Writer
python agents/writer_agent.py

# Reviewer
python agents/reviewer_agent.py

# Corrector
python agents/corrector_agent.py

# Validator
python agents/validator_agent.py
```

## 📂 Outputs

Les résultats sont sauvegardés dans `outputs/` :

### Format JSON
```json
{
  "domain": "personnages",
  "brief": "...",
  "content": "...",
  "coherence_score": 0.85,
  "completeness_score": 0.90,
  "quality_score": 0.80,
  "is_valid": true,
  "ready_for_publication": true,
  "history": [...],
  "review_issues": [...],
  "corrections": [...]
}
```

### Format Markdown
```markdown
# Personnages - 20250102_143022

**Brief:** Un marchand d'ombres...

---

## Contenu Final
[Contenu généré]

---

## Métriques
- Score de cohérence: 0.85
- Score de complétude: 0.90
- ...
```

## 🏗️ Structure du Projet

```
.
├── agents/                    # Agents du système
│   ├── base/                 # Classes de base
│   │   ├── base_agent.py     # Agent abstrait
│   │   └── domain_config.py  # Configuration par domaine
│   ├── writer_agent.py       # Agent d'écriture
│   ├── reviewer_agent.py     # Agent de relecture
│   ├── corrector_agent.py    # Agent de correction
│   └── validator_agent.py    # Agent de validation
│
├── config/                    # Configuration
│   ├── notion_config.py      # Config Notion/MCP
│   └── domain_configs/       # Configs par domaine
│       └── personnages_config.py
│
├── workflows/                 # Workflows LangGraph
│   └── content_workflow.py   # Workflow complet
│
├── outputs/                   # Résultats générés
│   ├── *.json               # Données complètes
│   └── *.md                 # Contenu formaté
│
├── demo_workflow.py          # Démo avec Rich
├── langgraph.json            # Config LangGraph Studio
└── README.md                 # Ce fichier
```

## 🔧 Utilisation Avancée

### Créer un Personnage Personnalisé

```python
from workflows.content_workflow import ContentWorkflow, WriterConfig
from config.domain_configs.personnages_config import PERSONNAGES_CONFIG

# Créer le workflow
workflow = ContentWorkflow(PERSONNAGES_CONFIG)

# Configurer
brief = "Un alchimiste qui transforme les émotions..."
config = WriterConfig(
    intent="orthogonal_depth",
    level="major",
    dialogue_mode="parle",
    creativity=0.8
)

# Exécuter
result = workflow.run(brief, config)

# Sauvegarder
workflow.save_results(result)
```

### Ajouter un Nouveau Domaine

1. Créer `config/domain_configs/lieux_config.py`
2. Définir `LIEUX_CONFIG` avec template et règles
3. Utiliser avec `ContentWorkflow(LIEUX_CONFIG)`

## 📊 Métriques de Qualité

- **Cohérence** (0.0-1.0) : Intégration narrative
- **Complétude** (0.0-1.0) : Présence des champs requis
- **Qualité** (0.0-1.0) : Originalité et respect des principes

### Critères de Publication
- ✅ Aucune erreur critique
- ✅ Score complétude ≥ 0.8
- ✅ Score qualité ≥ 0.7
- ✅ Références valides

## 🔗 Intégration Notion

### Configuration MCP
1. Créer une intégration Notion
2. Ajouter `NOTION_TOKEN` dans `.env`
3. Configurer les permissions (voir `docs/MCP_SETUP.md`)

### Bases de Données
- Personnages : `1886e4d21b4581a29340f77f5f2e5885`
- Lieux : `1886e4d21b4581eda022ea4e0f1aba5f`
- Communautés : `1886e4d21b4581dea4f4d01beb5e1be2`
- Espèces : `1886e4d21b4581e9a768df06185c1aea`

## 📝 Conventions

### Principes Narratifs (Personnages)
- **Orthogonalité rôle ↔ profondeur**
- **Surface / Profondeur / Monde**
- **Temporalité IS / WAS / COULD-HAVE-BEEN**
- **Show > Tell**
- **Blancs actifs**

Voir `rules.mdc` pour plus de détails.

## 🧪 Tests

```bash
# Test de configuration Notion
python test_notion_connection.py

# Test API 2025-09-03
python test_notion_api_2025.py

# Test sandbox
python test_sandbox_connection.py
```

## 📚 Documentation

- **Architecture** : `docs/AGENT_ARCHITECTURE.md`
- **MCP Setup** : `docs/MCP_SETUP.md`
- **Règles** : `rules.mdc`

## 🎯 Prochaines Étapes

- [ ] Intégration MCP réelle (création dans Notion)
- [ ] Ajout domaines Lieux, Communautés, Espèces
- [ ] Interface web avec Streamlit
- [ ] Support modèles locaux (Ollama)

## 📄 Licence

Projet personnel - Alteir GDD

