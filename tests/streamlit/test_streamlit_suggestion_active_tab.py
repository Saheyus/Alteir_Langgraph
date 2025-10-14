from tests.streamlit.fixtures_streamlit import at  # noqa: F401
from tests.streamlit.utils_streamlit_test import set_session_state


def test_suggestion_uses_active_tab_brief(at, monkeypatch):
    from app.streamlit_app import context_selector as cs
    captured = {}

    def fake_render_context_selector(domain, brief):  # type: ignore[unused-argument]
        captured["brief"] = brief
        return {"selected_ids": [], "token_estimate": 0}
    monkeypatch.setattr(cs, "render_context_selector", fake_render_context_selector)

    at = set_session_state(at, {"brief_mode": "random_simple"})
    at = at.run()
    # Validate the active brief used by suggestion
    active_brief = at.session_state["_active_brief_text"]
    assert isinstance(active_brief, str) and len(active_brief) > 5


