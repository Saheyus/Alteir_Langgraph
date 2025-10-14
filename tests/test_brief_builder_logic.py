from app.streamlit_app.brief_builder_logic import (
    compose_brief_text,
    roll_tags,
    swap_tag,
    validate_selection,
)


def test_compose_brief_text_personnages_simple():
    selections = {
        "TYPE": "PNJ principal",
        "ESPÈCE": "Humains",
        "LIEU": "Vieille Ville",
        "OCCUPATION": "Archiviste",
        "GENRE": "Féminin",
    }
    text = compose_brief_text("Personnages", "simple", selections)
    assert "PNJ principal" in text and "Humains" in text and "Vieille Ville" in text


def test_roll_tags_respects_locked_and_seed():
    locked = {"TYPE": True, "ESPÈCE": False}
    first = roll_tags(
        "Personnages",
        "simple",
        seed=42,
        locked=locked,
        user_overrides={"TYPE": "PNJ principal"},
    )
    second = roll_tags(
        "Personnages",
        "simple",
        seed=42,
        locked=locked,
        user_overrides={"TYPE": "PNJ principal"},
    )
    assert first == second
    assert first["TYPE"] == "PNJ principal"


def test_swap_tag_simple_validation():
    options = ["Humains", "Aedres", "Construits"]
    assert swap_tag("ESPÈCE", "Humains", options) in options


def test_validate_selection_non_blocking():
    warnings = validate_selection(
        "Lieux",
        "simple",
        {
            "RÔLE": "Ville",
            "TAILLE": "Point d'intérêt",
            "LIEU": "Vieille Ville",
            "ATMOSPHÈRE": "Oppressante",
            "PARTICULARITÉ": "Bioluminescence",
        },
    )
    assert isinstance(warnings, list)



