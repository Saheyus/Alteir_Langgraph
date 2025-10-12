#!/usr/bin/env python3
"""
Exemple : CorrectorAgent avec Structured Outputs multi-fournisseur
"""
import sys
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field

sys.path.append(str(Path(__file__).parent.parent))

from agents.base.llm_utils import LLMAdapter

# ============================================================================
# 1. DÉFINIR LES SCHÉMAS PYDANTIC
# ============================================================================

class Correction(BaseModel):
    """Une correction effectuée"""
    type: str = Field(description="Type: orthographe, grammaire, style, clarté")
    original: str = Field(description="Texte original incorrect")
    corrected: str = Field(description="Texte corrigé")
    explanation: str = Field(description="Explication de la correction")

class CorrectionResult(BaseModel):
    """Résultat complet de la correction"""
    corrected_text: str = Field(description="Texte complet corrigé")
    corrections: List[Correction] = Field(description="Liste des corrections")
    summary: str = Field(description="Résumé des améliorations (2-3 phrases)")

# ============================================================================
# 2. UTILISATION AVEC DIFFÉRENTS FOURNISSEURS
# ============================================================================

def correct_with_structured_output(text: str, provider: str = "openai"):
    """
    Corrige un texte avec structured outputs
    
    Args:
        text: Texte à corriger
        provider: 'openai', 'anthropic', 'mistral', 'ollama'
    """
    
    # Créer le LLM selon le fournisseur
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model="gpt-5-nano",
            use_responses_api=True,
            extra_body={
                "reasoning": {"effort": "minimal"},
                "max_output_tokens": 1000,
            }
        )
    
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(
            model="claude-sonnet-4-5-20250929",  # Latest Claude Sonnet 4.5
            temperature=0.3
        )
    
    elif provider == "mistral":
        from langchain_mistralai import ChatMistralAI
        llm = ChatMistralAI(
            model="mistral-large-latest",
            temperature=0.3
        )
    
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        llm = ChatOllama(
            model="llama3.2",
            temperature=0.3,
            format="json"  # Force JSON mode
        )
    
    else:
        raise ValueError(f"Provider inconnu: {provider}")
    
    # Créer l'adapter
    adapter = LLMAdapter(llm)
    
    # Prompt de correction
    prompt = f"""Corrige ce texte en français :

TEXTE À CORRIGER:
{text}

INSTRUCTIONS:
1. Corrige l'orthographe, la grammaire, la ponctuation
2. Améliore la clarté et le style
3. Liste TOUTES les corrections effectuées
4. Fournis le texte complet corrigé
5. Résume les améliorations en 2-3 phrases"""
    
    # Obtenir le résultat structuré
    result = adapter.get_structured_output(
        prompt=prompt,
        schema=CorrectionResult
    )
    
    return result

# ============================================================================
# 3. DÉMONSTRATION
# ============================================================================

def main():
    """Test avec différents fournisseurs"""
    
    # Texte avec fautes volontaires
    text = """Les vérité du passé sont souvent plus sombre qu'ont ne le pense.
    J'ais découvert des artefact qui change tout ce qu'on savait.
    Parfois, je me demande si certain connaissance devrait resté enterré."""
    
    print("=" * 70)
    print("TEXTE ORIGINAL:")
    print("=" * 70)
    print(text)
    print()
    
    # Tester avec OpenAI (si disponible)
    try:
        print("=" * 70)
        print("CORRECTION AVEC OPENAI (GPT-5-nano)")
        print("=" * 70)
        
        result = correct_with_structured_output(text, provider="openai")
        
        print("\nTEXTE CORRIGÉ:")
        print(result.corrected_text)
        
        print(f"\n📝 CORRECTIONS ({len(result.corrections)}):")
        for i, corr in enumerate(result.corrections, 1):
            print(f"\n{i}. [{corr.type.upper()}]")
            print(f"   Original:  {corr.original}")
            print(f"   Corrigé:   {corr.corrected}")
            print(f"   Raison:    {corr.explanation}")
        
        print(f"\n💡 RÉSUMÉ:")
        print(f"   {result.summary}")
        
    except Exception as e:
        print(f"[SKIP] OpenAI non disponible: {e}")
    
    # Tester avec Ollama (local, pas de clé API nécessaire)
    try:
        print("\n" + "=" * 70)
        print("CORRECTION AVEC OLLAMA (llama3.2 local)")
        print("=" * 70)
        
        result_ollama = correct_with_structured_output(text, provider="ollama")
        
        print("\nTEXTE CORRIGÉ:")
        print(result_ollama.corrected_text)
        
        print(f"\n📝 {len(result_ollama.corrections)} corrections effectuées")
        
    except Exception as e:
        print(f"[SKIP] Ollama non disponible: {e}")
    
    print("\n" + "=" * 70)
    print("✅ L'approche fonctionne avec n'importe quel fournisseur !")
    print("=" * 70)

if __name__ == "__main__":
    main()

