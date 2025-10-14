from __future__ import annotations

import random
import re
from typing import Dict, List, Optional

from config.tags_registry import TAGS_REGISTRY
from config.brief_templates import BRIEF_TEMPLATES


CategorySelections = Dict[str, str]
LockedMap = Dict[str, bool]


def _get_template(domain: str, mode: str) -> Optional[str]:
    return BRIEF_TEMPLATES.get(domain, {}).get(mode)


def _get_options(domain: str, category: str) -> List[str]:
    return TAGS_REGISTRY.get(domain, {}).get(category, [])


def compose_brief_text(
    domain: str,
    mode: str,
    selections: CategorySelections,
    extras: Optional[Dict] = None,
) -> str:
    """Compose a textual brief from a template and selected tags.

    Falls back to a simple key:value listing if template is missing.
    """
    template = _get_template(domain, mode)
    if not template:
        parts = [f"{k}: {v}" for k, v in selections.items()]
        return " | ".join(parts)

    text = template
    for cat, value in selections.items():
        text = text.replace(f"[{cat}]", str(value))

    # replace any remaining placeholders with '?'
    text = re.sub(r"\[[A-ZÉÈÀÂÙÏÇ_ ]+\]", "?", text)
    return " ".join(text.split())


def roll_tags(
    domain: str,
    mode: str,
    seed: int,
    locked: LockedMap,
    user_overrides: Optional[CategorySelections] = None,
) -> CategorySelections:
    """Generate selections deterministically by seed, honoring locked categories.

    user_overrides are applied last.
    """
    rng = random.Random(seed)
    selections: CategorySelections = {}
    template = _get_template(domain, mode) or ""
    needed: List[str] = []
    for m in re.findall(r"\[([A-ZÉÈÀÂÙÏÇ_ ]+)\]", template):
        if m not in needed:
            needed.append(m)

    for cat in needed:
        if locked.get(cat):
            # keep previous or override externally
            selections[cat] = (user_overrides or {}).get(cat, selections.get(cat, ""))
            continue
        opts = _get_options(domain, cat)
        selections[cat] = rng.choice(opts) if opts else ""

    if user_overrides:
        selections.update(user_overrides)
    return selections


def swap_tag(category: str, current: str, options: List[str]) -> str:
    """Return the next option (cyclic) different from current if possible."""
    if not options:
        return current
    try:
        idx = options.index(current)
    except ValueError:
        return options[0]
    if len(options) == 1:
        return options[0]
    return options[(idx + 1) % len(options)]


def validate_selection(domain: str, mode: str, selections: CategorySelections) -> List[str]:
    """Return soft warnings; never blocks generation."""
    warnings: List[str] = []
    if domain == "Lieux":
        role = selections.get("RÔLE")
        taille = selections.get("TAILLE")
        if role == "Ville" and taille == "Point d'intérêt":
            warnings.append("Rôle 'Ville' rarement cohérent avec 'Point d'intérêt'.")
    return warnings



