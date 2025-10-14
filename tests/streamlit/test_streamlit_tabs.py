from tests.streamlit.fixtures_streamlit import at  # noqa: F401
from tests.streamlit.utils_streamlit_test import set_session_state


def test_modes_render_random_briefs(at, monkeypatch):
    # Stub context selector to avoid Notion calls
    from app.streamlit_app import context_selector as cs
    monkeypatch.setattr(cs, "render_context_selector", lambda domain, brief: {"selected_ids": [], "token_estimate": 0})

    # Random simple
    at = set_session_state(at, {"brief_mode": "random_simple"})
    active_brief = at.session_state["_active_brief_text"]
    assert isinstance(active_brief, str) and len(active_brief) > 5

    # Random complexe
    at = set_session_state(at, {"brief_mode": "random_complex"})
    active_brief = at.session_state["_active_brief_text"]
    assert isinstance(active_brief, str) and len(active_brief) > 5


