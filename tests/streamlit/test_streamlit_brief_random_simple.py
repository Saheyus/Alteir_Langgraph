from tests.streamlit.fixtures_streamlit import at  # noqa: F401
from tests.streamlit.utils_streamlit_test import set_session_state
from app.streamlit_app.brief_builder_logic import roll_tags


def test_random_simple_regenerate_respects_locked(at, monkeypatch):
    # Stub context selector
    from app.streamlit_app import context_selector as cs
    monkeypatch.setattr(cs, "render_context_selector", lambda domain, brief: {"selected_ids": [], "token_estimate": 0})

    # Go to random simple
    at = set_session_state(at, {"brief_mode": "random_simple"})
    assert "_random_simple_selections" in at.session_state
    first = dict(at.session_state["_random_simple_selections"])  # type: ignore[index]

    # Lock TYPE and reroll non-locked
    locked = dict(at.session_state["_random_simple_locked"]) if "_random_simple_locked" in at.session_state else {}
    locked["TYPE"] = True
    # Emulate UI reroll non-locked using the same logic function
    second = roll_tags("Personnages", "simple", seed=1, locked=locked, user_overrides={k: v for k, v in first.items() if locked.get(k)})
    assert second["TYPE"] == first.get("TYPE")
    changed = any(k != "TYPE" and second.get(k) != first.get(k) for k in first.keys())
    assert changed


