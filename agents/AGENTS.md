# Instructions Agents

## Architecture
Agents **génériques** configurés par `DomainConfig`, pas d'agents spécialisés par domaine.

## Agents Disponibles
1. **WriterAgent** : Génération contenu original
2. **ReviewerAgent** : Analyse cohérence narrative (retourne scores + issues)
3. **CorrectorAgent** : Correction linguistique (retourne corrections)
4. **ValidatorAgent** : Validation finale
5. **NotionAgent** : Export vers Notion

## Base Pattern
```python
from agents.base.base_agent import BaseAgent, AgentResult
from agents.base.domain_config import DomainConfig

class MyAgent(BaseAgent):
    def __init__(self, domain_config: DomainConfig, llm=None):
        super().__init__(domain_config, llm)
    
    def process(self, input_data, context=None) -> AgentResult:
        # self.domain_config pour spécificités
        # self.llm pour appels LLM
        pass
```

## LLM Adapter
**TOUJOURS** utiliser `LLMAdapter` pour abstraction provider :
```python
from agents.base.llm_utils import LLMAdapter

adapter = LLMAdapter(llm)
result = adapter.get_structured_output(prompt, schema=MySchema)
```

## Structured Outputs
**TOUJOURS** préférer structured outputs au parsing manuel :
```python
# ✅ Bon
from pydantic import BaseModel
class Result(BaseModel):
    field: str

result = adapter.get_structured_output(prompt, schema=Result)

# ❌ Mauvais
if '[CORRECTION:' in line:  # Fragile
    parts = line.split(']', 1)
```

## Notion Relation Resolver
Pour résoudre relations Notion (fuzzy matching) :
```python
from agents.notion_relation_resolver import NotionRelationResolver

resolver = NotionRelationResolver(fuzzy_threshold=0.80)
match = resolver.find_match("Humain modifié", "especes")
```

## Parsing LLM Output
- ReviewerAgent : Extraire scores + issues
- CorrectorAgent : Extraire corrections
- **Nettoyer** sections INSTRUCTIONS avant retour

