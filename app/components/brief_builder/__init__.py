#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any
import logging

import streamlit as st
import streamlit.components.v1 as components

logger = logging.getLogger(__name__)

_component_path = str(Path(__file__).parent)
_brief_builder = components.declare_component("brief_builder", path=_component_path)


def render_brief_builder(
    template: str,
    options_by_category: Dict[str, list],
    selections: Dict[str, str],
    component_mode: str | None = None,
) -> Dict[str, str]:
    """Render the HTML/CSS brief builder component and return updated selections.

    The component returns a mapping {category: value} whenever a select changes.
    """
    # Use stable component key based on provided component_mode when available.
    # Fallback to current session brief_mode for backward compatibility.
    mode: str = str(component_mode or st.session_state.get("brief_mode", "free"))
    version_state_key = f"brief_builder_version_{mode}"
    last_version: int = int(st.session_state.get(version_state_key, 0))

    value: Any = _brief_builder(
        template=template,
        options=options_by_category,
        selections=selections,
        version=last_version,
        key=f"brief_builder_{mode}",
        default=selections,
    )
    if isinstance(value, dict):
        try:
            logger.info(
                "[brief_builder] delta_from_component=%s | current_selections_keys=%s",
                list(value.keys()),
                list(selections.keys()),
            )
        except Exception:
            pass
        # Ignore stale payloads: only accept strictly newer version
        incoming_version_raw = value.get("__version")
        if isinstance(incoming_version_raw, (int, float)):
            incoming_version = int(incoming_version_raw)
            if incoming_version <= last_version:
                try:
                    logger.info(
                        "[brief_builder] Ignoring stale delta version=%s <= last=%s | mode=%s",
                        incoming_version,
                        last_version,
                        mode,
                    )
                except Exception:
                    pass
                return {}
            # Update accepted version in session state
            st.session_state[version_state_key] = incoming_version
            try:
                logger.info(
                    "[brief_builder] Accepted delta version=%s > last=%s | mode=%s",
                    incoming_version,
                    last_version,
                    mode,
                )
            except Exception:
                pass
        # Strip control field and coerce to str
        return {str(k): str(v) for k, v in value.items() if k != "__version"}
    return selections


