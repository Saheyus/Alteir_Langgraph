"""UI rendering for the creation tab."""

from __future__ import annotations

import random
from html import escape

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
from .context_selector import render_context_selector
from .generation import generate_content
from .layout import get_domain_header


DEFAULT_MAX_TOKENS = 5000


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
        st.session_state.max_tokens = DEFAULT_MAX_TOKENS

    if "selected_profile" not in st.session_state or previous_domain != domain:
        st.session_state.selected_profile = "Personnalisé"

    st.session_state.last_domain = domain


def _ensure_configuration_styles() -> None:
    if st.session_state.get("_creation_styles_loaded"):
        return

    st.markdown(
        """
        <style>
        .config-summary {
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 1rem 1.25rem;
            background: #ffffff;
        }
        .config-summary__header {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            gap: 0.75rem;
            margin-bottom: 0.75rem;
        }
        .config-summary__title {
            font-weight: 600;
            color: #111827;
        }
        .config-summary__profile {
            font-size: 0.85rem;
            color: #4b5563;
            padding: 0.15rem 0.55rem;
            border-radius: 999px;
            background: #f3f4f6;
        }
        .config-summary__profile--custom {
            background: #e0f2fe;
            color: #0c4a6e;
            font-weight: 600;
        }
        .config-summary__badges {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-bottom: 0.75rem;
        }
        .config-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            background: #f3f4f6;
            color: #111827;
            font-size: 0.85rem;
            border: 1px solid #e5e7eb;
        }
        .config-badge.changed {
            background: #dbeafe;
            color: #1e3a8a;
            border-color: #bfdbfe;
            font-weight: 600;
        }
        .config-summary table {
            width: 100%;
            border-collapse: collapse;
        }
        .config-summary th,
        .config-summary td {
            padding: 0.55rem 0.4rem;
            border-bottom: 1px solid #e5e7eb;
            font-size: 0.9rem;
            color: #1f2937;
        }
        .config-summary th {
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.04em;
            color: #6b7280;
        }
        .config-summary tbody tr:last-child td {
            border-bottom: none;
        }
        .config-summary .value--changed {
            font-weight: 600;
            color: #111827;
        }
        .config-summary .change-badge {
            margin-left: 0.45rem;
            padding: 0.15rem 0.5rem;
            border-radius: 999px;
            background: #fef3c7;
            color: #92400e;
            font-size: 0.7rem;
        }
        .config-summary__baseline {
            color: #6b7280;
            font-size: 0.85rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state["_creation_styles_loaded"] = True


def _format_value(value: str | float | None) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _render_configuration_summary(
    *,
    domain: str,
    profils: dict,
    selected_profile: str,
    intent: str,
    level: str,
    atmosphere: str | None,
    dialogue_mode: str | None,
    model_info: dict,
    creativity: float | None,
    reasoning_effort: str | None,
    max_tokens: int,
) -> None:
    _ensure_configuration_styles()

    profile_reference = profils.get(selected_profile) if selected_profile in profils else None
    profile_label = (
        f"Profil : {escape(selected_profile)}"
        if profile_reference
        else "Profil personnalisé"
    )
    profile_class = (
        "config-summary__profile"
        if profile_reference
        else "config-summary__profile config-summary__profile--custom"
    )

    narrative_rows: list[tuple[str, str | None, str | None]] = []
    base_intent = profile_reference.get("intent") if profile_reference else None
    narrative_rows.append(("Intention narrative", intent, base_intent))

    if domain == "Lieux":
        base_level = profile_reference.get("level") if profile_reference else None
        base_atmosphere = profile_reference.get("atmosphere") if profile_reference else None
        narrative_rows.append(("Échelle spatiale", level, base_level))
        narrative_rows.append(("Atmosphère", atmosphere, base_atmosphere))
    else:
        base_level = profile_reference.get("level") if profile_reference else None
        base_dialogue = profile_reference.get("dialogue_mode") if profile_reference else None
        narrative_rows.append(("Niveau de détail", level, base_level))
        narrative_rows.append(("Mode de dialogue", dialogue_mode, base_dialogue))

    badges: list[tuple[str, str, bool]] = []
    if model_info.get("uses_reasoning"):
        current_reasoning = reasoning_effort or model_info.get("default_reasoning", "minimal")
        default_reasoning = model_info.get("default_reasoning", "minimal")
        badges.append(("Reasoning", current_reasoning, current_reasoning != default_reasoning))
    else:
        current_creativity = creativity if creativity is not None else st.session_state.get("creativity")
        if current_creativity is not None:
            base_creativity = profile_reference.get("creativity") if profile_reference else None
            changed = (
                base_creativity is not None and abs(current_creativity - base_creativity) > 1e-6
            )
            badges.append(("Température", f"{float(current_creativity):.2f}", changed))

    token_changed = max_tokens != DEFAULT_MAX_TOKENS
    badges.append(("Max tokens", f"{max_tokens:,}".replace(",", "\u202f"), token_changed))

    rows_html = []
    for label, current, baseline in narrative_rows:
        current_display = _format_value(current)
        baseline_display = _format_value(baseline)
        changed = baseline is not None and str(current) != str(baseline)
        change_badge = "" if not changed else "<span class='change-badge'>Modifié</span>"
        value_class = "value--changed" if changed else ""
        rows_html.append(
            """
            <tr>
                <th>{label}</th>
                <td><span class='{value_class}'>{current}</span>{badge}</td>
                <td class='config-summary__baseline'>{baseline}</td>
            </tr>
            """.format(
                label=escape(label),
                value_class=value_class,
                current=escape(current_display),
                badge=change_badge,
                baseline=escape(baseline_display),
            )
        )

    badge_html = "".join(
        """
        <span class='config-badge {changed}'>
            <span>{label}</span>
            <strong>{value}</strong>
        </span>
        """.format(
            changed="changed" if is_changed else "",
            label=escape(label),
            value=escape(str(value)),
        )
        for label, value, is_changed in badges
    )

    st.markdown(
        """
        <div class="config-summary">
            <div class="config-summary__header">
                <span class="config-summary__title">Configuration</span>
                <span class="{profile_class}">{profile_label}</span>
            </div>
            <div class="config-summary__badges">{badges}</div>
            <table>
                <thead>
                    <tr>
                        <th>Paramètre</th>
                        <th>Valeur actuelle</th>
                        <th>Profil</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        """.format(
            profile_class=profile_class,
            profile_label=profile_label,
            badges=badge_html,
            rows="".join(rows_html),
        ),
        unsafe_allow_html=True,
    )

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

        _render_configuration_summary(
            domain=domain,
            profils=profils,
            selected_profile=selected_profile,
            intent=intent,
            level=level,
            atmosphere=atmosphere if domain == "Lieux" else None,
            dialogue_mode=dialogue_mode if domain != "Lieux" else None,
            model_info=model_info,
            creativity=creativity,
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
        )

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

    context_summary = render_context_selector(domain, brief)
    st.session_state.selected_context_summary = context_summary

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
                context_summary,
            )
