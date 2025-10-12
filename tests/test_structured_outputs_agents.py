"""Tests for structured outputs paths in Reviewer, Corrector, Validator using a fake LLM."""

from __future__ import annotations

from typing import Any

class _FakeLLM:
    """Minimal fake LLM duck-typing the features we need."""

    def __init__(self, payload):
        self._payload = payload

    def with_structured_output(self, schema):
        class _S:
            def __init__(self, payload):
                self.payload = payload

            def invoke(self, prompt):
                return schema.model_validate(self.payload)

        return _S(self._payload)

    def invoke(self, input, **kwargs):
        return type("R", (), {"content": str(self._payload)})

from agents.reviewer_agent import ReviewerAgent
from agents.corrector_agent import CorrectorAgent
from agents.validator_agent import ValidatorAgent
from config.domain_configs.personnages_config import PERSONNAGES_CONFIG




def test_reviewer_structured_outputs():
    payload = {
        "issues": [
            {
                "severity": "major",
                "category": "coherence",
                "description": "Contradiction mineure",
                "suggestion": "Aligner avec le contexte",
            }
        ],
        "improvements": ["Ajouter un exemple concret"],
        "coherence_score": 0.8,
        "improved_content": "Texte amélioré",
    }
    agent = ReviewerAgent(PERSONNAGES_CONFIG, llm=_FakeLLM(payload))
    res = agent.process("content")
    assert res.success
    assert res.coherence_score == 0.8
    assert res.issues and res.issues[0].severity == "major"


def test_corrector_structured_outputs():
    payload = {
        "corrected_content": "Texte corrigé",
        "corrections": [
            {"type": "orthographe", "original": "errur", "corrected": "erreur", "explanation": None}
        ],
        "improvement_summary": "Corrections appliquées",
    }
    agent = CorrectorAgent(PERSONNAGES_CONFIG, llm=_FakeLLM(payload))
    res = agent.process("content")
    assert res.success
    assert res.content == "Texte corrigé"
    assert res.corrections and res.corrections[0].type == "orthographe"


def test_validator_structured_outputs():
    payload = {
        "validation_errors": [
            {"field": "Nom", "error_type": "missing", "description": "Nom requis", "severity": "critical"}
        ],
        "completeness_score": 0.6,
        "quality_score": 0.7,
        "is_valid": False,
        "ready_for_publication": False,
    }
    agent = ValidatorAgent(PERSONNAGES_CONFIG, llm=_FakeLLM(payload))
    res = agent.process("content")
    assert res.success
    assert res.completeness_score == 0.6
    assert res.quality_score == 0.7
    assert res.validation_errors and res.validation_errors[0].field == "Nom"


# ============================================================================
# TESTS AVEC LLM RÉEL
# ============================================================================

import pytest


@pytest.mark.llm_api
@pytest.mark.slow
def test_reviewer_with_real_llm(test_llm):
    """Test ReviewerAgent avec LLM réel pour structured outputs"""
    content = """
    # Test Personnage
    
    **Nom**: Test
    **Type**: PNJ
    **Genre**: Masculin
    
    Un personnage de test simple.
    """
    
    agent = ReviewerAgent(PERSONNAGES_CONFIG, llm=test_llm)
    res = agent.process(content)
    
    # Vérifier que structured outputs fonctionne
    assert res.success
    assert hasattr(res, 'coherence_score')
    assert hasattr(res, 'issues')
    assert hasattr(res, 'improvements')
    
    # Vérifier types
    assert isinstance(res.coherence_score, (int, float))
    assert isinstance(res.issues, list)
    assert isinstance(res.improvements, list)
    
    print(f"\n✓ ReviewerAgent structured outputs OK")
    print(f"  - Coherence: {res.coherence_score}")
    print(f"  - Issues: {len(res.issues)}")
    print(f"  - Improvements: {len(res.improvements)}")


@pytest.mark.llm_api
@pytest.mark.slow
def test_corrector_with_real_llm(test_llm):
    """Test CorrectorAgent avec LLM réel pour structured outputs"""
    content = """
    # Test Personage
    
    **Nom**: Test
    **Type**: PNJ
    
    Un personage avec des erruer de frappe.
    """
    
    agent = CorrectorAgent(PERSONNAGES_CONFIG, llm=test_llm)
    res = agent.process(content)
    
    # Vérifier structured outputs
    assert res.success
    assert hasattr(res, 'content')  # Contenu corrigé
    assert hasattr(res, 'corrections')
    
    # Vérifier types
    assert isinstance(res.content, str)
    assert isinstance(res.corrections, list)
    
    # Le contenu corrigé devrait être différent (ou identique si pas d'erreurs)
    assert len(res.content) > 0
    
    print(f"\n✓ CorrectorAgent structured outputs OK")
    print(f"  - Corrections appliquées: {len(res.corrections)}")


@pytest.mark.llm_api
@pytest.mark.slow
def test_validator_with_real_llm(test_llm):
    """Test ValidatorAgent avec LLM réel pour structured outputs"""
    content = """
    # Test Personnage
    
    **Nom**: Test Complet
    **Type**: PNJ
    **Genre**: Masculin
    **Espèce**: Humain
    **Âge**: 30 ans
    
    Un personnage de test complet avec tous les champs requis.
    """
    
    agent = ValidatorAgent(PERSONNAGES_CONFIG, llm=test_llm)
    res = agent.process(content)
    
    # Vérifier structured outputs
    assert res.success
    assert hasattr(res, 'is_valid')
    assert hasattr(res, 'completeness_score')
    assert hasattr(res, 'quality_score')
    assert hasattr(res, 'validation_errors')
    
    # Vérifier types
    assert isinstance(res.is_valid, bool)
    assert isinstance(res.completeness_score, (int, float))
    assert isinstance(res.quality_score, (int, float))
    assert isinstance(res.validation_errors, list)
    
    # Scores devraient être entre 0 et 1
    assert 0 <= res.completeness_score <= 1
    assert 0 <= res.quality_score <= 1
    
    print(f"\n✓ ValidatorAgent structured outputs OK")
    print(f"  - Valid: {res.is_valid}")
    print(f"  - Completeness: {res.completeness_score}")
    print(f"  - Quality: {res.quality_score}")
    print(f"  - Errors: {len(res.validation_errors)}")


