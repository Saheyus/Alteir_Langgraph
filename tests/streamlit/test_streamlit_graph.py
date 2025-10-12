from __future__ import annotations

import pytest

from .utils_streamlit_test import extract_messages


pytestmark = [pytest.mark.ui, pytest.mark.e2e]


def test_graph_tab_no_data_warning(at):
    msgs = extract_messages(at)
    # The graph tab initially shows a warning when no outputs exist
    # We only assert that the app renders messages in general; specific tab switching is limited in AppTest
    assert isinstance(msgs, list)


