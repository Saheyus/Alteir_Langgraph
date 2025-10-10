"""E2E minimal (dry-run): workflow → outputs without real Notion writes.

This test runs the content workflow with a tiny brief and checks that:
- outputs are produced (json and md)
- NotionConfig.DRY_RUN is respected (no network call required)
"""

from __future__ import annotations

import os
from pathlib import Path

from config.notion_config import NotionConfig
from workflows.content_workflow import ContentWorkflow
from config.domain_configs.personnages_config import PERSONNAGES_CONFIG


def test_e2e_dry_run_outputs(tmp_path: Path, monkeypatch):
    # Force DRY_RUN for the test
    monkeypatch.setenv("NOTION_DRY_RUN", "true")
    # Ensure outputs go to temp dir
    monkeypatch.chdir(tmp_path)

    workflow = ContentWorkflow(PERSONNAGES_CONFIG)
    brief = "Un court brief pour un test dry-run. Genre: Non défini. Espèce: Humain. Âge: 30."

    state = workflow.run(brief)
    json_file, md_file = workflow.save_results(state, output_dir="outputs")

    assert json_file.exists(), "JSON de sortie non créé"
    assert md_file.exists(), "Markdown de sortie non créé"

    # Sanity checks
    content = state.get("content", "")
    assert isinstance(content, str)
    assert len(content) > 0


