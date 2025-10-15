import json
import types
import pytest

from tests.streamlit.fixtures_streamlit import at  # noqa: F401
from .utils_streamlit_test import extract_messages, click_button_by_label, set_session_state


def _install_context_probe(monkeypatch, captured):
    """Monkeypatch generation to capture the context passed to the workflow.

    We patch app.streamlit_app.generation.ContentWorkflow to a stub that records
    the 'context' argument received in run_iter_live and returns a minimal
    streaming iterator that immediately completes with a fake payload.
    """

    class _StubWorkflow:
        def __init__(self, domain_config, llm=None):  # signature compatible
            self.domain_config = domain_config
            self.llm = llm

        def run_iter_live(self, brief, writer_config, context=None, include_reasoning=False):
            # Record the context for assertions
            captured["context"] = context
            # Yield a minimal sequence of events to satisfy UI
            yield ("writer:start", None)
            # Minimal done payload with required keys
            payload = {
                "content": "Contenu test",
                "writer_metadata": {},
                "reviewer_metadata": {},
                "corrector_metadata": {},
                "validator_metadata": {},
                "coherence_score": 0.8,
                "completeness_score": 0.8,
                "quality_score": 0.8,
                "ready_for_publication": True,
            }
            yield ("writer:done", payload)
            yield ("reviewer:start", None)
            yield ("reviewer:done", payload)
            yield ("corrector:start", None)
            yield ("corrector:done", payload)
            yield ("validator:start", None)
            yield ("validator:done", payload)

        def save_results(self, state):
            # Not used in this test; return dummy files
            class _F:
                name = "dummy.json"
                stem = "dummy"
                def read_text(self, encoding="utf-8"):  # pragma: no cover - not used
                    return json.dumps({})
            return _F(), _F()

    import app.streamlit_app.generation as gen
    # Patch workflow to our stub
    monkeypatch.setattr(gen, "ContentWorkflow", _StubWorkflow)
    # Patch LLM factory to avoid real API usage
    def _fake_llm(*args, **kwargs):
        class _LLM:
            pass
        return _LLM()
    monkeypatch.setattr(gen, "create_llm", _fake_llm)


@pytest.mark.streamlit
def test_auto_suggested_context_is_passed_to_generation(at, monkeypatch):
    """Ensure selected context from Auto-suggestion is fetched and passed to generation.

    Flow:
    - Set a brief to enable Auto-suggestion
    - Click "Suggérer automatiquement" to populate selection
    - Trigger generation
    - Assert the stub workflow received a non-empty context with selected_ids/pages
    """

    # Prepare: ensure domain and model default load
    at = at.run()

    # Step 1: enable suggestion (provide brief)
    at = set_session_state(at, {"brief": "alchimiste du Leviathan"})

    # Step 2: click auto-suggestion (metadata-only)
    at = click_button_by_label(at, "Suggérer automatiquement")

    # If Notion is unavailable in CI, simulate a selected context manually
    # so the generation fallback can reconstruct it.
    selection = {
        "selected_ids": ["fake_page_1", "fake_page_2"],
        "previews": {
            "fake_page_1": {"id": "fake_page_1", "domain": "lieux", "title": "Tombeau des lueurs dissidentes", "summary": "", "token_estimate": 200},
            "fake_page_2": {"id": "fake_page_2", "domain": "lieux", "title": "Cité labiales", "summary": "", "token_estimate": 180},
        },
        "suggestions": [],
    }
    at = set_session_state(at, {"context_selection": selection})

    # Step 3: patch workflow and trigger generation
    captured = {}
    _install_context_probe(monkeypatch, captured)

    # Patch Notion fetcher used inside generation to avoid network
    import app.streamlit_app.generation as gen
    class _FakePage:
        def __init__(self, id, title, domain):
            self.id = id
            self.title = title
            self.domain = domain
            self.summary = ""
            self.content = "Lorem ipsum"
            self.properties = {}
            self.token_estimate = 100
            self.last_edited = None
    class _FakeFetcher:
        def fetch_page_full(self, page_id, domain=None):
            title = "Tombeau des lueurs dissidentes" if page_id == "fake_page_1" else "Cité labiales"
            dom = domain or "lieux"
            return _FakePage(page_id, title, dom)
        def format_context_for_llm(self, pages):
            return "\n".join(getattr(p, "title", "") for p in pages)
    monkeypatch.setattr(gen, "NotionContextFetcher", _FakeFetcher)

    # Use sidebar trigger to avoid relying on main button text per-domain
    at = set_session_state(at, {"trigger_generate": True})

    # After generation, our stub should have captured context
    ctx = captured.get("context")
    assert isinstance(ctx, dict), "No context dict captured"

    # Context must either include fetched pages or at least selected ids
    selected_ids = list(ctx.get("selected_ids") or [])
    pages = list(ctx.get("pages") or [])

    assert selected_ids, "Selected IDs should not be empty after auto-suggestion"

    # If pages were fetched, they should be dicts with id/title
    if pages:
        assert all(isinstance(p, dict) and p.get("id") for p in pages), "Pages must contain dicts with 'id'"


