#!/usr/bin/env python3
"""Test the regenerate button logic in random brief tabs."""

import random
import re
from config.tags_registry import TAGS_REGISTRY
from config.brief_templates import BRIEF_TEMPLATES


def test_regenerate_logic():
    """Test that regenerate button logic works correctly."""
    
    # Setup: simulate session state for random_simple_state
    domain = "Personnages"
    mode_name = "simple"
    mode_key = "random_simple_state"
    
    # Simulate initial state
    session_state = {
        mode_key: {
            "seed": 0,
            "locked": {
                "TYPE": True,  # Locked - should NOT change
                "ESPÈCE": False,  # Unlocked - should change
                "LIEU": False,  # Unlocked - should change
                "OCCUPATION": False,
                "FACTION": False,
                "QUALITÉS": False,
                "DÉFAUTS": False,
                "GENRE": False,
            },
            "selections": {
                "TYPE": "PNJ secondaire",
                "ESPÈCE": "Railleurs",
                "LIEU": "Léviathan pétrifié",
                "OCCUPATION": "Courtisan",
                "FACTION": "Autre (à inventer)",
                "QUALITÉS": "Humble",
                "DÉFAUTS": "Paresseuse",
                "GENRE": "Non défini",
            }
        }
    }
    
    # Store original locked value
    original_type = session_state[mode_key]["selections"]["TYPE"]
    original_espece = session_state[mode_key]["selections"]["ESPÈCE"]
    
    # Simulate button click - increment seed
    session_state[mode_key]["seed"] += 1
    new_seed = session_state[mode_key]["seed"]
    
    # Get template and needed categories
    template = BRIEF_TEMPLATES.get(domain, {}).get(mode_name, "")
    needed = []
    for m in re.findall(r"\[([A-ZÉÈÀÂÙÏÇ_ ]+)\]", template):
        if m not in needed:
            needed.append(m)
    
    # Generate new random selections respecting locks
    rng = random.Random(new_seed)
    changes = []
    for cat in needed:
        if session_state[mode_key]["locked"].get(cat):
            # Keep locked value - don't change it
            changes.append(f"{cat}: LOCKED (kept {session_state[mode_key]['selections'][cat]})")
            continue
        else:
            # Pick a different value from current to avoid repeating
            opts = TAGS_REGISTRY.get(domain, {}).get(cat, [])
            current = session_state[mode_key]["selections"].get(cat)
            if len(opts) > 1:
                available = [opt for opt in opts if opt != current]
                new_val = rng.choice(available) if available else rng.choice(opts)
                session_state[mode_key]["selections"][cat] = new_val
                changes.append(f"{cat}: {current} → {new_val}")
            elif opts:
                new_val = rng.choice(opts)
                session_state[mode_key]["selections"][cat] = new_val
                changes.append(f"{cat}: {current} → {new_val}")
    
    # Verify results
    print("\n=== Test Regenerate Button Logic ===")
    print(f"Seed: 0 → {new_seed}")
    print("\nChanges:")
    for change in changes:
        print(f"  {change}")
    
    # Assertions
    new_type = session_state[mode_key]["selections"]["TYPE"]
    new_espece = session_state[mode_key]["selections"]["ESPÈCE"]
    
    print("\n=== Assertions ===")
    assert new_type == original_type, f"LOCKED field TYPE changed! {original_type} → {new_type}"
    print(f"✓ TYPE remained locked: {new_type}")
    
    # ESPÈCE should have changed (unless only 1 option, which is not the case)
    assert new_espece != original_espece, f"UNLOCKED field ESPÈCE did not change! Still: {new_espece}"
    print(f"✓ ESPÈCE changed: {original_espece} → {new_espece}")
    
    print("\n=== All tests passed! ===")


def test_regenerate_all_locked():
    """Test regenerate when all fields are locked."""
    domain = "Personnages"
    mode_name = "simple"
    mode_key = "random_simple_state"
    
    # All fields locked
    session_state = {
        mode_key: {
            "seed": 0,
            "locked": {
                "TYPE": True,
                "ESPÈCE": True,
                "LIEU": True,
                "OCCUPATION": True,
                "FACTION": True,
                "QUALITÉS": True,
                "DÉFAUTS": True,
                "GENRE": True,
            },
            "selections": {
                "TYPE": "PNJ secondaire",
                "ESPÈCE": "Railleurs",
                "LIEU": "Léviathan pétrifié",
                "OCCUPATION": "Courtisan",
                "FACTION": "Autre (à inventer)",
                "QUALITÉS": "Humble",
                "DÉFAUTS": "Paresseuse",
                "GENRE": "Non défini",
            }
        }
    }
    
    original_selections = dict(session_state[mode_key]["selections"])
    
    # Simulate regenerate
    session_state[mode_key]["seed"] += 1
    new_seed = session_state[mode_key]["seed"]
    template = BRIEF_TEMPLATES.get(domain, {}).get(mode_name, "")
    needed = []
    for m in re.findall(r"\[([A-ZÉÈÀÂÙÏÇ_ ]+)\]", template):
        if m not in needed:
            needed.append(m)
    
    rng = random.Random(new_seed)
    for cat in needed:
        if session_state[mode_key]["locked"].get(cat):
            continue
        else:
            opts = TAGS_REGISTRY.get(domain, {}).get(cat, [])
            current = session_state[mode_key]["selections"].get(cat)
            if len(opts) > 1:
                available = [opt for opt in opts if opt != current]
                session_state[mode_key]["selections"][cat] = rng.choice(available) if available else rng.choice(opts)
            elif opts:
                session_state[mode_key]["selections"][cat] = rng.choice(opts)
    
    print("\n=== Test All Locked ===")
    assert session_state[mode_key]["selections"] == original_selections
    print("✓ All fields remained unchanged when all locked")


if __name__ == "__main__":
    test_regenerate_logic()
    test_regenerate_all_locked()
    print("\n🎉 All regenerate button tests passed!")

