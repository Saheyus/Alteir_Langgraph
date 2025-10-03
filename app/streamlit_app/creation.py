"""UI rendering for the creation tab."""

from __future__ import annotations

import random

import streamlit as st

from .constants import (
    ATMOSPHERE_OPTIONS,
    BRIEF_EXAMPLES,
    BRIEF_PLACEHOLDERS,
    DIALOGUE_OPTIONS,
    INTENT_OPTIONS,
    LEVEL_OPTIONS,
    PROFILE_CONFIGS,
)
from .generation import generate_content
from .layout import get_domain_header


def _random_different(options, current):
    if len(options) <= 1:
        return options[0] if options else current
    available = [opt for opt in options if opt != current]
    return random.choice(available)


def _ensure_session_defaults(domain: str, model_info: dict) -> None:
    previous_domain = st.session_state.get("last_domain")

    if "random_seed" not in st.session_state:
        st.session_state.random_seed = 0

    if domain == "Lieux":
        if "intent" not in st.session_state or domain != st.session_state.get("last_domain"):
            st.session_state.intent = "zone_exploration"
        if "level" not in st.session_state or domain != st.session_state.get("last_domain"):
            st.session_state.level = "site"
        if "atmosphere" not in st.session_state:
            st.session_state.atmosphere = "neutre"
    else:
        if "intent" not in st.session_state or domain != st.session_state.get("last_domain"):
            st.session_state.intent = "orthogonal_depth"
        if "level" not in st.session_state or domain != st.session_state.get("last_domain"):
            st.session_state.level = "standard"
        if "dialogue_mode" not in st.session_state:
            st.session_state.dialogue_mode = "parle"

    if "creativity" not in st.session_state:
        st.session_state.creativity = 0.7

    if "reasoning_effort" not in st.session_state:
        st.session_state.reasoning_effort = model_info.get("default_reasoning", "minimal")

    if "max_tokens" not in st.session_state:
        st.session_state.max_tokens = 5000

    if "selected_profile" not in st.session_state or previous_domain != domain:
        st.session_state.selected_profile = "Personnalisé"

    st.session_state.last_domain = domain


def render_creation_tab(domain: str, selected_model: str, model_info: dict) -> None:
    """Render the creation tab for the given domain and model."""

    st.header(get_domain_header(domain))

    brief_examples = BRIEF_EXAMPLES[domain]

    if "brief" not in st.session_state:
        st.session_state.brief = ""

    brief_placeholder = BRIEF_PLACEHOLDERS[domain]

    col_brief_label, col_example_btn = st.columns([4, 1])
    with col_brief_label:
        brief_label = "Description du lieu" if domain == "Lieux" else "Description du personnage"
        st.markdown(f"**{brief_label}**")
    with col_example_btn:
        if st.button("🎲 Brief aléatoire", help="Charger un exemple de brief"):
            st.session_state.brief = random.choice(brief_examples)

    brief = st.text_area(
        brief_label,
        value=st.session_state.get("brief", ""),
        placeholder=brief_placeholder,
        height=100,
        label_visibility="collapsed",
        key="brief",
    )

    _ensure_session_defaults(domain, model_info)

    intent_options = INTENT_OPTIONS[domain]
    level_options = LEVEL_OPTIONS[domain]
    dialogue_options = DIALOGUE_OPTIONS.get(domain, [])
    atmosphere_options = ATMOSPHERE_OPTIONS.get(domain, [])

    def randomize_all():
        st.session_state.intent = _random_different(intent_options, st.session_state.intent)
        st.session_state.level = _random_different(level_options, st.session_state.level)
        if domain == "Lieux":
            st.session_state.atmosphere = _random_different(
                atmosphere_options, st.session_state.atmosphere
            )
        else:
            st.session_state.dialogue_mode = _random_different(
                dialogue_options, st.session_state.dialogue_mode
            )
        while True:
            new_creativity = round(random.uniform(0.5, 0.9), 2)
            if abs(new_creativity - st.session_state.creativity) >= 0.1:
                st.session_state.creativity = new_creativity
                break
        st.session_state.random_seed += 1

    def randomize_intent():
        st.session_state.intent = _random_different(intent_options, st.session_state.intent)
        st.session_state.random_seed += 1

    def randomize_level():
        st.session_state.level = _random_different(level_options, st.session_state.level)
        st.session_state.random_seed += 1

    def randomize_dialogue():
        st.session_state.dialogue_mode = _random_different(
            dialogue_options, st.session_state.dialogue_mode
        )
        st.session_state.random_seed += 1

    def randomize_creativity():
        while True:
            new_creativity = round(random.uniform(0.5, 0.9), 2)
            if abs(new_creativity - st.session_state.creativity) >= 0.1:
                st.session_state.creativity = new_creativity
                break
        st.session_state.random_seed += 1

    st.subheader("Profils & Paramètres")
    profils = PROFILE_CONFIGS[domain]

    def apply_profile():
        if st.session_state.selected_profile != "Personnalisé":
            profile = profils[st.session_state.selected_profile]
            st.session_state.intent = profile["intent"]
            st.session_state.level = profile["level"]
            if domain == "Lieux":
                st.session_state.atmosphere = profile["atmosphere"]
            else:
                st.session_state.dialogue_mode = profile["dialogue_mode"]
            st.session_state.creativity = profile["creativity"]
            st.session_state.random_seed += 1

    col_profile, col_dice = st.columns([5, 1])
    with col_profile:
        selected_profile = st.selectbox(
            "Profil prédéfini",
            ["Personnalisé"] + list(profils.keys()),
            help="Charger une configuration prédéfinie",
            key="selected_profile",
            on_change=apply_profile,
        )
        if selected_profile != "Personnalisé":
            st.caption(f"ℹ️ {profils[selected_profile]['description']}")

    with col_dice:
        st.write("")
        st.write("")
        st.button(
            "🎲",
            help="Mélanger tous les paramètres",
            use_container_width=True,
            on_click=randomize_all,
        )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Paramètres Narratifs")

        col_intent, col_intent_random = st.columns([4, 1])
        with col_intent_random:
            st.write("")
            st.write("")
            st.button("🎲", key="random_intent", help="Valeur aléatoire", on_click=randomize_intent)
        with col_intent:
            if domain == "Lieux":
                intent_label = "Fonction narrative"
                intent_help = "Rôle du lieu dans l'histoire"
            else:
                intent_label = "Intention narrative"
                intent_help = "Orthogonal = profondeur ≠ rôle visible"

            intent = st.selectbox(
                intent_label,
                intent_options,
                index=intent_options.index(st.session_state.intent),
                help=intent_help,
                key=f"intent_select_{st.session_state.random_seed}",
            )

        col_level, col_level_random = st.columns([4, 1])
        with col_level_random:
            st.write("")
            st.write("")
            st.button("🎲", key="random_level", help="Valeur aléatoire", on_click=randomize_level)
        with col_level:
            if domain == "Lieux":
                level_label = "Échelle spatiale"
                level_help = "Taille du lieu : point d'intérêt < site < secteur < district"
            else:
                level_label = "Niveau de détail"
                level_help = "cameo: 4-6 répliques | standard: 8-10 | major: 10-12"

            level = st.selectbox(
                level_label,
                level_options,
                index=level_options.index(st.session_state.level),
                help=level_help,
                key=f"level_select_{st.session_state.random_seed}",
            )

        if domain == "Lieux":
            def randomize_atmosphere():
                st.session_state.atmosphere = _random_different(
                    atmosphere_options, st.session_state.atmosphere
                )
                st.session_state.random_seed += 1

            col_atmosphere, col_atmosphere_random = st.columns([4, 1])
            with col_atmosphere_random:
                st.write("")
                st.write("")
                st.button(
                    "🎲",
                    key="random_atmosphere",
                    help="Valeur aléatoire",
                    on_click=randomize_atmosphere,
                )
            with col_atmosphere:
                atmosphere = st.selectbox(
                    "Atmosphère",
                    atmosphere_options,
                    index=atmosphere_options.index(st.session_state.atmosphere),
                    help="Ambiance générale du lieu",
                    key=f"atmosphere_select_{st.session_state.random_seed}",
                )
        else:
            col_dialogue, col_dialogue_random = st.columns([4, 1])
            with col_dialogue_random:
                st.write("")
                st.write("")
                st.button(
                    "🎲",
                    key="random_dialogue",
                    help="Valeur aléatoire",
                    on_click=randomize_dialogue,
                )
            with col_dialogue:
                dialogue_mode = st.selectbox(
                    "Mode de dialogue",
                    dialogue_options,
                    index=dialogue_options.index(st.session_state.dialogue_mode),
                    help="Comment le personnage communique",
                    key=f"dialogue_select_{st.session_state.random_seed}",
                )

    with col2:
        st.subheader("Paramètres Techniques")

        if model_info.get("uses_reasoning"):
            reasoning_options = ["minimal", "low", "medium", "high"]

            def randomize_reasoning():
                st.session_state.reasoning_effort = _random_different(
                    reasoning_options, st.session_state.reasoning_effort
                )
                st.session_state.random_seed += 1

            col_reasoning, col_reasoning_random = st.columns([4, 1])
            with col_reasoning_random:
                st.write("")
                st.write("")
                st.button(
                    "🎲",
                    key="random_reasoning",
                    help="Valeur aléatoire",
                    on_click=randomize_reasoning,
                )
            with col_reasoning:
                reasoning_effort = st.selectbox(
                    "Effort de raisonnement",
                    options=reasoning_options,
                    index=reasoning_options.index(st.session_state.reasoning_effort),
                    help="minimal = rapide | low = équilibré | medium = standard | high = approfondi",
                    key=f"reasoning_select_{st.session_state.random_seed}",
                )
                creativity = None
        else:
            col_creativity, col_creativity_random = st.columns([4, 1])
            with col_creativity_random:
                st.write("")
                st.write("")
                st.write("")
                st.write("")
                st.button(
                    "🎲",
                    key="random_creativity",
                    help="Valeur aléatoire",
                    on_click=randomize_creativity,
                )
            with col_creativity:
                creativity = st.slider(
                    "Créativité (température)",
                    min_value=0.0,
                    max_value=1.0,
                    value=st.session_state.creativity,
                    step=0.01,
                    help="0 = déterministe | 1 = très créatif",
                    key=f"creativity_slider_{st.session_state.random_seed}",
                )
                reasoning_effort = None

        st.write("")
        max_tokens = st.slider(
            "Max tokens (sortie)",
            min_value=1000,
            max_value=30000,
            value=st.session_state.max_tokens,
            step=1000,
            help="Limite de tokens pour la réponse (1000-30000). ⚠️ GPT-5 utilise des tokens pour le reasoning !",
            key=f"max_tokens_slider_{st.session_state.random_seed}",
        )

        config_lines = [f"- Intent: `{intent}`"]
        if domain == "Lieux":
            config_lines.extend([f"- Échelle: `{level}`", f"- Atmosphère: `{atmosphere}`"])
        else:
            config_lines.extend([f"- Niveau: `{level}`", f"- Dialogue: `{dialogue_mode}`"])

        if model_info.get("uses_reasoning"):
            config_lines.append(f"- Reasoning: `{reasoning_effort}`")
        else:
            config_lines.append(f"- Température: `{creativity}`")

        config_lines.append(f"- Max tokens: `{max_tokens}`")
        st.info("**Configuration:**\n" + "\n".join(config_lines))

    st.session_state.intent = intent
    st.session_state.level = level
    if domain == "Lieux":
        st.session_state.atmosphere = atmosphere
        dialogue_mode = "none"
    else:
        st.session_state.dialogue_mode = dialogue_mode

    if model_info.get("uses_reasoning"):
        st.session_state.reasoning_effort = reasoning_effort
    else:
        st.session_state.creativity = creativity

    st.session_state.max_tokens = max_tokens

    button_text = {
        "Personnages": "🚀 Générer le Personnage",
        "Lieux": "🚀 Générer le Lieu",
    }
    error_text = {
        "Personnages": "⚠️ Veuillez fournir une description du personnage",
        "Lieux": "⚠️ Veuillez fournir une description du lieu",
    }

    if st.button(button_text[domain], type="primary", use_container_width=True):
        if not brief:
            st.error(error_text[domain])
        else:
            generate_content(
                brief,
                intent,
                level,
                dialogue_mode,
                creativity if creativity is not None else st.session_state.creativity,
                reasoning_effort,
                max_tokens,
                selected_model,
                model_info,
                domain,
            )
