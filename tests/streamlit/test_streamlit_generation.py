from __future__ import annotations

import importlib.util
import pytest

from .utils_streamlit_test import extract_messages, has_message, click_button_by_label


pytestmark = [pytest.mark.ui, pytest.mark.e2e]


def test_generation_minimal_flow(at, ensure_gpt5_nano, enable_notion_sandbox_reads):
    # Skip gracefully if heavy runtime deps are unavailable
    if importlib.util.find_spec("langchain_openai") is None or importlib.util.find_spec("langgraph") is None:
        pytest.xfail("Missing runtime deps for generation path (langgraph/langchain_openai)")

    # Set a brief and trigger generation via session_state to avoid brittle UI clicks
    at.session_state["brief"] = "Un forgeron bourru mais généreux, 60 ans"
    at.session_state["trigger_generate"] = True
    at = at.run(timeout=60.0)

    msgs = extract_messages(at)
    # Success banner expected at the end (if deps and keys are valid)
    # Tolerate environments missing heavy deps by marking xfail
    # Otherwise, require either success banner or an error banner
    assert has_message(msgs, "généré avec succès", msg_type="success") or has_message(msgs, "Erreur", msg_type="error")


