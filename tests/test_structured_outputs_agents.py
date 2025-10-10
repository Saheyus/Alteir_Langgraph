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


