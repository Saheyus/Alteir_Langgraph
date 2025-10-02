# Architecture Multi-Agents - Système GDD Alteir

## 🎯 Analyse et Proposition d'Architecture

### Contexte du Projet
- **6 types de contenu** : Personnages, Lieux, Communautés, Espèces, Objets, Chronologie
- **4 rôles d'agents** : Writer, Reviewer, Corrector, Validator
- **Objectif** : Système flexible, maintenable et performant

---

## 📊 Comparaison des Approches

### Option 1 : Agents Purement Spécialisés par Domaine
```
CharacterWriterAgent, PlaceWriterAgent, CommunityWriterAgent...
CharacterReviewerAgent, PlaceReviewerAgent, CommunityReviewerAgent...
→ 24 agents au total (6 domaines × 4 rôles)
```

**Avantages** :
- ✅ Expertise maximale par domaine
- ✅ Prompts ultra-spécialisés
- ✅ Performance optimale

**Inconvénients** :
- ❌ Code redondant massif
- ❌ Maintenance cauchemardesque
- ❌ Scalabilité limitée

---

### Option 2 : Agents Purement Généralistes par Rôle
```
WriterAgent, ReviewerAgent, CorrectorAgent, ValidatorAgent
→ 4 agents au total
```

**Avantages** :
- ✅ Code mutualisé
- ✅ Maintenance simple
- ✅ Scalabilité facile

**Inconvénients** :
- ❌ Perte de spécificité
- ❌ Prompts génériques
- ❌ Qualité potentiellement moindre

---

### Option 3 : Architecture Hybride (RECOMMANDÉE) ⭐

**Agents avec Rôle + Configuration de Domaine**

```python
# Agent de base avec rôle défini
WriterAgent(domain_config: DomainConfig)
ReviewerAgent(domain_config: DomainConfig)
CorrectorAgent(domain_config: DomainConfig)
ValidatorAgent(domain_config: DomainConfig)

# Configuration par domaine
DomainConfig = {
    "domain": "personnages" | "lieux" | "communautes"...,
    "template": NotionTemplate,
    "validation_rules": List[Rule],
    "context_sources": List[str]
}
```

**Avantages** :
- ✅ **Code mutualisé** : 1 agent par rôle seulement
- ✅ **Spécialisation** : via configuration et prompts dynamiques
- ✅ **Extensibilité** : nouveau domaine = nouvelle config, pas nouveau code
- ✅ **Maintenance** : logique centralisée
- ✅ **Flexibilité** : mix de comportements possibles

**Architecture** :
```
agents/
├── base/
│   ├── base_agent.py          # Classe abstraite commune
│   └── domain_config.py       # Configurations par domaine
├── writer_agent.py            # Agent écrivain générique
├── reviewer_agent.py          # Agent relecteur générique
├── corrector_agent.py         # Agent correcteur générique
└── validator_agent.py         # Agent validateur générique

config/
└── domain_configs/
    ├── personnages_config.py  # Config spécifique personnages
    ├── lieux_config.py        # Config spécifique lieux
    ├── communautes_config.py  # Config spécifique communautés
    └── ...
```

---

## 🏗️ Architecture Détaillée Recommandée

### 1. Classe de Base (`BaseAgent`)

```python
class BaseAgent(ABC):
    """Classe abstraite pour tous les agents"""
    
    def __init__(self, domain_config: DomainConfig, llm: ChatOpenAI = None):
        self.domain = domain_config.domain
        self.template = domain_config.template
        self.validation_rules = domain_config.validation_rules
        self.context_sources = domain_config.context_sources
        self.llm = llm or self._create_default_llm()
    
    @abstractmethod
    def process(self, content: str, context: Dict) -> AgentResult:
        """Méthode à implémenter par chaque agent"""
        pass
    
    def gather_context(self) -> Dict:
        """Récupère le contexte depuis Notion"""
        # Commun à tous les agents
        pass
    
    def _build_system_prompt(self) -> str:
        """Construit le prompt système avec spécificités du domaine"""
        base_prompt = self.BASE_PROMPT
        domain_specific = self.domain_config.get_domain_instructions()
        return f"{base_prompt}\n\n{domain_specific}"
```

### 2. Configuration par Domaine (`DomainConfig`)

```python
@dataclass
class DomainConfig:
    """Configuration spécifique à un domaine"""
    domain: str  # "personnages", "lieux", etc.
    template: Dict[str, Any]  # Template Notion
    
    # Instructions spécifiques au domaine
    domain_instructions: str
    
    # Règles de validation
    validation_rules: List[ValidationRule]
    
    # Sources de contexte Notion
    context_sources: List[str]  # IDs des bases liées
    
    # Exemples de sortie
    examples: List[Dict[str, str]]
    
    # Paramètres spécifiques
    specific_params: Dict[str, Any]
```

### 3. Agents Spécialisés par Rôle

#### **WriterAgent**
- Rôle : Création de contenu initial
- Spécificités par domaine via `DomainConfig`
- Peut avoir des sous-configurations (ex: CharacterWriterConfig pour intent, level, etc.)

```python
class WriterAgent(BaseAgent):
    """Agent d'écriture générique configuré par domaine"""
    
    BASE_PROMPT = """Tu es un expert en création de contenu pour GDD..."""
    
    def __init__(self, domain_config: DomainConfig, writer_config: WriterConfig = None):
        super().__init__(domain_config)
        self.writer_config = writer_config or WriterConfig()
    
    def process(self, brief: str, context: Dict) -> WriterResult:
        # Logique d'écriture avec spécificités du domaine
        prompt = self._build_domain_specific_prompt(brief, context)
        result = self.llm.invoke(prompt)
        return self._parse_result(result)
```

#### **ReviewerAgent**
- Rôle : Vérification de la cohérence narrative
- Validation des liens entre éléments
- Contrôle de la cohérence du lore

```python
class ReviewerAgent(BaseAgent):
    """Agent de relecture générique configuré par domaine"""
    
    BASE_PROMPT = """Tu es un expert en cohérence narrative..."""
    
    def process(self, content: str, context: Dict) -> ReviewResult:
        # Vérifications spécifiques au domaine
        checks = self.domain_config.validation_rules
        issues = self._check_coherence(content, checks, context)
        suggestions = self._generate_suggestions(issues)
        return ReviewResult(issues=issues, suggestions=suggestions)
```

#### **CorrectorAgent**
- Rôle : Correction linguistique et stylistique
- Amélioration de la clarté
- Respect des conventions

```python
class CorrectorAgent(BaseAgent):
    """Agent de correction générique configuré par domaine"""
    
    BASE_PROMPT = """Tu es un expert en correction linguistique..."""
    
    def process(self, content: str, context: Dict) -> CorrectedResult:
        # Corrections avec style adapté au domaine
        style_guide = self.domain_config.specific_params.get("style_guide")
        corrected = self._apply_corrections(content, style_guide)
        return CorrectedResult(corrected=corrected, changes=self.changes)
```

#### **ValidatorAgent**
- Rôle : Validation finale
- Vérification des références croisées
- Contrôle de la complétude

```python
class ValidatorAgent(BaseAgent):
    """Agent de validation générique configuré par domaine"""
    
    BASE_PROMPT = """Tu es un expert en validation de contenu..."""
    
    def process(self, content: str, context: Dict) -> ValidationResult:
        # Validation avec règles du domaine
        required_fields = self.domain_config.template.keys()
        validation = self._validate_completeness(content, required_fields)
        cross_refs = self._validate_cross_references(content, context)
        return ValidationResult(valid=validation.passed, errors=validation.errors)
```

---

## 🔄 Workflows et Orchestration

### Workflow Standard (via LangGraph)

```python
from langgraph.graph import StateGraph, END

class ContentState(TypedDict):
    domain: str
    brief: str
    content: str
    review_notes: List[str]
    corrections: List[str]
    validated: bool
    context: Dict

# Créer le graphe
workflow = StateGraph(ContentState)

# Nœuds avec agents configurés
def writer_node(state: ContentState):
    domain_config = get_domain_config(state["domain"])
    agent = WriterAgent(domain_config)
    result = agent.process(state["brief"], state["context"])
    return {"content": result.text}

def reviewer_node(state: ContentState):
    domain_config = get_domain_config(state["domain"])
    agent = ReviewerAgent(domain_config)
    result = agent.process(state["content"], state["context"])
    return {"review_notes": result.issues, "content": result.improved}

def corrector_node(state: ContentState):
    domain_config = get_domain_config(state["domain"])
    agent = CorrectorAgent(domain_config)
    result = agent.process(state["content"], state["context"])
    return {"content": result.corrected, "corrections": result.changes}

def validator_node(state: ContentState):
    domain_config = get_domain_config(state["domain"])
    agent = ValidatorAgent(domain_config)
    result = agent.process(state["content"], state["context"])
    return {"validated": result.valid}

# Construire le workflow
workflow.add_node("writer", writer_node)
workflow.add_node("reviewer", reviewer_node)
workflow.add_node("corrector", corrector_node)
workflow.add_node("validator", validator_node)

workflow.set_entry_point("writer")
workflow.add_edge("writer", "reviewer")
workflow.add_edge("reviewer", "corrector")
workflow.add_edge("corrector", "validator")
workflow.add_edge("validator", END)

app = workflow.compile()
```

---

## 📁 Structure de Fichiers Proposée

```
agents/
├── __init__.py
├── base/
│   ├── __init__.py
│   ├── base_agent.py              # Classe abstraite BaseAgent
│   ├── domain_config.py           # Classe DomainConfig
│   └── agent_result.py            # Classes de résultats
├── writer_agent.py                # WriterAgent générique
├── reviewer_agent.py              # ReviewerAgent générique
├── corrector_agent.py             # CorrectorAgent générique
├── validator_agent.py             # ValidatorAgent générique
└── specialized/                   # (optionnel) agents très spécifiques
    └── character_writer_agent.py  # Si besoin de logique unique

config/
├── __init__.py
├── notion_config.py               # Config Notion existante
└── domain_configs/
    ├── __init__.py
    ├── personnages_config.py      # Config domaine personnages
    ├── lieux_config.py            # Config domaine lieux
    ├── communautes_config.py      # Config domaine communautés
    ├── especes_config.py          # Config domaine espèces
    ├── objets_config.py           # Config domaine objets
    └── chronologie_config.py      # Config domaine chronologie

workflows/
├── __init__.py
├── content_workflow.py            # Workflow principal
└── specialized_workflows.py       # Workflows spécifiques si besoin
```

---

## 🎯 Cas d'Usage : Personnages

### Configuration Spécifique

```python
# config/domain_configs/personnages_config.py
PERSONNAGES_CONFIG = DomainConfig(
    domain="personnages",
    template=PERSONNAGES_TEMPLATE,
    domain_instructions="""
    Pour les personnages:
    - Appliquer Orthogonalité rôle ↔ profondeur
    - Structure Surface/Profondeur/Monde
    - Temporalité IS/WAS/COULD-HAVE-BEEN
    - Dialogues variés et jouables
    """,
    validation_rules=[
        RequiredFieldRule(["Nom", "Type", "Espèce"]),
        CoherenceRule("Âge", "Chronologie"),
        RelationRule("Communautés", context_source="communautes"),
    ],
    context_sources=[
        "collection://1886e4d2-1b45-8145-879b-000b236239de",  # Communautés
        "collection://1886e4d2-1b45-81dd-9199-000b92800d69",  # Espèces
        "collection://1886e4d2-1b45-8163-9932-000bf0d9bccc",  # Lieux
    ],
    examples=[...],
    specific_params={
        "intent_modes": ["orthogonal_depth", "vocation_pure", ...],
        "dialogue_modes": ["parle", "gestuel", "telepathique", ...],
        "level_options": ["cameo", "standard", "major"]
    }
)
```

### Utilisation

```python
# Créer un personnage
domain_config = PERSONNAGES_CONFIG
writer_config = WriterConfig(intent="orthogonal_depth", level="standard")

writer = WriterAgent(domain_config, writer_config)
result = writer.process(
    brief="Un cartographe qui cache un secret",
    context=domain_config.gather_context()
)
```

---

## 🚀 Avantages de cette Architecture

### 1. **Maintenabilité**
- Code centralisé par rôle
- Modifications dans un seul endroit
- Tests unitaires simplifiés

### 2. **Extensibilité**
- Nouveau domaine = nouvelle config, pas nouveau code
- Nouveaux rôles facilement ajoutables
- Workflows composables

### 3. **Flexibilité**
- Mix de comportements via configuration
- Paramètres ajustables par domaine
- Agents réutilisables

### 4. **Performance**
- Spécialisation via prompts dynamiques
- Contexte optimisé par domaine
- Cache des configurations

### 5. **Qualité**
- Expertise maintenue via configurations riches
- Validation cohérente
- Standards unifiés

---

## 🔄 Migration du Code Existant

### CharacterWriterAgent → WriterAgent

```python
# Avant (spécialisé)
character_agent = CharacterWriterAgent(config)

# Après (générique avec config)
domain_config = PERSONNAGES_CONFIG
writer_config = WriterConfig(
    intent=config.intent,
    level=config.level,
    dialogue_mode=config.dialogue_mode
)
writer_agent = WriterAgent(domain_config, writer_config)
```

Le `CharacterWriterAgent` existant peut soit :
1. Être refactorisé en `WriterAgent` + `PERSONNAGES_CONFIG`
2. Rester comme exemple d'agent ultra-spécialisé dans `agents/specialized/`

---

## ✅ Recommandation Finale

**Adopter l'architecture hybride avec :**

1. **4 agents génériques** (Writer, Reviewer, Corrector, Validator)
2. **6+ configurations de domaine** (Personnages, Lieux, etc.)
3. **Workflows composables** via LangGraph
4. **Système de plugins** pour cas ultra-spécifiques

Cette approche offre le meilleur équilibre entre :
- Spécialisation (via config riche)
- Maintenabilité (code mutualisé)
- Extensibilité (nouveaux domaines faciles)
- Performance (prompts optimisés)

---

*Document créé : Octobre 2025*
*Version : 1.0*
