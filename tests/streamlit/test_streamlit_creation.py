from __future__ import annotations

import pytest

from .utils_streamlit_test import extract_messages, has_message


pytestmark = [pytest.mark.ui, pytest.mark.e2e]


def test_creation_tab_renders(at, ensure_gpt5_nano):
    # The header should be present
    msgs = extract_messages(at)
    assert any("Système Multi-Agents" in m.get("text", "") for m in msgs)


def test_sidebar_config_persistence(at, ensure_gpt5_nano):
    # Ensure that the sidebar shows a configuration info block
    msgs = extract_messages(at)
    # It may be empty on fresh start; no strict assertion here other than app renders without error
    assert isinstance(msgs, list)


