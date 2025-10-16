"""UI rendering for the creation tab."""

from __future__ import annotations

import random
import html as _html
import re

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
from .cache import load_ui_prefs, save_ui_prefs
from .brief_builder_logic import compose_brief_text, roll_tags, swap_tag
from config.tags_registry import TAGS_REGISTRY
from config.brief_templates import BRIEF_TEMPLATES
from config.logging_config import get_logger

logger = get_logger(__name__)


def _random_different(options, current):
    if len(options) <= 1:
        return options[0] if options else current
    available = [opt for opt in options if opt != current]
    return random.choice(available)


def _humanize_category(raw_name: str) -> str:
    """Turn registry/template category identifiers into human-readable labels."""
    return raw_name.replace("_", " ").strip().title()


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
    elif domain == "Personnages":
        if "intent" not in st.session_state or domain != st.session_state.get("last_domain"):
            st.session_state.intent = "orthogonal_depth"
        if "level" not in st.session_state or domain != st.session_state.get("last_domain"):
            st.session_state.level = "standard"
        if "dialogue_mode" not in st.session_state:
            st.session_state.dialogue_mode = "parle"
    else:
        # Espèces / Communautés : pas de dialogue/atmosphere
        if "intent" not in st.session_state or domain != st.session_state.get("last_domain"):
            # choisir une valeur par défaut par domaine si disponible
            defaults = {
                "Espèces": "predateur_signature",
                "Communautés": "influence_locale",
            }
            st.session_state.intent = defaults.get(domain, "orthogonal_depth")
        if "level" not in st.session_state or domain != st.session_state.get("last_domain"):
            defaults = {
                "Espèces": "standard",
                "Communautés": "chapitre",
            }
            st.session_state.level = defaults.get(domain, "standard")

    if "creativity" not in st.session_state:
        st.session_state.creativity = 0.7

    if "reasoning_effort" not in st.session_state:
        st.session_state.reasoning_effort = model_info.get("default_reasoning", "minimal")

    # Default verbosity for GPT-5 family
    if "verbosity" not in st.session_state:
        # Defaults align with OpenAI docs: medium by default
        st.session_state.verbosity = "medium"

    # Default for agentic work (writer+reviewer+... when True)
    if "agentic_work" not in st.session_state:
        st.session_state.agentic_work = True

    if "max_tokens" not in st.session_state:
        st.session_state.max_tokens = 5000

    if "selected_profile" not in st.session_state or previous_domain != domain:
        st.session_state.selected_profile = "Personnalisé"

    st.session_state.last_domain = domain
    # Load persisted UI prefs once per app session
    if "_ui_prefs_loaded" not in st.session_state:
        prefs = load_ui_prefs()
        # Restore core knobs if missing
        st.session_state.intent = prefs.get("intent", st.session_state.intent)
        st.session_state.level = prefs.get("level", st.session_state.level)
        if domain == "Lieux":
            st.session_state.atmosphere = prefs.get("atmosphere", st.session_state.atmosphere)
        else:
            st.session_state.dialogue_mode = prefs.get("dialogue_mode", st.session_state.dialogue_mode)
        st.session_state.creativity = prefs.get("creativity", st.session_state.creativity)
        st.session_state.reasoning_effort = prefs.get("reasoning_effort", st.session_state.reasoning_effort)
        st.session_state.max_tokens = prefs.get("max_tokens", st.session_state.max_tokens)
        st.session_state.verbosity = prefs.get("verbosity", st.session_state.verbosity)
        st.session_state.agentic_work = prefs.get("agentic_work", st.session_state.agentic_work)
        st.session_state._ui_prefs_loaded = True


def render_creation_tab(domain: str, selected_model: str, model_info: dict) -> None:
    """Render the creation tab for the given domain and model."""

    st.header(get_domain_header(domain))
    try:
        logger.info(
            "[creation] render_creation_tab domain=%s model=%s brief_mode=%s",
            domain,
            selected_model,
            st.session_state.get("brief_mode"),
        )
    except Exception:
        pass

    brief_examples = BRIEF_EXAMPLES[domain]

    if "brief" not in st.session_state:
        st.session_state.brief = ""

    # Tabs state
    if "brief_mode" not in st.session_state:
        st.session_state.brief_mode = "free"  # free | random_simple | random_complex
    if "random_simple_state" not in st.session_state:
        st.session_state.random_simple_state = {"seed": 0, "render_nonce": 0, "locked": {}, "selections": {}}
    if "random_complex_state" not in st.session_state:
        st.session_state.random_complex_state = {"seed": 0, "render_nonce": 0, "locked": {}, "selections": {}}

    brief_placeholder = BRIEF_PLACEHOLDERS[domain]

    def _render_free_tab() -> str:
        col_brief_label, col_example_btn = st.columns([4, 1])
        with col_brief_label:
            if domain == "Lieux":
                brief_label = "Description du lieu"
            elif domain == "Espèces":
                brief_label = "Description de l'espèce"
            elif domain == "Communautés":
                brief_label = "Description de la communauté"
            else:
                brief_label = "Description du personnage"
            st.markdown(f"**{brief_label}**")
        with col_example_btn:
            if st.button("🎲 Exemple", help="Charger un exemple de brief"):
                st.session_state.brief = random.choice(brief_examples)

        value = st.text_area(
            brief_label,
            placeholder=brief_placeholder,
            height=100,
            label_visibility="collapsed",
            key="brief",
        )
        return value

    def _render_random_tab(mode_key: str, mode_name: str) -> str:
        state = st.session_state[mode_key]
        # When this tab is visible, consider its brief as active
        st.session_state.brief_mode = "random_simple" if mode_name == "simple" else "random_complex"
        template_available = BRIEF_TEMPLATES.get(domain, {}).get(mode_name)
        if not template_available:
            st.info("Brief aléatoire non disponible pour ce domaine.")
            return ""
        # Initialize selections on first render
        if not state["selections"]:
            state["selections"] = roll_tags(domain, mode_name, seed=state["seed"], locked=state["locked"], user_overrides={})
            try:
                logger.info(
                    "[creation] init selections mode_key=%s mode=%s seed=%s locked=%s selections=%s",
                    mode_key,
                    mode_name,
                    state["seed"],
                    dict(state["locked"]),
                    dict(state["selections"]),
                )
            except Exception:
                pass

        # Deux zones: contrôles à gauche, aperçu à droite
        template = BRIEF_TEMPLATES.get(domain, {}).get(mode_name, "")
        options_by_category = {k: v for k, v in TAGS_REGISTRY.get(domain, {}).items()}

        col_left, col_right = st.columns([2, 1])

        with col_left:
            st.subheader("Paramètres du prompt")
            cats = []
            for m in re.findall(r"\[([A-ZÉÈÀÂÙÏÇ_ ]+)\]", template):
                if m not in cats:
                    cats.append(m)
            try:
                logger.debug(
                    "[creation] categories mode_key=%s: %s",
                    mode_key,
                    ", ".join(cats),
                )
            except Exception:
                pass

            # Afficher deux étiquettes par rangée avec largeur réduite
            for i in range(0, len(cats), 2):
                cat_cols = st.columns(2)
                pair = [cats[i], cats[i + 1] if i + 1 < len(cats) else None]
                for col_idx, cat in enumerate(pair):
                    if not cat:
                        continue
                    with cat_cols[col_idx]:
                        opts = options_by_category.get(cat, [])
                        cur = state["selections"].get(cat, opts[0] if opts else "")
                        # Afficher le titre de la catégorie
                        label = _humanize_category(cat)
                        # Tout sur une seule ligne: Label : Selectbox [Checkbox] 🔒
                        row_label, row_sel, row_lock = st.columns([1, 3, 0.6])
                        with row_label:
                            st.markdown(f'<div style="margin-right: 4px;"><strong>{label} :</strong></div>', unsafe_allow_html=True)
                        with row_sel:
                            sel = st.selectbox(
                                label,
                                opts or [""],
                                index=(opts.index(cur) if cur in opts else 0) if opts else 0,
                                key=f"{mode_key}_{cat}_select_{state.get('render_nonce', 0)}",
                                label_visibility="collapsed",
                            )
                            state["selections"][cat] = sel
                        with row_lock:
                            locked = bool(state["locked"].get(cat))
                            col_checkbox, col_lock_icon = st.columns([1, 1])
                            with col_checkbox:
                                new_locked = st.checkbox(
                                    "lock",
                                    value=locked,
                                    key=f"{mode_key}_{cat}_lock",
                                    label_visibility="collapsed",
                                )
                                state["locked"][cat] = new_locked
                            with col_lock_icon:
                                if new_locked:
                                    st.markdown('<span style="color: #FFD700; font-size: 1.2em; margin-right: 15px;">🔒</span>', unsafe_allow_html=True)
                                else:
                                    st.markdown('<span style="color: #666; font-size: 1.2em; margin-right: 15px;">🔓</span>', unsafe_allow_html=True)

        with col_right:
            st.subheader("Aperçu")
            brief_text = compose_brief_text(domain, mode_name, state["selections"])
            # Cadre esthétique autour de l'aperçu avec texte à l'intérieur
            _escaped = _html.escape(brief_text).replace("\n", "<br>")
            st.markdown(
                f"""
                <div style=\"border:1px solid rgba(120,120,120,0.35); border-radius:10px; padding:16px; background: rgba(0,0,0,0.03);\">{_escaped}</div>
                """,
                unsafe_allow_html=True,
            )
            # Petit espace entre l'aperçu et le bouton Regénérer
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            
            # Bouton Regénérer sous l'aperçu
            if st.button("🎲 Regénérer", key=f"regen_{mode_key}", use_container_width=True):
                # Increment seed
                before_seed = st.session_state[mode_key]["seed"]
                st.session_state[mode_key]["seed"] += 1
                st.session_state[mode_key]["render_nonce"] = int(st.session_state[mode_key].get("render_nonce", 0)) + 1
                new_seed = st.session_state[mode_key]["seed"]
                before_sel = dict(st.session_state[mode_key]["selections"])  # shallow copy
                before_locked = dict(st.session_state[mode_key]["locked"])  # shallow copy
                
                # Get template and needed categories
                template = BRIEF_TEMPLATES.get(domain, {}).get(mode_name, "")
                needed = []
                for m in re.findall(r"\[([A-ZÉÈÀÂÙÏÇ_ ]+)\]", template):
                    if m not in needed:
                        needed.append(m)
                
                # Generate new random selections respecting locks
                rng = random.Random(new_seed)
                changed = {}
                for cat in needed:
                    if st.session_state[mode_key]["locked"].get(cat):
                        # Keep locked value - don't change it
                        continue
                    else:
                        # Pick a different value from current to avoid repeating
                        opts = TAGS_REGISTRY.get(domain, {}).get(cat, [])
                        current = st.session_state[mode_key]["selections"].get(cat)
                        if len(opts) > 1:
                            available = [opt for opt in opts if opt != current]
                            new_val = rng.choice(available) if available else rng.choice(opts)
                            st.session_state[mode_key]["selections"][cat] = new_val
                            # Sync widget state so UI reflects the new value
                            st.session_state[f"{mode_key}_{cat}_select"] = new_val
                            if new_val != current:
                                changed[cat] = (current, new_val)
                        elif opts:
                            new_val = rng.choice(opts)
                            st.session_state[mode_key]["selections"][cat] = new_val
                            st.session_state[f"{mode_key}_{cat}_select"] = new_val
                            if new_val != current:
                                changed[cat] = (current, new_val)
                
                # Force Streamlit to rerun to show new values
                # Try modern st.rerun() first, fallback to experimental if needed
                try:
                    logger.info(
                        "[creation] regenerate clicked mode_key=%s seed %s->%s nonce=%s changed=%s locked=%s",
                        mode_key,
                        before_seed,
                        new_seed,
                        st.session_state[mode_key]["render_nonce"],
                        {k: f"{v[0]}→{v[1]}" for k, v in changed.items()},
                        {k: v for k, v in before_locked.items() if v},
                    )
                    st.rerun()
                except AttributeError:
                    try:
                        logger.warning("[creation] st.rerun() missing, falling back to experimental_rerun()")
                        st.experimental_rerun()
                    except AttributeError:
                        # Fallback: set a flag to trigger rerun on next render
                        logger.error("[creation] No rerun method available; setting _force_rerun flag")
                        st.session_state._force_rerun = True

        # Expose selections and locks for tests/debug
        if mode_name == "simple":
            st.session_state._random_simple_selections = dict(state["selections"])  # shallow copy
            st.session_state._random_simple_locked = dict(state["locked"])  # shallow copy
        else:
            st.session_state._random_complex_selections = dict(state["selections"])  # shallow copy
            st.session_state._random_complex_locked = dict(state["locked"])  # shallow copy

        return brief_text

    tabs = st.tabs(["Écriture libre", "Aléatoire", "Aléatoire complexe"])
    with tabs[0]:
        free_text = _render_free_tab()
    with tabs[1]:
        brief_random_simple = _render_random_tab("random_simple_state", "simple")
    with tabs[2]:
        brief_random_complex = _render_random_tab("random_complex_state", "complexe")

    _ensure_session_defaults(domain, model_info)

    intent_options = INTENT_OPTIONS[domain]
    level_options = LEVEL_OPTIONS[domain]
    dialogue_options = DIALOGUE_OPTIONS.get(domain, [])
    atmosphere_options = ATMOSPHERE_OPTIONS.get(domain, [])
    # Ensure a defined dialogue_mode variable for all domains
    dialogue_mode = st.session_state.get("dialogue_mode", "parle") if domain == "Personnages" else "none"
    # Sanitize dialogue_mode when switching back to Personnages
    if domain == "Personnages" and dialogue_options:
        if st.session_state.get("dialogue_mode") not in dialogue_options:
            st.session_state.dialogue_mode = dialogue_options[0]

    def _safe_index(options_list, value, default_idx: int = 0) -> int:
        try:
            return options_list.index(value)
        except Exception:
            return default_idx if options_list else 0

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
                index=_safe_index(intent_options, st.session_state.intent, 0),
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
                index=_safe_index(level_options, st.session_state.level, 0),
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
                    index=_safe_index(atmosphere_options, st.session_state.atmosphere, 0),
                    help="Ambiance générale du lieu",
                    key=f"atmosphere_select_{st.session_state.random_seed}",
                )
        elif domain == "Personnages":
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
                    index=_safe_index(dialogue_options, st.session_state.dialogue_mode, 0),
                    help="Comment le personnage communique",
                    key=f"dialogue_select_{st.session_state.random_seed}",
                )
        else:
            # No extra control for dialogue/atmosphere on other domains
            pass

    with col2:
        st.subheader("Paramètres Techniques")

        provider = model_info.get("provider")
        uses_reasoning = bool(model_info.get("uses_reasoning"))

        if provider == "OpenAI" and uses_reasoning:
            reasoning_options = ["minimal", "low", "medium", "high"]
            verbosity_options = ["low", "medium", "high"]

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

            # Verbosity control (GPT-5 only)
            def randomize_verbosity():
                st.session_state.verbosity = _random_different(
                    verbosity_options, st.session_state.verbosity
                )
                st.session_state.random_seed += 1

            col_verbosity, col_verbosity_random = st.columns([4, 1])
            with col_verbosity_random:
                st.write("")
                st.write("")
                st.button(
                    "🎲",
                    key="random_verbosity",
                    help="Valeur aléatoire",
                    on_click=randomize_verbosity,
                )
            with col_verbosity:
                verbosity = st.selectbox(
                    "Verbosity (niveau de détail)",
                    options=verbosity_options,
                    index=verbosity_options.index(st.session_state.verbosity),
                    help="low = concis | medium = équilibré | high = détaillé",
                    key=f"verbosity_select_{st.session_state.random_seed}",
                )
            # Anthropic reasoning toggle not shown here
            st.session_state.include_reasoning = True
        else:
            # Temperature UI (Anthropic, Mistral, Ollama, or OpenAI non-reasoning)
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

            # Anthropic: show optional reasoning toggle (if provider supports it)
            if provider == "Anthropic":
                st.checkbox(
                    "Afficher le raisonnement (si disponible)",
                    value=st.session_state.get("include_reasoning", True),
                    key="include_reasoning",
                    help="Affiche un flux de raisonnement si le modèle en renvoie. Ne change pas les paramètres du modèle.",
                )

        st.write("")
        # Toggle: Travail agentique (Writer seul si décoché)
        st.session_state.agentic_work = st.checkbox(
            "Travail agentique",
            value=bool(st.session_state.get("agentic_work", True)),
            help="Quand décoché, seule l'étape d'écriture (Writer) est exécutée. Les étapes d'analyse/correction/validation sont sautées (plus rapide).",
        )
        max_tokens = st.slider(
            "Max tokens (sortie)",
            min_value=50000,
            max_value=500000,
            value=st.session_state.max_tokens,
            step=10000,
            help="Limite de tokens pour la réponse (50000-300000). ⚠️ GPT-5 utilise des tokens pour le reasoning !",
            key=f"max_tokens_slider_{st.session_state.random_seed}",
        )

        # Encadré de configuration retiré (doublon avec la barre latérale)

    st.session_state.intent = intent
    st.session_state.level = level
    if domain == "Lieux":
        st.session_state.atmosphere = atmosphere
        dialogue_mode = "none"
    elif domain == "Personnages":
        st.session_state.dialogue_mode = dialogue_mode
    else:
        dialogue_mode = "none"

    if provider == "OpenAI" and uses_reasoning:
        st.session_state.reasoning_effort = reasoning_effort
        st.session_state.verbosity = verbosity
    else:
        st.session_state.creativity = creativity

    st.session_state.max_tokens = max_tokens

    # Persist current prefs (best-effort)
    try:
        prefs = load_ui_prefs()
        prefs.update({
            "intent": intent,
            "level": level,
            "dialogue_mode": dialogue_mode,
            "atmosphere": st.session_state.get("atmosphere"),
            "creativity": st.session_state.get("creativity"),
            "reasoning_effort": st.session_state.get("reasoning_effort"),
            "max_tokens": max_tokens,
            "verbosity": st.session_state.get("verbosity"),
            "agentic_work": st.session_state.get("agentic_work", True),
        })
        save_ui_prefs(prefs)
    except Exception:
        pass

    # Determine active brief text based on selected mode
    if st.session_state.brief_mode == "free":
        active_brief_text = free_text
    elif st.session_state.brief_mode == "random_simple":
        active_brief_text = brief_random_simple
    else:
        active_brief_text = brief_random_complex

    st.subheader("📚 Contexte Notion")
    with st.expander("Sélectionner du contexte depuis Notion", expanded=True):
        # Expose active brief to session for testability (no UI impact)
        st.session_state._active_brief_text = active_brief_text
        context_summary = render_context_selector(domain, active_brief_text)
        st.session_state.selected_context_summary = context_summary

    button_text = {
        "Personnages": "🚀 Générer le Personnage",
        "Lieux": "🚀 Générer le Lieu",
        "Espèces": "🚀 Générer l'Espèce",
        "Communautés": "🚀 Générer la Communauté",
    }
    error_text = {
        "Personnages": "⚠️ Veuillez fournir une description du personnage",
        "Lieux": "⚠️ Veuillez fournir une description du lieu",
        "Espèces": "⚠️ Veuillez fournir une description de l'espèce",
        "Communautés": "⚠️ Veuillez fournir une description de la communauté",
    }

    trigger = st.session_state.pop("trigger_generate", False)
    if st.button(button_text[domain], type="primary", use_container_width=True) or trigger:
        if not active_brief_text:
            st.error(error_text[domain])
        else:
            # Ensure verbosity variable exists in all branches
            _verbosity = verbosity if (provider == "OpenAI" and uses_reasoning) else None
            # Force-commit latest checkbox state just before generation
            try:
                from .context_selector import force_commit_selection
                committed = force_commit_selection()
                # Small latency to allow Streamlit state propagation
                import time as _t
                _t.sleep(0.05)
                # Prefer freshly committed selection when non-empty
                if committed and committed.get("selected_ids"):
                    context_summary = committed
            except Exception:
                pass
            generate_content(
                active_brief_text,
                intent,
                level,
                dialogue_mode,
                creativity if creativity is not None else st.session_state.creativity,
                reasoning_effort,
                _verbosity,
                max_tokens,
                selected_model,
                model_info,
                domain,
                context_summary,
                include_reasoning=st.session_state.get("include_reasoning") if model_info.get("provider") == "Anthropic" else True if (model_info.get("provider") == "OpenAI" and model_info.get("uses_reasoning")) else False,
                agentic_work=bool(st.session_state.get("agentic_work", True)),
            )

            # Gestion export Notion immédiate si flag déjà posé (cas rare pendant génération)
            from .results import export_to_notion  # local import
            if st.session_state.pop("trigger_export", False):
                payload = st.session_state.get("_pending_export_payload") or st.session_state.get("_last_generation_result")
                if payload:
                    export_container = st.container()
                    with export_container:
                        export_to_notion(payload)
    # Zone PERSISTANTE: affichée juste après "Contenu final" et avant "Options avancées"
    last_json = st.session_state.get("_last_saved_json")
    last_md = st.session_state.get("_last_saved_md")
    if last_json or last_md:
        col_files_persist, col_export_persist = st.columns([2, 1])
        with col_files_persist:
            from pathlib import Path as _Path
            json_name = _Path(last_json).name if last_json else None
            md_name = _Path(last_md).name if last_md else None
            info_lines = ["**Fichiers sauvegardés:**"]
            if json_name:
                info_lines.append(f"- 📊 JSON: `{json_name}`")
            if md_name:
                info_lines.append(f"- 📝 Markdown: `{md_name}`")
            st.info("\n".join(info_lines))
        with col_export_persist:
            if st.button(
                "📤 Exporter vers Notion",
                key="export_btn_persist_inline",
                help="Créer une page dans Notion",
                disabled=bool(st.session_state.get("_export_in_progress", False)),
            ):
                try:
                    st.session_state._pending_export_payload = dict(st.session_state.get("_last_generation_result") or {})
                except Exception:
                    st.session_state._pending_export_payload = st.session_state.get("_last_generation_result")
                st.session_state._export_in_progress = True
                st.session_state.trigger_export = True
            if last_json:
                try:
                    with open(last_json, "r", encoding="utf-8") as _h:
                        st.download_button(
                            label="💾 Télécharger JSON",
                            data=_h.read(),
                            file_name=_Path(last_json).name,
                            mime="application/json",
                            key="download_json_persist",
                        )
                except Exception:
                    pass

    # Feedback export persistant (si présent)
    persisted_creation = st.session_state.get("_export_creation")
    if isinstance(persisted_creation, dict):
        if persisted_creation.get("success"):
            page_url = persisted_creation.get("page_url") or "https://www.notion.so"
            st.markdown(
                f"""
            <div style=\"background-color:#ecfdf5;border-left:5px solid #10b981;padding:1rem;margin:1rem 0;border-radius:.5rem;\">✅ Export confirmé — <a href=\"{page_url}\" target=\"_blank\" style=\"color:#047857;text-decoration:underline;font-weight:600;\">ouvrir la fiche</a></div>
            """,
                unsafe_allow_html=True,
            )
        elif persisted_creation.get("error"):
            st.error(f"❌ Échec export: {persisted_creation.get('error')}")
    # QoL: Reset parameters button
    with st.expander("⚙️ Options avancées"):
        col_reset, col_cancel = st.columns(2)
        with col_reset:
            if st.button("🔄 Réinitialiser paramètres"):
                for key in [
                    "intent",
                    "level",
                    "dialogue_mode",
                    "atmosphere",
                    "creativity",
                    "reasoning_effort",
                    "max_tokens",
                    "selected_profile",
                ]:
                    if key in st.session_state:
                        del st.session_state[key]
                # Clear persisted prefs as well
                try:
                    save_ui_prefs({})
                except Exception:
                    pass
                st.experimental_rerun()
        with col_cancel:
            # Placeholder for future cancel: would require cooperative checks in workflow
            st.caption("Annuler la génération (prochain itératif)")

    # Gestion export globale (s'exécute à chaque rerun)
    from .results import export_to_notion  # local import
    if st.session_state.pop("trigger_export", False):
        payload = st.session_state.get("_pending_export_payload") or st.session_state.get("_last_generation_result")
        if payload:
            export_feedback_global = st.container()
            with export_feedback_global:
                st.session_state._export_in_progress = True
                with st.spinner("📤 Export vers Notion en cours…"):
                    export_to_notion(payload)
                st.session_state._export_in_progress = False
