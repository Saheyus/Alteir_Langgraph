# 🔄 Guide Multi-Fournisseur LLM

Ce guide explique comment utiliser le système avec différents fournisseurs LLM (OpenAI, Anthropic, Mistral, Ollama, etc.).

## 🎯 Stratégie

### Architecture Agnostique

Le système utilise **`LLMAdapter`** pour abstraire les différences entre fournisseurs :

```python
from agents.base.llm_utils import LLMAdapter

# Fonctionne avec n'importe quel LLM
adapter = LLMAdapter(llm)

# Obtenir une sortie structurée
result = adapter.get_structured_output(
    prompt="Corrige ce texte...",
    schema=CorrectionResult
)
```

### 3 Niveaux de Fallback

1. **Structured Outputs natifs** (OpenAI, Anthropic) → JSON garanti
2. **JSON mode** (Mistral, Ollama) → Parsing JSON du texte
3. **Parser manuel** (fallback) → Regex/extraction custom

---

## 📦 Fournisseurs Supportés

### 1. **OpenAI** (Recommandé pour production)

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-5-nano",  # Rapide et économique
    use_responses_api=True,
    extra_body={
        "reasoning": {"effort": "minimal"},
        "max_output_tokens": 1000,
    }
)
```

**Avantages :**
- ✅ Structured Outputs natifs (100% fiable)
- ✅ GPT-5-nano très rapide
- ✅ Reasoning intégré
- ❌ Nécessite clé API payante

### 2. **Anthropic Claude**

```python
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    temperature=0.3
)
```

**Avantages :**
- ✅ Excellent en français
- ✅ JSON mode fiable
- ✅ Contexte 200k tokens
- ❌ Plus cher que GPT-5-nano

### 3. **Mistral AI**

```python
from langchain_mistralai import ChatMistralAI

llm = ChatMistralAI(
    model="mistral-large-latest",
    temperature=0.3
)
```

**Avantages :**
- ✅ Français natif
- ✅ Bon rapport qualité/prix
- ⚠️ JSON mode, parsing nécessaire

### 4. **Ollama** (Local, gratuit)

```python
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="llama3.2",  # ou mistral, qwen, etc.
    temperature=0.3,
    format="json"
)
```

**Avantages :**
- ✅ Totalement gratuit et local
- ✅ Pas de limite de requêtes
- ✅ Confidentialité garantie
- ❌ Qualité moindre que GPT-5
- ❌ Plus lent (dépend du GPU)

---

## 🔧 Configuration par Environnement

### Fichier `.env`

```bash
# Production : OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Dev : Anthropic
# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-...

# Local : Ollama
# LLM_PROVIDER=ollama
# OLLAMA_BASE_URL=http://localhost:11434
```

### Code Adaptatif

```python
import os
from agents.base.llm_utils import LLMAdapter

def create_llm():
    """Crée le LLM selon l'environnement"""
    provider = os.getenv("LLM_PROVIDER", "openai")
    
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-5-nano", use_responses_api=True)
    
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model="claude-3-5-sonnet-20241022")
    
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model="llama3.2", format="json")
    
    else:
        raise ValueError(f"Provider inconnu: {provider}")

# Dans vos agents
llm = create_llm()
adapter = LLMAdapter(llm)
```

---

## 📝 Utilisation dans les Agents

### Exemple : CorrectorAgent

```python
from pydantic import BaseModel, Field
from typing import List

class Correction(BaseModel):
    type: str
    original: str
    corrected: str
    explanation: str

class CorrectionResult(BaseModel):
    corrected_text: str
    corrections: List[Correction]
    summary: str

class CorrectorAgent:
    def __init__(self, llm):
        self.adapter = LLMAdapter(llm)
    
    def process(self, text: str) -> CorrectionResult:
        prompt = f"Corrige ce texte: {text}"
        
        # Fonctionne avec TOUS les fournisseurs
        result = self.adapter.get_structured_output(
            prompt=prompt,
            schema=CorrectionResult
        )
        
        return result
```

---

## 🧪 Tests Multi-Fournisseur

```bash
# Tester avec OpenAI
LLM_PROVIDER=openai python examples/corrector_structured_example.py

# Tester avec Ollama (local)
LLM_PROVIDER=ollama python examples/corrector_structured_example.py

# Tester avec Anthropic
LLM_PROVIDER=anthropic python examples/corrector_structured_example.py
```

---

## 📊 Comparaison des Fournisseurs

| Fournisseur | Qualité | Vitesse | Prix | Structured | Local |
|-------------|---------|---------|------|------------|-------|
| **OpenAI GPT-5-nano** | ⭐⭐⭐⭐⭐ | ⚡⚡⚡ | 💰 | ✅ Natif | ❌ |
| **Anthropic Claude** | ⭐⭐⭐⭐⭐ | ⚡⚡ | 💰💰 | ✅ JSON | ❌ |
| **Mistral Large** | ⭐⭐⭐⭐ | ⚡⚡⚡ | 💰 | ⚠️ JSON | ❌ |
| **Ollama llama3.2** | ⭐⭐⭐ | ⚡ | 🆓 | ⚠️ JSON | ✅ |

---

## 💡 Recommandations

### Production
- **OpenAI GPT-5-nano** : Meilleur rapport qualité/prix/vitesse
- Structured Outputs garantis, pas de parsing

### Développement Local
- **Ollama** : Gratuit, illimité, privé
- Qualité suffisante pour les tests

### Gros Volumes
- **Mistral** : Bon prix, français natif
- Moins cher que Claude

### Maximum Qualité
- **Claude 3.5 Sonnet** : Meilleur en compréhension
- Plus cher mais excellent

---

## 🔒 Sécurité & Confidentialité

### Données Sensibles
➡️ **Utilisez Ollama local** : Aucune donnée ne quitte votre machine

### Production Publique
➡️ **OpenAI ou Anthropic** : Infrastructure fiable, SLA garantis

### Conformité RGPD
➡️ **Mistral (EU)** : Hébergé en Europe, conforme RGPD

---

## 🚀 Migration entre Fournisseurs

Grâce à `LLMAdapter`, la migration est **sans modification de code** :

```python
# Avant (OpenAI uniquement)
llm = ChatOpenAI(model="gpt-5-nano")

# Après (n'importe quel provider)
llm = create_llm()  # Lit LLM_PROVIDER depuis .env

# Le reste du code reste IDENTIQUE
adapter = LLMAdapter(llm)
result = adapter.get_structured_output(...)
```

---

## 📚 Ressources

- [LangChain Providers](https://python.langchain.com/docs/integrations/chat/)
- [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)
- [Ollama Models](https://ollama.com/library)
- [Anthropic Claude](https://www.anthropic.com/claude)
- [Mistral AI](https://mistral.ai/)

