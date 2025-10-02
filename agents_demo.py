# agents_demo.py
from typing import Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

# --- 0) Helpers ------------------------------------------------------------
def to_text(content: Any) -> str:
    """
    Normalise le contenu renvoyé par LangChain/Responses en texte.
    - content peut être une str, ou une liste de blocs (text/image/...).
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for p in content:
            # Cas dict-like (SDKs récents)
            if isinstance(p, dict):
                if "text" in p and isinstance(p["text"], str):
                    parts.append(p["text"])
                elif "type" in p and p["type"] == "output_text" and "content" in p:
                    parts.append(str(p["content"]))
                else:
                    # dernier recours: cast
                    parts.append(str(p))
            else:
                # objets message chunk (compatibilité)
                txt = getattr(p, "text", None)
                parts.append(txt if isinstance(txt, str) else str(p))
        return "".join(parts).strip()
    # fallback
    return str(content)

# --- 1) Modèle OpenAI via Responses API -----------------------------------
llm = ChatOpenAI(
    model="gpt-5-nano",
    use_responses_api=True,
    # Certains champs Responses passent via extra_body pour éviter le warning
    extra_body={
        "reasoning": {"effort": "minimal"},
        "max_output_tokens": 300,
    },
)

# --- 2) État partagé -------------------------------------------------------
class DocState(dict):
    text: str

# --- 3) Nœuds (agents) -----------------------------------------------------
def writer_node(state: DocState):
    resp = llm.invoke(
        f"Écris un paragraphe simple, très concis, sur : {state['text']}"
    )
    return {"text": to_text(resp.content)}

def reviewer_node(state: DocState):
    resp = llm.invoke(
        "Améliore la clarté et la cohérence du texte suivant, sans l'allonger inutilement :\n\n"
        + to_text(state["text"])
    )
    return {"text": to_text(resp.content)}

def corrector_node(state: DocState):
    resp = llm.invoke(
        "Corrige l’orthographe, la grammaire et la ponctuation de ce texte en conservant le sens :\n\n"
        + to_text(state["text"])
    )
    return {"text": to_text(resp.content)}

# --- 4) Graphe LangGraph ---------------------------------------------------
graph = StateGraph(DocState)
graph.add_node("writer", writer_node)
graph.add_node("reviewer", reviewer_node)
graph.add_node("corrector", corrector_node)

graph.set_entry_point("writer")
graph.add_edge("writer", "reviewer")
graph.add_edge("reviewer", "corrector")
graph.add_edge("corrector", END)

app = graph.compile()

if __name__ == "__main__":
    initial = {"text": "Les Crocs d'Améthyste dans mon GDD"}
    final = app.invoke(initial)
    print("Texte final :")
    print(to_text(final["text"]))
