import types
from typing import Any, Iterator, List

from agents.base.llm_utils import LLMAdapter


class _FakeChunk:
    def __init__(self, content: Any):
        self.content = content


class _FakeLLM:
    """
    Minimal fake LLM exposing .stream() and .invoke() to exercise LLMAdapter.stream_text.
    Produces reasoning parts first, then output text parts, similar to GPT-5 Responses API.
    """

    def __init__(self, parts_sequence: List[Any]):
        self._sequence = parts_sequence

    def stream(self, messages: Any) -> Iterator[_FakeChunk]:
        for item in self._sequence:
            yield _FakeChunk(item)

    def invoke(self, messages: Any):  # pragma: no cover - fallback path not used here
        return _FakeChunk("fallback response text")


def test_stream_text_ignores_reasoning_when_disabled():
    # Simulate reasoning deltas followed by output_text deltas
    seq = [
        [
            {"type": "reasoning.delta", "text": "Thinking 1. "},
            {"type": "reasoning.delta", "text": "Thinking 2. "},
        ],
        [
            {"type": "output_text.delta", "text": "Hello "},
            {"type": "output_text.delta", "text": "world"},
        ],
    ]

    adapter = LLMAdapter(_FakeLLM(seq))
    chunks = list(adapter.stream_text([{"role": "user", "content": "hi"}], include_reasoning=False))

    # Should yield only text, ignoring reasoning parts
    assert any(isinstance(c, str) and c for c in chunks), "Expected non-empty text chunks"
    text = "".join([c for c in chunks if isinstance(c, str)])
    assert "Hello" in text and "world" in text
    assert "Thinking" not in text


def test_stream_text_emits_both_fields_when_reasoning_enabled():
    seq = [
        [
            {"type": "reasoning.delta", "text": "Thinking 1. "},
            {"type": "reasoning.delta", "text": "Thinking 2. "},
        ],
        [
            {"type": "output_text.delta", "text": "Hello "},
            {"type": "output_text.delta", "text": "world"},
        ],
    ]

    adapter = LLMAdapter(_FakeLLM(seq))
    chunks = list(adapter.stream_text([{"role": "user", "content": "hi"}], include_reasoning=True))

    # Should produce dicts when reasoning arrives, and strings for plain text
    assert any(isinstance(c, dict) and (c.get("reasoning") or c.get("text")) for c in chunks)
    collected_text = []
    collected_reasoning = []
    for c in chunks:
        if isinstance(c, str):
            collected_text.append(c)
        elif isinstance(c, dict):
            if c.get("text"):
                collected_text.append(c["text"])  # may be empty sometimes
            if c.get("reasoning"):
                collected_reasoning.append(c["reasoning"])  # may be incremental

    assert "Hello" in "".join(collected_text)
    assert "world" in "".join(collected_text)
    assert "Thinking" in "".join(collected_reasoning)


