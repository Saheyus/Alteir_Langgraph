from __future__ import annotations

import pytest

from .utils_streamlit_test import extract_messages, has_message, click_button_by_label


pytestmark = [pytest.mark.ui, pytest.mark.e2e]


def test_context_preload_and_summary_count(at, enable_notion_sandbox_reads):
    # Should show a preload info line with count
    msgs = extract_messages(at)
    assert any("préchargée(s)" in m.get("text", "") for m in msgs if m.get("type") == "info")


def test_auto_suggestion_flow(at, enable_notion_sandbox_reads):
    # Provide a brief to enable suggestion
    at.session_state["brief"] = "alchimiste du Leviathan"
    at = at.run()
    # Click auto-suggestion button
    at = click_button_by_label(at, "Suggérer automatiquement")
    msgs = extract_messages(at)
    # Expect an info line indicating suggestions found or offline warning
    assert has_message(msgs, "suggestion", msg_type=None) or has_message(msgs, "hors ligne", msg_type="warning")


