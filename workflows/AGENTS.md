# Instructions Workflows

## Pattern LangGraph
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class MyState(TypedDict):
    content: str
    metadata: dict

def node_function(state: MyState) -> dict:
    return {"content": "..."}

graph = StateGraph(MyState)
graph.add_node("node1", node_function)
graph.add_edge("node1", END)
app = graph.compile()
```

## Workflow Principal
`content_workflow.py` : Workflow complet 4 agents
1. Writer → génération
2. Reviewer → analyse
3. Corrector → correction
4. Validator → validation finale

## Sauvegarde Résultats
- **JSON** (`outputs/*.json`) : État complet, métadonnées
- **Markdown** (`outputs/*.md`) : Contenu formaté, lisible

## Nommage Fichiers
Format : `domain_camelCaseName_timestamp`
```python
# Exemple : personnages_drarusLumenflex_20251003_010511.json
filename = f"{domain}_{camel_case_name}_{timestamp}"
```

## LLM Instance
Workflow accepte LLM optionnel :
```python
workflow = ContentWorkflow(
    domain_config=config,
    llm=custom_llm  # Optionnel, sinon défaut gpt-4o-mini
)
```

## État Workflow
```python
{
    "brief": str,
    "content": str,
    "review": {...},
    "corrections": [...],
    "validation": {...},
    "scores": {...}
}
```

