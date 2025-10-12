"""Common fixtures for Streamlit AppTest E2E tests."""

from __future__ import annotations

import os
import pytest
from pathlib import Path

from streamlit.testing.v1 import AppTest

from .utils_streamlit_test import run_main_app, dump_snapshot


@pytest.fixture
def at() -> AppTest:
    """Run the app fresh for each test and yield the AppTest handle."""
    return run_main_app(timeout=30.0)


@pytest.fixture(autouse=True)
def snapshot_on_failure(request, at: AppTest):
    """Automatically save a JSON snapshot on test failure."""
    yield
    # If the test failed, dump snapshot for post-mortem
    rep = getattr(request.node, "rep_call", None)
    if rep and rep.failed:
        try:
            dump_snapshot(request.node.name, at)
        except Exception:
            # Best effort; do not mask the original failure
            pass


@pytest.fixture
def ensure_gpt5_nano(monkeypatch):
    """Ensure GPT-5-nano is selected and OPENAI_API_KEY is present, else skip."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.startswith("your_") or api_key.startswith("sk-proj-YOUR"):
        pytest.skip("OPENAI_API_KEY missing or placeholder; skipping UI test that needs model selection")
    # No env change needed for selection; UI will reflect default/persisted choice
    yield


@pytest.fixture
def enable_notion_sandbox_reads(monkeypatch):
    """Skip tests if Notion token is missing for sandbox reads."""
    if not os.getenv("NOTION_TOKEN"):
        pytest.skip("NOTION_TOKEN missing; Notion sandbox reads are not available in this env")
    yield


@pytest.fixture
def ui_dry_run_export(monkeypatch):
    """Force DRY_RUN for UI export tests to avoid writes."""
    monkeypatch.setenv("NOTION_DRY_RUN", "true")
    yield


@pytest.fixture(autouse=True)
def stub_heavy_optional_modules(monkeypatch):
    """Stub optional heavy modules to avoid import crashes in headless AppTest.

    - plotly / plotly.graph_objects: provide no-op stand-ins
    - langgraph.graph: provide minimal symbols to allow imports
    - agents.graph_visualizer: provide simplified functions returning placeholders
    """
    import sys
    import types

    # Prefer real modules; stub only if import fails
    try:
        import plotly.graph_objects  # type: ignore
    except Exception:
        plotly_mod = types.ModuleType("plotly")
        go_mod = types.ModuleType("plotly.graph_objects")

        class _Figure:
            def __init__(self, *args, **kwargs):
                self._dummy = True

        go_mod.Figure = _Figure
        go_mod.Scatter = object  # placeholder
        sys.modules["plotly"] = plotly_mod
        sys.modules["plotly.graph_objects"] = go_mod

    try:
        from langgraph import graph as _lg_graph  # type: ignore
    except Exception:
        lg = types.ModuleType("langgraph")
        lg_graph = types.ModuleType("langgraph.graph")

        class _DummyStateGraph:  # minimal placeholder
            def __init__(self, *args, **kwargs):
                pass

        lg_graph.StateGraph = _DummyStateGraph
        lg_graph.END = object()
        sys.modules["langgraph"] = lg
        sys.modules["langgraph.graph"] = lg_graph

    try:
        import agents.graph_visualizer  # type: ignore
    except Exception:
        gv = types.ModuleType("agents.graph_visualizer")

        def create_interactive_graph(*args, **kwargs):
            return {"placeholder": True}

        def create_stats_chart(*args, **kwargs):
            return {"placeholder": True}

        gv.create_interactive_graph = create_interactive_graph
        gv.create_stats_chart = create_stats_chart
        sys.modules["agents.graph_visualizer"] = gv

    yield


@pytest.fixture(autouse=True)
def fast_workflow(monkeypatch):
    """Speed up UI generation by monkeypatching ContentWorkflow.run_iter_live.

    This avoids long LLM calls while still exercising the UI updates and success banners.
    """
    try:
        from workflows.content_workflow import ContentWorkflow
    except Exception:
        return

    def fake_run_iter_live(self, brief, writer_config, context=None, include_reasoning=False):  # type: ignore[unused-argument]
        yield ("writer:start", {})
        yield ("writer:done", {"content": "draft", "writer_metadata": {"success": True}})
        yield ("reviewer:start", {})
        yield ("reviewer:done", {"content": "review", "reviewer_metadata": {"success": True}})
        yield ("corrector:start", {})
        yield ("corrector:done", {"content": "corrected", "corrector_metadata": {"success": True}})
        yield ("validator:start", {})
        yield (
            "validator:done",
            {
                "content": "final content",
                "writer_metadata": {"success": True},
                "reviewer_metadata": {"success": True},
                "corrector_metadata": {"success": True},
                "validator_metadata": {"success": True, "is_valid": True},
                "coherence_score": 0.8,
                "completeness_score": 0.85,
                "quality_score": 0.8,
                "ready_for_publication": True,
            },
        )

    try:
        monkeypatch.setattr(ContentWorkflow, "run_iter_live", fake_run_iter_live, raising=False)
    except Exception:
        pass


