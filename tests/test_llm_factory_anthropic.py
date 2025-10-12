#!/usr/bin/env python3
"""Tests for Anthropic factory path in create_llm."""

from __future__ import annotations

import types

from app.streamlit_app.generation import create_llm
from app.streamlit_app.constants import MODELS


def test_create_llm_anthropic_instantiates_chat_anthropic(monkeypatch):
    """create_llm should return a ChatAnthropic instance for Anthropic provider."""

    class _FakeChatAnthropic:
        def __init__(self, model: str, temperature: float, max_tokens: int):
            self.model = model
            self.temperature = temperature
            self.max_tokens = max_tokens

    # Patch import path used in create_llm
    import sys
    fake_module = types.SimpleNamespace(ChatAnthropic=_FakeChatAnthropic)
    sys.modules['langchain_anthropic'] = fake_module

    model_info = MODELS["Claude 4.5 Sonnet"]

    llm = create_llm(
        model_name="Claude 4.5 Sonnet",
        model_config=model_info,
        creativity=0.6,
        reasoning_effort="low",
        verbosity=None,
        max_tokens=1234,
    )

    assert isinstance(llm, _FakeChatAnthropic)
    assert llm.model == model_info["name"]
    assert llm.temperature == 0.6
    assert llm.max_tokens == 1234


