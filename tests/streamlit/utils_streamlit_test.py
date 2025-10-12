"""Utilities for Streamlit E2E testing with streamlit.testing.v1.AppTest.

These helpers provide:
- A thin wrapper to run the main Streamlit app headlessly
- Message extraction across info/success/warning/error/caption/markdown
- Robust snapshot dumping on failure with session_state and recent files
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from streamlit.testing.v1 import AppTest


DEFAULT_TIMEOUT_S = 30.0


ARTIFACTS_DIR = Path("tests") / "artifacts" / "streamlit_snapshots"


def ensure_artifacts_dir() -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    return ARTIFACTS_DIR


def run_main_app(cwd: Path | None = None, timeout: float = DEFAULT_TIMEOUT_S) -> AppTest:
    """Run the main Streamlit entrypoint file with AppTest.

    Args:
        cwd: Optional working directory to chdir to before running.
    Returns:
        The AppTest instance after first run.
    """
    if cwd is not None:
        os.chdir(cwd)
    at = AppTest.from_file("app_streamlit.py")
    return at.run(timeout=timeout)


def extract_messages(at: AppTest) -> List[Dict[str, Any]]:
    """Extract user-visible messages from the AppTest tree.

    This includes info/success/warning/error/caption/markdown blocks.
    """
    messages: List[Dict[str, Any]] = []

    def _extend(msg_type: str, elems: list) -> None:
        for el in elems:
            try:
                text = str(getattr(el, "value", "") or "")
            except Exception:
                text = str(el)
            messages.append({"type": msg_type, "text": text})

    _extend("info", list(getattr(at, "info", [])))
    _extend("success", list(getattr(at, "success", [])))
    _extend("warning", list(getattr(at, "warning", [])))
    _extend("error", list(getattr(at, "error", [])))
    _extend("caption", list(getattr(at, "caption", [])))
    _extend("markdown", list(getattr(at, "markdown", [])))

    return messages


def has_message(messages: List[Dict[str, Any]], contains: str, msg_type: str | None = None) -> bool:
    needle = contains.lower()
    for m in messages:
        if msg_type is not None and m.get("type") != msg_type:
            continue
        if needle in (m.get("text") or "").lower():
            return True
    return False


def recent_output_files(limit: int = 5) -> List[str]:
    """Return recent files in outputs/ for quick snapshots."""
    out_dir = Path("outputs")
    if not out_dir.exists():
        return []
    files = sorted(out_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [str(p) for p in files[:limit]]


def dump_snapshot(test_name: str, at: AppTest, extra: Dict[str, Any] | None = None) -> Path:
    """Write a JSON snapshot with session_state, messages, and recent files."""
    ensure_artifacts_dir()
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    snap = {
        "test": test_name,
        "timestamp": ts,
        "session_state": dict(getattr(at, "session_state", {})),
        "messages": extract_messages(at),
        "files": recent_output_files(),
    }
    if extra:
        snap.update(extra)

    path = ARTIFACTS_DIR / f"{test_name}_{ts}.json"
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def set_session_state(at: AppTest, updates: Dict[str, Any], timeout: float = DEFAULT_TIMEOUT_S) -> AppTest:
    """Convenience to update session_state and trigger a rerun."""
    for k, v in updates.items():
        at.session_state[k] = v
    return at.run(timeout=timeout)


def click_button_by_label(at: AppTest, label_substring: str, timeout: float = DEFAULT_TIMEOUT_S) -> AppTest:
    """Click the first button whose label contains the given substring.

    Falls back silently if no such button exists.
    """
    try:
        for btn in getattr(at, "button", []):
            label = str(getattr(btn, "label", "") or "")
            if label_substring.lower() in label.lower():
                btn.click()
                return at.run(timeout=timeout)
    except Exception:
        pass
    return at


