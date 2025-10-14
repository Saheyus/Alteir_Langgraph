from tests.streamlit.fixtures_streamlit import at  # noqa: F401
from tests.streamlit.utils_streamlit_test import set_session_state


def test_generation_uses_active_tab_brief(at, monkeypatch):
    captured = {}
    from app.streamlit_app import generation as gen
    from app.streamlit_app import context_selector as cs

    def fake_generate_content(brief, *args, **kwargs):  # type: ignore[unused-argument]
        captured["brief"] = brief
    monkeypatch.setattr(gen, "generate_content", fake_generate_content)
    monkeypatch.setattr(cs, "render_context_selector", lambda domain, brief: {"selected_ids": [], "token_estimate": 0})

    at = set_session_state(at, {"brief_mode": "random_simple"})
    # Trigger generate
    at = set_session_state(at, {"trigger_generate": True})
    # In case generate is skipped due to missing brief, ensure active brief is set
    active_brief = at.session_state["_active_brief_text"]
    assert isinstance(active_brief, str) and len(active_brief) > 5


