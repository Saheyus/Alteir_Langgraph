from tests.streamlit.fixtures_streamlit import at  # noqa: F401
from tests.streamlit.utils_streamlit_test import set_session_state
from app.streamlit_app.brief_builder_logic import roll_tags


def test_random_complex_regenerate_respects_locked(at, monkeypatch):
    # Stub context selector
    from app.streamlit_app import context_selector as cs
    monkeypatch.setattr(cs, "render_context_selector", lambda domain, brief: {"selected_ids": [], "token_estimate": 0})

    # Go to random complex
    at = set_session_state(at, {"brief_mode": "random_complex"})
    assert "_random_complex_selections" in at.session_state
    first = dict(at.session_state["_random_complex_selections"])  # type: ignore[index]

    # Lock the first available key and ensure it stays constant after reroll
    lock_key = next(iter(first.keys()))
    locked = dict(at.session_state["_random_complex_locked"]) if "_random_complex_locked" in at.session_state else {}
    locked[lock_key] = True

    # Infer domain: if keys look like lieux (contain RÔLE/TAILLE) choose Lieux, else Personnages
    domain = "Lieux" if any("R" in k or "TAILLE" in k for k in first.keys()) else "Personnages"

    second = roll_tags(
        domain,
        "complexe",
        seed=1,
        locked=locked,
        user_overrides={k: v for k, v in first.items() if locked.get(k)},
    )

    assert second.get(lock_key) == first.get(lock_key)
    changed = any(k != lock_key and second.get(k) != first.get(k) for k in first.keys())
    assert changed


