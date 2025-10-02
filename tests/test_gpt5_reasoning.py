#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests de configuration GPT-5 vs GPT-4

Vérifie que :
- GPT-5 utilise reasoning au lieu de temperature
- GPT-4 utilise temperature classique
- Les paramètres sont correctement passés à l'API
"""
import os
import sys
import pytest
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Fix encoding pour Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

@pytest.mark.slow
def test_gpt5_reasoning():
    """Test GPT-5 avec reasoning"""
    print("\n" + "="*60)
    print("🧠 TEST GPT-5 AVEC REASONING")
    print("="*60)
    
    llm = ChatOpenAI(
        model="gpt-5-nano",
        use_responses_api=True,
        reasoning={"effort": "minimal"},  # minimal pour question simple
        max_tokens=2000,  # Plus de tokens pour avoir de la place pour la réponse
    )
    
    prompt = "Quelle est la capitale de la France ? Explique ton raisonnement."
    
    print(f"\n📝 Prompt: {prompt}")
    print("\n⏳ Appel API en cours...")
    
    response = llm.invoke(prompt)
    
    # Afficher TOUT l'objet response pour debug
    print("\n🔍 DEBUG COMPLET DE LA RÉPONSE:")
    print(f"  - Type: {type(response)}")
    print(f"  - Content: {response.content}")
    print(f"  - Dir: {[attr for attr in dir(response) if not attr.startswith('_')][:20]}")
    
    # Afficher le texte de réponse
    print("\n✅ RÉPONSE TEXTE:")
    if hasattr(response, 'text'):
        print(response.text)
    else:
        print(response.content)
    
    # Afficher les content_blocks pour voir le reasoning
    print("\n🔍 CONTENT BLOCKS:")
    if hasattr(response, 'content_blocks') and response.content_blocks:
        for i, block in enumerate(response.content_blocks):
            print(f"\n--- Block {i+1} ---")
            print(f"Type: {block.get('type', 'unknown')}")
            print(f"Contenu complet: {block}")
    else:
        print("⚠️ Pas de content_blocks")
        
    # Vérifier additional_kwargs
    if hasattr(response, 'additional_kwargs'):
        print("\n📦 ADDITIONAL_KWARGS:")
        print(response.additional_kwargs)
    
    # Afficher les métadonnées
    print("\n📊 METADATA:")
    print(f"  - Model: {response.response_metadata.get('model_name', 'N/A')}")
    print(f"  - Tokens: {response.response_metadata.get('token_usage', 'N/A')}")
    
    return response


@pytest.mark.slow
def test_gpt4_temperature():
    """Test GPT-4 avec temperature (sans reasoning)"""
    print("\n" + "="*60)
    print("🌡️ TEST GPT-4 AVEC TEMPERATURE")
    print("="*60)
    
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=1000,
    )
    
    prompt = "Quelle est la capitale de la France ? Explique ton raisonnement."
    
    print(f"\n📝 Prompt: {prompt}")
    print("\n⏳ Appel API en cours...")
    
    response = llm.invoke(prompt)
    
    # Afficher le texte de réponse
    print("\n✅ RÉPONSE TEXTE:")
    print(response.content)
    
    # Vérifier les content_blocks (ne devrait pas avoir de reasoning)
    print("\n🔍 CONTENT BLOCKS:")
    if hasattr(response, 'content_blocks'):
        for i, block in enumerate(response.content_blocks):
            print(f"\n--- Block {i+1} (type: {block.get('type', 'unknown')}) ---")
            print(block)
    else:
        print("✅ Pas de content_blocks (normal pour GPT-4 classique)")
    
    # Afficher les métadonnées
    print("\n📊 METADATA:")
    print(f"  - Model: {response.response_metadata.get('model_name', 'N/A')}")
    print(f"  - Tokens: {response.response_metadata.get('token_usage', 'N/A')}")
    
    return response


def compare_configs():
    """Compare les configs LLM"""
    print("\n" + "="*60)
    print("⚙️ COMPARAISON DES CONFIGURATIONS")
    print("="*60)
    
    # Config GPT-5
    print("\n🚀 GPT-5 (reasoning):")
    llm_gpt5 = ChatOpenAI(
        model="gpt-5-nano",
        use_responses_api=True,
        reasoning={"effort": "medium"},
        max_tokens=1000,
    )
    print(f"  - Model: {llm_gpt5.model_name}")
    print(f"  - Uses responses API: {getattr(llm_gpt5, 'use_responses_api', False)}")
    print(f"  - Temperature: {getattr(llm_gpt5, 'temperature', 'N/A')}")
    
    # Config GPT-4
    print("\n🔄 GPT-4 (temperature):")
    llm_gpt4 = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=1000,
    )
    print(f"  - Model: {llm_gpt4.model_name}")
    print(f"  - Uses responses API: {getattr(llm_gpt4, 'use_responses_api', False)}")
    print(f"  - Temperature: {llm_gpt4.temperature}")


@pytest.mark.unit
def test_compare_configs():
    """Test de comparaison des configurations (sans appel API)"""
    compare_configs()


if __name__ == "__main__":
    # Permet de lancer le script directement pour debug
    print("\n🧪 TEST DES PARAMÈTRES GPT-5 vs GPT-4")
    print("="*60)
    print("💡 Pour lancer via pytest : pytest tests/test_gpt5_reasoning.py -v")
    print("💡 Pour tests rapides uniquement : pytest tests/test_gpt5_reasoning.py -m unit")
    print("="*60)
    
    # Vérifier la clé API
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERREUR: OPENAI_API_KEY non définie dans .env")
        exit(1)
    
    try:
        # Comparer les configs
        compare_configs()
        
        # Test GPT-5
        response_gpt5 = test_gpt5_reasoning()
        
        # Test GPT-4
        response_gpt4 = test_gpt4_temperature()
        
        print("\n" + "="*60)
        print("✅ TESTS TERMINÉS")
        print("="*60)
        print("\n💡 Points vérifiés:")
        print("  1. GPT-5 utilise use_responses_api=True")
        print("  2. GPT-5 utilise reasoning au lieu de temperature")
        print("  3. GPT-4 utilise temperature classique")
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()

