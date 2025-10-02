#!/usr/bin/env python3
"""
Interface Streamlit pour le système multi-agents GDD Alteir
"""
import streamlit as st
import sys
from pathlib import Path
import json
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

# Configuration de la page
st.set_page_config(
    page_title="GDD Alteir - Multi-Agents",
    page_icon="🤖",
    layout="wide"
)

# === OPTIMISATIONS: Lazy Loading avec Cache ===

@st.cache_resource(show_spinner="Chargement des dépendances...")
def load_workflow_dependencies(domain="personnages"):
    """Charge les dépendances lourdes une seule fois"""
    from workflows.content_workflow import ContentWorkflow
    from agents.writer_agent import WriterConfig
    
    if domain == "lieux":
        from config.domain_configs.lieux_config import LIEUX_CONFIG
        return ContentWorkflow, WriterConfig, LIEUX_CONFIG
    else:
        from config.domain_configs.personnages_config import PERSONNAGES_CONFIG
        return ContentWorkflow, WriterConfig, PERSONNAGES_CONFIG

@st.cache_data(ttl=60)
def get_outputs_count():
    """Cache le comptage des fichiers pour 60 secondes"""
    outputs_dir = Path("outputs")
    if outputs_dir.exists():
        return len(list(outputs_dir.glob("*.json")))
    return 0

@st.cache_data(ttl=30)
def list_output_files():
    """Cache la liste des fichiers pour 30 secondes"""
    outputs_dir = Path("outputs")
    if not outputs_dir.exists():
        return []
    
    json_files = sorted(
        outputs_dir.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    return [f.stem for f in json_files]

@st.cache_data
def load_result_file(file_stem: str):
    """Cache le chargement d'un fichier résultat"""
    outputs_dir = Path("outputs")
    json_path = outputs_dir / f"{file_stem}.json"
    
    if not json_path.exists():
        return None
    
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Style CSS
st.markdown("""
<style>
/* Réduire l'espace en haut */
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 0rem;
}

/* En-tête principal avec gradient et design moderne */
.main-header {
    font-size: 2.8rem;
    font-weight: 800;
    text-align: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0.5rem 0 1rem 0;
    padding: 0.5rem 0;
    letter-spacing: -0.02em;
}

.subtitle {
    text-align: center;
    color: #666;
    font-size: 1rem;
    margin-top: -0.5rem;
    margin-bottom: 1.5rem;
}

.header-divider {
    height: 3px;
    background: linear-gradient(90deg, transparent, #667eea, #764ba2, transparent);
    margin: 1rem auto 2rem auto;
    border-radius: 2px;
    max-width: 300px;
}

.metric-box {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}

.success-box {
    background-color: #d4edda;
    border-left: 4px solid #28a745;
    padding: 1rem;
    margin: 1rem 0;
}

.warning-box {
    background-color: #fff3cd;
    border-left: 4px solid #ffc107;
    padding: 1rem;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

def main():
    """Interface principale"""
    
    # En-tête avec design moderne
    st.markdown('''
    <div style="text-align: center;">
        <h1 class="main-header">🤖 Système Multi-Agents</h1>
        <p class="subtitle">Création collaborative de contenu pour le GDD Alteir</p>
        <div class="header-divider"></div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        st.subheader("Modèle LLM")
        
        # Modèles disponibles avec leurs specs
        MODELS = {
            "GPT-5": {
                "name": "gpt-5",
                "provider": "OpenAI",
                "description": "Modèle le plus puissant, raisonnement approfondi",
                "max_tokens": 4000,
                "icon": "🚀",
                "uses_reasoning": True,
                "default_reasoning": "medium"
            },
            "GPT-5-mini": {
                "name": "gpt-5-mini",
                "provider": "OpenAI",
                "description": "Équilibré entre performance et coût",
                "max_tokens": 3000,
                "icon": "⚡",
                "uses_reasoning": True,
                "default_reasoning": "low"
            },
            "GPT-5-nano": {
                "name": "gpt-5-nano",
                "provider": "OpenAI",
                "description": "Rapide et économique, idéal pour itérations",
                "max_tokens": 2000,
                "icon": "✨",
                "uses_reasoning": True,
                "default_reasoning": "minimal"
            },
            "GPT-4o-mini": {
                "name": "gpt-4o-mini",
                "provider": "OpenAI",
                "description": "Modèle de fallback stable",
                "max_tokens": 2000,
                "icon": "🔄",
                "uses_reasoning": False
            }
        }
        
        selected_model = st.selectbox(
            "Modèle",
            options=list(MODELS.keys()),
            index=2,  # GPT-5-nano par défaut
            format_func=lambda x: f"{MODELS[x]['icon']} {x}",
            help="Choisir le modèle LLM pour la génération"
        )
        
        # Afficher les détails du modèle sélectionné
        model_info = MODELS[selected_model]
        st.caption(f"**{model_info['provider']}** • {model_info['description']}")
        
        st.subheader("Domaine")
        domain = st.selectbox(
            "Domaine", 
            ["Personnages", "Lieux"], 
            index=0,
            help="Choisir le type de contenu à générer"
        )
        
        # Icône selon le domaine
        domain_icons = {
            "Personnages": "👤",
            "Lieux": "🏛️"
        }
        st.caption(f"{domain_icons[domain]} **{domain}**")
        
        st.subheader("📊 Statistiques")
        nb_files = get_outputs_count()  # Utilise le cache
        st.metric("Générations", nb_files)
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["✨ Créer", "📂 Résultats", "🕸️ Graphe", "ℹ️ À propos"])
    
    # TAB 1: Création
    with tab1:
        # En-tête adapté au domaine
        domain_headers = {
            "Personnages": "Créer un Personnage",
            "Lieux": "Créer un Lieu"
        }
        st.header(domain_headers[domain])
        
        # Exemples de briefs selon le domaine
        BRIEF_EXAMPLES_PERSONNAGES = [
            "Un alchimiste qui transforme les émotions en substances physiques. Genre: Non défini. Espèce: Humain modifié. Âge: 38 cycles. Membre d'une guilde secrète, cache une dépendance à ses propres créations.",
            "Un cartographe solitaire membre d'un culte cherchant des ossements divins. Genre: Féminin. Espèce: Humaine. Âge: 45 cycles. Porte un compas en os qui vibre près des reliques.",
            "Un marchand d'ombres qui vend des souvenirs oubliés. Genre: Non binaire. Espèce: Gedroth. Âge: 102 cycles. Ancien bibliothécaire devenu contrebandier de mémoires interdites.",
            "Une chasseuse de primes cybernétique traquant son propre créateur. Genre: Féminin. Espèce: Hybride mécanique. Âge: 28 cycles. Recherche la vérité sur ses origines.",
            "Un barde aveugle qui voit les émotions comme des couleurs. Genre: Masculin. Espèce: Humain. Âge: 34 cycles. Autrefois peintre célèbre, maintenant musicien errant.",
            "Une archéologue obsédée par une civilisation disparue dont elle rêve chaque nuit. Genre: Féminin. Espèce: Humaine modifiée. Âge: 41 cycles. Collectionne des artefacts qui lui causent des visions.",
            "Un escargot cyberpunk touche-à-tout géotrouvetout et amateur d'art. Genre: Non défini. Espèce: Escargot modifié. Âge: 27 cycles. Rêve de créer une galerie underground.",
            "Un ancien soldat reconverti en chef cuisinier utilisant des ingrédients interdits. Genre: Masculin. Espèce: Humain. Âge: 52 cycles. Ses plats réveillent des souvenirs enfouis.",
        ]
        
        BRIEF_EXAMPLES_LIEUX = [
            "Une bibliothèque souterraine abandonnée dont les livres murmurent. Taille: Site. Rôle: Lieu de culte. Autrefois lieu de savoir, maintenant repaire de cultistes.",
            "Un marché flottant sur des plateformes organiques qui respirent. Taille: Secteur. Rôle: Lieu commercial. Construit sur le dos d'une créature endormie.",
            "Les ruines d'une station de purification d'eau devenue sanctuaire. Taille: Point d'intérêt. Rôle: Zone magique. L'eau y coule encore, mais transforme ce qu'elle touche.",
            "Un quartier vertical dans les entrailles d'un Léviathan pétrifié. Taille: District. Rôle: Ville. Sept niveaux de habitations creusées dans l'os ancien.",
            "Une forge maudite où les armes forgées pleurent. Taille: Site. Rôle: Lieu artisanal. Les artisans y travaillent avec des masques pour ne pas entendre.",
            "Un jardin suspendu où poussent des souvenirs cristallisés. Taille: Site. Rôle: Zone naturelle. Entretenu par des jardiniers aveugles qui récoltent les rêves.",
            "Une gare abandonnée devenue labyrinthe de rails fantômes. Taille: Secteur. Rôle: Lieu unique. Des trains spectraux y passent encore certaines nuits.",
        ]
        
        BRIEF_EXAMPLES = BRIEF_EXAMPLES_LIEUX if domain == "Lieux" else BRIEF_EXAMPLES_PERSONNAGES
        
        # Brief avec boutons d'exemple
        col_brief_label, col_example_btn = st.columns([4, 1])
        with col_brief_label:
            brief_label = "Description du lieu" if domain == "Lieux" else "Description du personnage"
            st.markdown(f"**{brief_label}**")
        with col_example_btn:
            if st.button("🎲 Brief aléatoire", help="Charger un exemple de brief"):
                import random
                st.session_state.brief_example = random.choice(BRIEF_EXAMPLES)
                st.rerun()
        
        brief_placeholder = {
            "Personnages": "Ex: Un alchimiste qui transforme les émotions en substances physiques...",
            "Lieux": "Ex: Une bibliothèque souterraine dont les livres murmurent..."
        }
        
        brief = st.text_area(
            brief_label,
            value=st.session_state.get('brief_example', ''),
            placeholder=brief_placeholder[domain],
            height=100,
            label_visibility="collapsed"
        )
        
        # Initialiser session state pour les paramètres
        import random
        if 'random_seed' not in st.session_state:
            st.session_state.random_seed = 0
        
        # Options disponibles selon le domaine
        if domain == "Lieux":
            intent_options = ["hub_central", "passage_obligé", "zone_exploration", "lieu_secret"]
            level_options = ["point_interet", "site", "secteur", "district"]
            atmosphere_options = ["oppressante", "vivante", "sacrée", "hostile", "accueillante", "neutre"]
            
            # Initialiser les valeurs par défaut pour lieux
            if 'intent' not in st.session_state or domain != st.session_state.get('last_domain'):
                st.session_state.intent = "zone_exploration"
            if 'level' not in st.session_state or domain != st.session_state.get('last_domain'):
                st.session_state.level = "site"
            if 'atmosphere' not in st.session_state:
                st.session_state.atmosphere = "neutre"
        else:  # Personnages
            intent_options = ["orthogonal_depth", "vocation_pure", "archetype_assume", "mystere_non_resolu"]
            level_options = ["cameo", "standard", "major"]
            dialogue_options = ["parle", "gestuel", "telepathique", "ecrit_only"]
            
            # Initialiser les valeurs par défaut pour personnages
            if 'intent' not in st.session_state or domain != st.session_state.get('last_domain'):
                st.session_state.intent = "orthogonal_depth"
            if 'level' not in st.session_state or domain != st.session_state.get('last_domain'):
                st.session_state.level = "standard"
            if 'dialogue_mode' not in st.session_state:
                st.session_state.dialogue_mode = "parle"
        
        if 'creativity' not in st.session_state:
            st.session_state.creativity = 0.7
        
        # Initialiser reasoning_effort selon le modèle
        if 'reasoning_effort' not in st.session_state:
            st.session_state.reasoning_effort = MODELS[selected_model].get("default_reasoning", "minimal")
        
        # Initialiser max_tokens
        if 'max_tokens' not in st.session_state:
            st.session_state.max_tokens = 5000  # Valeur par défaut
        
        # Mémoriser le dernier domaine
        st.session_state.last_domain = domain
        
        # Fonction helper pour choisir une valeur différente
        def random_different(options, current):
            """Choisit une valeur aléatoire différente de la valeur actuelle"""
            if len(options) <= 1:
                return options[0] if options else current
            available = [opt for opt in options if opt != current]
            return random.choice(available)
        
        # Callbacks pour optimisation (évite reruns)
        def randomize_all():
            st.session_state.intent = random_different(intent_options, st.session_state.intent)
            st.session_state.level = random_different(level_options, st.session_state.level)
            if domain == "Lieux":
                st.session_state.atmosphere = random_different(atmosphere_options, st.session_state.atmosphere)
            else:
                st.session_state.dialogue_mode = random_different(dialogue_options, st.session_state.dialogue_mode)
            while True:
                new_creativity = round(random.uniform(0.5, 0.9), 2)
                if abs(new_creativity - st.session_state.creativity) >= 0.1:
                    st.session_state.creativity = new_creativity
                    break
            st.session_state.random_seed += 1
        
        def randomize_intent():
            st.session_state.intent = random_different(intent_options, st.session_state.intent)
            st.session_state.random_seed += 1
        
        def randomize_level():
            st.session_state.level = random_different(level_options, st.session_state.level)
            st.session_state.random_seed += 1
        
        def randomize_dialogue():
            st.session_state.dialogue_mode = random_different(dialogue_options, st.session_state.dialogue_mode)
            st.session_state.random_seed += 1
        
        def randomize_creativity():
            while True:
                new_creativity = round(random.uniform(0.5, 0.9), 2)
                if abs(new_creativity - st.session_state.creativity) >= 0.1:
                    st.session_state.creativity = new_creativity
                    break
            st.session_state.random_seed += 1
        
        # Profils prédéfinis et bouton dé global
        st.subheader("Profils & Paramètres")
        
        # Profils prédéfinis selon le domaine
        if domain == "Lieux":
            PROFILS = {
                "Hub central": {
                    "intent": "hub_central",
                    "level": "district",
                    "atmosphere": "vivante",
                    "creativity": 0.75,
                    "description": "Lieu de convergence, plein de vie et d'activités"
                },
                "Zone d'exploration": {
                    "intent": "zone_exploration",
                    "level": "secteur",
                    "atmosphere": "neutre",
                    "creativity": 0.70,
                    "description": "Zone à découvrir, secrets et opportunités"
                },
                "Passage obligé": {
                    "intent": "passage_obligé",
                    "level": "site",
                    "atmosphere": "hostile",
                    "creativity": 0.65,
                    "description": "Lieu de transit, dangers potentiels"
                },
                "Lieu secret": {
                    "intent": "lieu_secret",
                    "level": "point_interet",
                    "atmosphere": "oppressante",
                    "creativity": 0.80,
                    "description": "Caché, découverte importante"
                },
                "Sanctuaire": {
                    "intent": "lieu_secret",
                    "level": "site",
                    "atmosphere": "sacrée",
                    "creativity": 0.85,
                    "description": "Lieu de culte ou protection, ambiance spirituelle"
                },
            }
        else:  # Personnages
            PROFILS = {
                "Personnage principal": {
                    "intent": "orthogonal_depth",
                    "level": "major",
                    "dialogue_mode": "parle",
                    "creativity": 0.75,
                    "description": "Profondeur maximale, 10-12 répliques, 2-4 relations"
                },
                "PNJ secondaire": {
                    "intent": "orthogonal_depth",
                    "level": "standard",
                    "dialogue_mode": "parle",
                    "creativity": 0.70,
                    "description": "Profondeur moyenne, 8-10 répliques, 1-3 relations"
                },
                "Cameo/Figurant": {
                    "intent": "mystere_non_resolu",
                    "level": "cameo",
                    "dialogue_mode": "parle",
                    "creativity": 0.65,
                    "description": "Présence minimale, 4-6 répliques, 0-1 relation"
                },
                "Boss/Antagoniste": {
                    "intent": "archetype_assume",
                    "level": "major",
                    "dialogue_mode": "parle",
                    "creativity": 0.80,
                    "description": "Archétype assumé, profondeur maximale"
                },
                "Personnage mystérieux": {
                    "intent": "mystere_non_resolu",
                    "level": "standard",
                    "dialogue_mode": "gestuel",
                    "creativity": 0.85,
                    "description": "Zones d'ombre, communication non-verbale"
                },
            }
        
        def apply_profile():
            """Applique un profil prédéfini automatiquement"""
            if st.session_state.selected_profile != "Personnalisé":
                profile = PROFILS[st.session_state.selected_profile]
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
                ["Personnalisé"] + list(PROFILS.keys()),
                help="Charger une configuration prédéfinie",
                key="selected_profile",
                on_change=apply_profile
            )
            if selected_profile != "Personnalisé":
                st.caption(f"ℹ️ {PROFILS[selected_profile]['description']}")
        
        with col_dice:
            st.write("")
            st.write("")
            st.button("🎲", 
                     help="Mélanger tous les paramètres", 
                     use_container_width=True,
                     on_click=randomize_all)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Paramètres Narratifs")
            
            # Intention narrative (personnages) ou Fonction narrative (lieux)
            col_intent, col_intent_random = st.columns([4, 1])
            with col_intent_random:
                st.write("")  # Spacer
                st.write("")  # Spacer
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
                    key=f"intent_select_{st.session_state.random_seed}"
                )
            
            # Niveau de détail (personnages) ou Échelle (lieux)
            col_level, col_level_random = st.columns([4, 1])
            with col_level_random:
                st.write("")  # Spacer
                st.write("")  # Spacer
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
                    key=f"level_select_{st.session_state.random_seed}"
                )
            
            # Mode de dialogue (Personnages) OU Atmosphère (Lieux)
            if domain == "Lieux":
                def randomize_atmosphere():
                    st.session_state.atmosphere = random_different(atmosphere_options, st.session_state.atmosphere)
                    st.session_state.random_seed += 1
                
                col_atmosphere, col_atmosphere_random = st.columns([4, 1])
                with col_atmosphere_random:
                    st.write("")  # Spacer
                    st.write("")  # Spacer
                    st.button("🎲", key="random_atmosphere", help="Valeur aléatoire", on_click=randomize_atmosphere)
                with col_atmosphere:
                    atmosphere = st.selectbox(
                        "Atmosphère",
                        atmosphere_options,
                        index=atmosphere_options.index(st.session_state.atmosphere),
                        help="Ambiance générale du lieu",
                        key=f"atmosphere_select_{st.session_state.random_seed}"
                    )
            else:  # Personnages
                col_dialogue, col_dialogue_random = st.columns([4, 1])
                with col_dialogue_random:
                    st.write("")  # Spacer
                    st.write("")  # Spacer
                    st.button("🎲", key="random_dialogue", help="Valeur aléatoire", on_click=randomize_dialogue)
                with col_dialogue:
                    dialogue_mode = st.selectbox(
                        "Mode de dialogue",
                        dialogue_options,
                        index=dialogue_options.index(st.session_state.dialogue_mode),
                        help="Comment le personnage communique",
                        key=f"dialogue_select_{st.session_state.random_seed}"
                    )
        
        with col2:
            st.subheader("Paramètres Techniques")
            
            # Température (GPT-4) OU Reasoning Effort (GPT-5)
            if model_info.get("uses_reasoning"):
                # GPT-5 : Reasoning Effort
                reasoning_options = ["minimal", "low", "medium", "high"]
                
                def randomize_reasoning():
                    st.session_state.reasoning_effort = random_different(reasoning_options, st.session_state.reasoning_effort)
                    st.session_state.random_seed += 1
                
                col_reasoning, col_reasoning_random = st.columns([4, 1])
                with col_reasoning_random:
                    st.write("")  # Spacer
                    st.write("")  # Spacer
                    st.button("🎲", key="random_reasoning", help="Valeur aléatoire", on_click=randomize_reasoning)
                with col_reasoning:
                    reasoning_effort = st.selectbox(
                        "Effort de raisonnement",
                        options=reasoning_options,
                        index=reasoning_options.index(st.session_state.reasoning_effort),
                        help="minimal = rapide | low = équilibré | medium = standard | high = approfondi",
                        key=f"reasoning_select_{st.session_state.random_seed}"
                    )
                    creativity = None  # Pas utilisé pour GPT-5
            else:
                # GPT-4 : Température classique
                col_creativity, col_creativity_random = st.columns([4, 1])
                with col_creativity_random:
                    st.write("")  # Spacer
                    st.write("")  # Spacer
                    st.write("")  # Spacer
                    st.write("")  # Spacer
                    st.button("🎲", key="random_creativity", help="Valeur aléatoire", on_click=randomize_creativity)
                with col_creativity:
                    creativity = st.slider(
                        "Créativité (température)",
                        min_value=0.0,
                        max_value=1.0,
                        value=st.session_state.creativity,
                        step=0.01,
                        help="0 = déterministe | 1 = très créatif",
                        key=f"creativity_slider_{st.session_state.random_seed}"
                    )
                    reasoning_effort = None  # Pas utilisé pour GPT-4
            
            # Max tokens (pour tous les modèles)
            st.write("")  # Spacer
            max_tokens = st.slider(
                "Max tokens (sortie)",
                min_value=1000,
                max_value=30000,
                value=st.session_state.max_tokens,
                step=1000,
                help="Limite de tokens pour la réponse (1000-30000). ⚠️ GPT-5 utilise des tokens pour le reasoning !",
                key=f"max_tokens_slider_{st.session_state.random_seed}"
            )
            
            # Configuration affichée selon le domaine et le modèle
            config_lines = [f"- Intent: `{intent}`"]
            
            if domain == "Lieux":
                config_lines.extend([
                    f"- Échelle: `{level}`",
                    f"- Atmosphère: `{atmosphere}`"
                ])
            else:
                config_lines.extend([
                    f"- Niveau: `{level}`",
                    f"- Dialogue: `{dialogue_mode}`"
                ])
            
            # Paramètre de créativité/reasoning selon le modèle
            if model_info.get("uses_reasoning"):
                config_lines.append(f"- Reasoning: `{reasoning_effort}`")
            else:
                config_lines.append(f"- Température: `{creativity}`")
            
            # Max tokens pour tous
            config_lines.append(f"- Max tokens: `{max_tokens}`")
            
            st.info("**Configuration:**\n" + "\n".join(config_lines))
        
        # Mettre à jour session state avec les valeurs choisies manuellement
        st.session_state.intent = intent
        st.session_state.level = level
        if domain == "Lieux":
            st.session_state.atmosphere = atmosphere
            dialogue_mode = "none"  # Valeur par défaut pour lieux
        else:
            st.session_state.dialogue_mode = dialogue_mode
        
        # Mettre à jour selon le type de modèle
        if model_info.get("uses_reasoning"):
            st.session_state.reasoning_effort = reasoning_effort
        else:
            st.session_state.creativity = creativity
        
        # Mettre à jour max_tokens
        st.session_state.max_tokens = max_tokens
        
        # Bouton de génération adapté au domaine
        button_text = {
            "Personnages": "🚀 Générer le Personnage",
            "Lieux": "🚀 Générer le Lieu"
        }
        error_text = {
            "Personnages": "⚠️ Veuillez fournir une description du personnage",
            "Lieux": "⚠️ Veuillez fournir une description du lieu"
        }
        
        if st.button(button_text[domain], type="primary", use_container_width=True):
            if not brief:
                st.error(error_text[domain])
            else:
                generate_content(brief, intent, level, dialogue_mode, creativity, reasoning_effort, max_tokens, selected_model, MODELS[selected_model], domain)
    
    # TAB 2: Résultats
    with tab2:
        st.header("Résultats Générés")
        
        show_results()
    
    # TAB 3: Graphe de relations
    with tab3:
        st.header("🕸️ Graphe de Relations")
        
        st.info("""
        📊 **Visualisation des relations entre entités**
        
        Cette fonctionnalité permet de visualiser les liens entre personnages, lieux, communautés et objets dans l'univers Alteir.
        """)
        
        # Sélection du type de graphe
        graph_type = st.selectbox(
            "Type de graphe",
            ["Personnages", "Lieux", "Tout l'univers"],
            help="Choisissez quelles entités afficher"
        )
        
        # Filtres
        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            show_communities = st.checkbox("Communautés", value=True)
            show_species = st.checkbox("Espèces", value=True)
        with col_filter2:
            show_locations = st.checkbox("Lieux", value=True)
            show_objects = st.checkbox("Objets", value=False)
        
        st.divider()
        
        # Placeholder pour le graphe
        st.info("🚧 **Fonctionnalité en développement**")
        st.markdown("""
        Le graphe de relations permettra de :
        - Visualiser les connexions entre entités
        - Explorer les réseaux de personnages
        - Identifier les hubs et points clés
        - Détecter les incohérences de relations
        
        **Implémentation prévue** : NetworkX + Plotly pour visualisation interactive
        """)
        
        # Exemple de données de graphe (mockup)
        if st.checkbox("Voir exemple de structure de données"):
            st.code("""
{
  "nodes": [
    {"id": "personnage_1", "label": "Norrik", "type": "personnage"},
    {"id": "lieu_1", "label": "Bibliothèque des Murmures", "type": "lieu"},
    {"id": "communaute_1", "label": "Les Cartographes", "type": "communaute"}
  ],
  "edges": [
    {"source": "personnage_1", "target": "lieu_1", "type": "vit_a"},
    {"source": "personnage_1", "target": "communaute_1", "type": "membre_de"}
  ]
}
            """, language="json")
    
    # TAB 4: À propos
    with tab4:
        st.header("À propos")
        
        st.markdown("""
        ### 🎯 Système Multi-Agents GDD Alteir
        
        **Architecture:**
        - 4 agents génériques (Writer, Reviewer, Corrector, Validator)
        - Configuration par domaine (Personnages, Lieux, etc.)
        - LangGraph pour orchestration
        - GPT-5-nano pour génération
        
        **Workflow:**
        1. **Writer** → Génère le contenu initial
        2. **Reviewer** → Analyse la cohérence narrative
        3. **Corrector** → Corrige la forme
        4. **Validator** → Validation finale
        
        **Principes Narratifs (Personnages):**
        - Orthogonalité rôle ↔ profondeur
        - Structure Surface / Profondeur / Monde
        - Temporalité IS / WAS / COULD-HAVE-BEEN
        - Show > Tell
        - Relations concrètes (prix, dette, délai, tabou)
        
        **Outputs:**
        - JSON complet avec métadonnées
        - Markdown formaté pour lecture
        - Scores de qualité (cohérence, complétude, qualité)
        """)

def create_llm(model_name: str, model_config: dict, creativity: float = None, reasoning_effort: str = None, max_tokens: int = None):
    """Crée une instance LLM selon le modèle choisi"""
    from langchain_openai import ChatOpenAI
    
    # Configuration de base
    llm_config = {
        "model": model_config["name"],
        "max_tokens": max_tokens or model_config["max_tokens"],
    }
    
    # Configuration selon le type de modèle
    if model_config.get("uses_reasoning"):
        # GPT-5 : utilise reasoning au lieu de temperature
        llm_config["use_responses_api"] = True
        llm_config["reasoning"] = {
            "effort": reasoning_effort or model_config.get("default_reasoning", "minimal")
        }
    else:
        # GPT-4 : utilise temperature classique
        llm_config["temperature"] = creativity
    
    return ChatOpenAI(**llm_config)

def generate_content(brief, intent, level, dialogue_mode, creativity, reasoning_effort, max_tokens, model_name, model_config, domain):
    """Génère du contenu (personnage ou lieu) selon le domaine"""
    
    # Lazy load des dépendances lourdes selon le domaine
    ContentWorkflow, WriterConfig, domain_config = load_workflow_dependencies(domain.lower())
    
    # Créer le LLM selon le modèle choisi
    llm = create_llm(model_name, model_config, creativity=creativity, reasoning_effort=reasoning_effort, max_tokens=max_tokens)
    
    # Configuration
    writer_config = WriterConfig(
        intent=intent,
        level=level,
        dialogue_mode=dialogue_mode,
        creativity=creativity
    )
    
    # Workflow avec le LLM choisi
    workflow = ContentWorkflow(domain_config, llm=llm)
    
    # Progress bar détaillée avec étapes
    progress_container = st.container()
    
    with progress_container:
        # Créer les colonnes pour les étapes
        cols = st.columns(4)
        steps = [
            {"name": "Writer", "icon": "✍️", "desc": "Génération"},
            {"name": "Reviewer", "icon": "🔍", "desc": "Analyse"},
            {"name": "Corrector", "icon": "✏️", "desc": "Correction"},
            {"name": "Validator", "icon": "✅", "desc": "Validation"}
        ]
        
        # Initialiser les placeholders pour chaque étape
        step_placeholders = []
        for i, (col, step) in enumerate(zip(cols, steps)):
            with col:
                placeholder = st.empty()
                step_placeholders.append(placeholder)
                placeholder.markdown(f"""
                <div style='text-align: center; padding: 10px; border-radius: 5px; background-color: #1E1E1E;'>
                    <div style='font-size: 24px;'>{step['icon']}</div>
                    <div style='font-size: 12px; color: #888;'>{step['name']}</div>
                    <div style='font-size: 10px; color: #666;'>{step['desc']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        time_estimate = st.empty()
        time_estimate.text("⏱️ Temps estimé : 30-45 secondes")
    
    try:
        import time
        start_time = time.time()
        
        # Étape 1: Writer
        step_placeholders[0].markdown(f"""
        <div style='text-align: center; padding: 10px; border-radius: 5px; background-color: #667eea; color: white;'>
            <div style='font-size: 24px;'>✍️</div>
            <div style='font-size: 12px; font-weight: bold;'>Writer</div>
            <div style='font-size: 10px;'>En cours...</div>
        </div>
        """, unsafe_allow_html=True)
        status_text.text("✍️ Writer : Génération du contenu initial...")
        progress_bar.progress(10)
        
        # Simuler l'avancement pendant l'exécution
        result = workflow.run(brief, writer_config)
        
        # Étape 1 terminée
        step_placeholders[0].markdown(f"""
        <div style='text-align: center; padding: 10px; border-radius: 5px; background-color: #28a745; color: white;'>
            <div style='font-size: 24px;'>✅</div>
            <div style='font-size: 12px; font-weight: bold;'>Writer</div>
            <div style='font-size: 10px;'>Terminé</div>
        </div>
        """, unsafe_allow_html=True)
        progress_bar.progress(25)
        
        # Étape 2: Reviewer
        step_placeholders[1].markdown(f"""
        <div style='text-align: center; padding: 10px; border-radius: 5px; background-color: #667eea; color: white;'>
            <div style='font-size: 24px;'>🔍</div>
            <div style='font-size: 12px; font-weight: bold;'>Reviewer</div>
            <div style='font-size: 10px;'>En cours...</div>
        </div>
        """, unsafe_allow_html=True)
        status_text.text("🔍 Reviewer : Analyse de cohérence narrative...")
        progress_bar.progress(50)
        
        # Étape 2 terminée
        step_placeholders[1].markdown(f"""
        <div style='text-align: center; padding: 10px; border-radius: 5px; background-color: #28a745; color: white;'>
            <div style='font-size: 24px;'>✅</div>
            <div style='font-size: 12px; font-weight: bold;'>Reviewer</div>
            <div style='font-size: 10px;'>Terminé</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Étape 3: Corrector
        step_placeholders[2].markdown(f"""
        <div style='text-align: center; padding: 10px; border-radius: 5px; background-color: #667eea; color: white;'>
            <div style='font-size: 24px;'>✏️</div>
            <div style='font-size: 12px; font-weight: bold;'>Corrector</div>
            <div style='font-size: 10px;'>En cours...</div>
        </div>
        """, unsafe_allow_html=True)
        status_text.text("✏️ Corrector : Correction linguistique...")
        progress_bar.progress(75)
        
        # Étape 3 terminée
        step_placeholders[2].markdown(f"""
        <div style='text-align: center; padding: 10px; border-radius: 5px; background-color: #28a745; color: white;'>
            <div style='font-size: 24px;'>✅</div>
            <div style='font-size: 12px; font-weight: bold;'>Corrector</div>
            <div style='font-size: 10px;'>Terminé</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Étape 4: Validator
        step_placeholders[3].markdown(f"""
        <div style='text-align: center; padding: 10px; border-radius: 5px; background-color: #667eea; color: white;'>
            <div style='font-size: 24px;'>✅</div>
            <div style='font-size: 12px; font-weight: bold;'>Validator</div>
            <div style='font-size: 10px;'>En cours...</div>
        </div>
        """, unsafe_allow_html=True)
        status_text.text("✅ Validator : Validation finale...")
        progress_bar.progress(90)
        
        # Étape 4 terminée
        step_placeholders[3].markdown(f"""
        <div style='text-align: center; padding: 10px; border-radius: 5px; background-color: #28a745; color: white;'>
            <div style='font-size: 24px;'>✅</div>
            <div style='font-size: 12px; font-weight: bold;'>Validator</div>
            <div style='font-size: 10px;'>Terminé</div>
        </div>
        """, unsafe_allow_html=True)
        
        elapsed_time = time.time() - start_time
        status_text.text(f"✅ Terminé en {elapsed_time:.1f}s !")
        progress_bar.progress(100)
        time_estimate.text("")
        
        # Ajouter les métadonnées du modèle au résultat
        result['model_used'] = model_name
        result['model_config'] = model_config
        
        # Sauvegarder
        json_file, md_file = workflow.save_results(result)
        
        # Afficher résultats
        success_msg = {
            "personnages": f"✅ Personnage généré avec succès ! (Modèle: {model_config['icon']} {model_name})",
            "lieux": f"✅ Lieu généré avec succès ! (Modèle: {model_config['icon']} {model_name})"
        }
        st.success(success_msg[domain.lower()])
        
        # Métriques
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Cohérence",
                f"{result['coherence_score']:.2f}",
                delta="Bon" if result['coherence_score'] >= 0.7 else "À améliorer"
            )
        
        with col2:
            st.metric(
                "Complétude",
                f"{result['completeness_score']:.2f}",
                delta="Complet" if result['completeness_score'] >= 0.8 else "Incomplet"
            )
        
        with col3:
            st.metric(
                "Qualité",
                f"{result['quality_score']:.2f}",
                delta="Bon" if result['quality_score'] >= 0.7 else "À améliorer"
            )
        
        # Statut
        if result['ready_for_publication']:
            st.markdown('<div class="success-box">✅ <b>Prêt pour publication</b></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="warning-box">⚠️ <b>Nécessite révision</b></div>', unsafe_allow_html=True)
        
        # Contenu
        with st.expander("📄 Voir le contenu généré", expanded=True):
            st.markdown(result['content'])
        
        # Problèmes
        if result['review_issues']:
            with st.expander(f"⚠️ Problèmes identifiés ({len(result['review_issues'])})"):
                for issue in result['review_issues']:
                    severity = issue['severity']
                    if severity == 'critical':
                        severity_icon = "🔴"
                        box_color = "#f8d7da"
                        border_color = "#dc3545"
                    elif severity == 'major':
                        severity_icon = "🟠"
                        box_color = "#fff3cd"
                        border_color = "#ffc107"
                    else:
                        severity_icon = "🟡"
                        box_color = "#d1ecf1"
                        border_color = "#17a2b8"
                    
                    st.markdown(f"""
                    <div style="background-color: {box_color}; border-left: 4px solid {border_color}; padding: 1rem; margin: 0.5rem 0; border-radius: 0.3rem;">
                        {severity_icon} <b>{issue.get('category', 'General').capitalize()}</b><br>
                        {issue['description']}
                        {f"<br><i>💡 Suggestion: {issue['suggestion']}</i>" if issue.get('suggestion') else ""}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Corrections
        if result['corrections']:
            with st.expander(f"✏️ Corrections ({len(result['corrections'])})"):
                for corr in result['corrections']:
                    st.markdown(f"""
                    <div style="background-color: #e7f3ff; border-left: 4px solid #2196F3; padding: 1rem; margin: 0.5rem 0; border-radius: 0.3rem;">
                        <b>{corr['type']}</b>: <code>{corr['original']}</code> → <code>{corr['corrected']}</code>
                        {f"<br><i>{corr['explanation']}</i>" if corr.get('explanation') else ""}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Fichiers et export
        col_files, col_export = st.columns([2, 1])
        
        with col_files:
            st.info(f"""
            **Fichiers sauvegardés:**
            - 📊 JSON: `{json_file.name}`
            - 📝 Markdown: `{md_file.name}`
            """)
        
        with col_export:
            st.write("")
            if st.button("📤 Exporter vers Notion", use_container_width=True, help="Créer une page dans Notion"):
                export_to_notion(result)
                
            if st.button("💾 Télécharger JSON", use_container_width=True):
                with open(json_file, 'r', encoding='utf-8') as f:
                    st.download_button(
                        label="📥 Télécharger",
                        data=f.read(),
                        file_name=json_file.name,
                        mime="application/json"
                    )
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la génération: {e}")

def export_to_notion(result):
    """Exporte le résultat vers Notion avec MCP"""
    try:
        with st.spinner("📤 Export vers Notion en cours..."):
            # Récupérer les métadonnées du personnage
            metadata = result.get('writer_metadata', {})
            
            # Préparer les propriétés pour Notion
            properties = {
                "Nom": metadata.get('nom', 'Sans nom'),
                "Type": metadata.get('type', 'PNJ'),
                "Espèce": metadata.get('espece', ''),
                "Genre": metadata.get('genre', 'Non défini'),
                "État": "Brouillon IA",
            }
            
            # Ajouter les propriétés optionnelles si présentes
            if metadata.get('age'):
                properties['Âge'] = int(metadata.get('age', 0))
            if metadata.get('alias'):
                properties['Alias'] = metadata.get('alias')
            if metadata.get('occupation'):
                properties['Occupation'] = metadata.get('occupation')
            if metadata.get('axe_ideologique'):
                properties['Axe idéologique'] = metadata.get('axe_ideologique')
            if metadata.get('archetype'):
                properties['Archétype littéraire'] = [metadata.get('archetype')]
            if metadata.get('langage'):
                properties['Langage'] = [metadata.get('langage')]
            
            # Log pour debug
            with st.expander("🔍 Debug - Données envoyées", expanded=False):
                st.write("**Propriétés:**")
                st.json(properties)
                st.write("**Contenu (prévisualisation):**")
                st.text(result['content'][:300] + "...")
            
            # Base de données Personnages
            DATABASE_ID = "1886e4d21b4581a29340f77f5f2e5885"  # Personnages
            
            # Appel API REST Notion pour créer la page
            try:
                import requests
                import os
                
                # Préparer les propriétés au format Notion API
                notion_properties = {}
                
                # Title property
                notion_properties["Nom"] = {
                    "title": [{"text": {"content": properties.get("Nom", "Sans nom")}}]
                }
                
                # Select properties
                if properties.get("Type"):
                    notion_properties["Type"] = {"select": {"name": properties["Type"]}}
                if properties.get("Genre"):
                    notion_properties["Genre"] = {"select": {"name": properties["Genre"]}}
                if properties.get("État"):
                    notion_properties["État"] = {"status": {"name": properties["État"]}}
                if properties.get("Axe idéologique"):
                    notion_properties["Axe idéologique"] = {"select": {"name": properties["Axe idéologique"]}}
                
                # Rich text properties
                if properties.get("Espèce"):
                    notion_properties["Espèce"] = {
                        "rich_text": [{"text": {"content": properties["Espèce"]}}]
                    }
                if properties.get("Alias"):
                    notion_properties["Alias"] = {
                        "rich_text": [{"text": {"content": properties["Alias"]}}]
                    }
                if properties.get("Occupation"):
                    notion_properties["Occupation"] = {
                        "rich_text": [{"text": {"content": properties["Occupation"]}}]
                    }
                
                # Number property
                if properties.get("Âge"):
                    notion_properties["Âge"] = {"number": properties["Âge"]}
                
                # Multi-select properties
                if properties.get("Archétype littéraire"):
                    notion_properties["Archétype littéraire"] = {
                        "multi_select": [{"name": arch} for arch in properties["Archétype littéraire"]]
                    }
                if properties.get("Langage"):
                    notion_properties["Langage"] = {
                        "multi_select": [{"name": lang} for lang in properties["Langage"]]
                    }
                
                # Créer la page via API REST
                headers = {
                    "Authorization": f"Bearer {os.getenv('NOTION_TOKEN')}",
                    "Notion-Version": "2022-06-28",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "parent": {"database_id": DATABASE_ID.replace("-", "")},
                    "properties": notion_properties
                }
                
                response = requests.post(
                    "https://api.notion.com/v1/pages",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    st.error(f"Erreur API Notion: {response.status_code}")
                    st.json(response.json())
                    raise Exception(f"API Error: {response.text}")
                
                page_data = response.json()
                page_url = page_data.get('url', '#')
                page_id = page_data.get('id', 'unknown')
                
                st.success(f"""
                ✅ **Personnage exporté vers Notion !**
                
                📄 **Lien de la fiche:** [{properties['Nom']}]({page_url})
                
                Le personnage a été créé dans la base Personnages.
                
                **Informations :**
                - ID de la page : `{page_id}`
                - Base : Personnages
                - État : Brouillon IA
                
                **Prochaines étapes :**
                - Vérifier la page dans Notion
                - Compléter les relations (Communautés, Lieux, etc.)
                - Valider et changer l'état si nécessaire
                """)
                
                st.balloons()  # Animation de célébration
                
            except Exception as mcp_error:
                st.error(f"❌ Erreur MCP lors de la création : {mcp_error}")
                
                # Afficher les détails pour debugging
                with st.expander("🔧 Détails de l'erreur", expanded=True):
                    st.exception(mcp_error)
                    st.write("**Configuration actuelle:**")
                    st.json({
                        "data_source_id": DATA_SOURCE_ID,
                        "properties": properties,
                        "content_length": len(result['content'])
                    })
                
                raise
    
    except Exception as e:
        st.error(f"❌ Erreur lors de l'export : {e}")
        st.exception(e)  # Afficher la stack trace complète

def show_results():
    """Affiche les résultats générés"""
    
    # Utilise le cache pour lister les fichiers
    file_names = list_output_files()
    
    if not file_names:
        st.info("Aucun résultat généré pour le moment.")
        return
    
    st.write(f"**{len(file_names)} résultat(s) généré(s)**")
    
    # Sélecteur
    selected_file = st.selectbox("Sélectionner un résultat", file_names)
    
    if selected_file:
        # Utilise le cache pour charger le fichier
        data = load_result_file(selected_file)
        
        if not data:
            st.error("Erreur lors du chargement du fichier")
            return
        
        # Afficher
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Cohérence", f"{data['coherence_score']:.2f}")
        with col2:
            st.metric("Complétude", f"{data['completeness_score']:.2f}")
        with col3:
            st.metric("Qualité", f"{data['quality_score']:.2f}")
        
        # Modèle utilisé (si disponible)
        if data.get('model_used'):
            model_config = data.get('model_config', {})
            icon = model_config.get('icon', '🤖')
            st.info(f"{icon} **Modèle utilisé :** {data['model_used']}")
        
        # Statut
        if data['ready_for_publication']:
            st.success("✅ Prêt pour publication")
        else:
            st.warning("⚠️ Nécessite révision")
        
        # Actions
        col_export, col_download = st.columns(2)
        
        with col_export:
            if st.button("📤 Exporter vers Notion", use_container_width=True, help="Créer une page dans Notion", key=f"export_{selected_file}"):
                export_to_notion(data)
        
        with col_download:
            # Bouton de téléchargement JSON
            from pathlib import Path
            json_path = Path("outputs") / f"{selected_file}.json"
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    st.download_button(
                        label="💾 Télécharger JSON",
                        data=f.read(),
                        file_name=f"{selected_file}.json",
                        mime="application/json",
                        use_container_width=True
                    )
        
        st.divider()
        
        # Contenu
        with st.expander("📄 Contenu", expanded=True):
            st.markdown(data['content'])
        
        # Problèmes et corrections
        if data.get('review_issues'):
            with st.expander(f"⚠️ Problèmes identifiés ({len(data['review_issues'])})"):
                for issue in data['review_issues']:
                    severity = issue.get('severity', 'minor')
                    if severity == 'critical':
                        severity_icon = "🔴"
                        box_color = "#f8d7da"
                        border_color = "#dc3545"
                    elif severity == 'major':
                        severity_icon = "🟠"
                        box_color = "#fff3cd"
                        border_color = "#ffc107"
                    else:
                        severity_icon = "🟡"
                        box_color = "#d1ecf1"
                        border_color = "#17a2b8"
                    
                    st.markdown(f"""
                    <div style="background-color: {box_color}; border-left: 4px solid {border_color}; padding: 1rem; margin: 0.5rem 0; border-radius: 0.3rem;">
                        {severity_icon} <b>{issue.get('category', 'General').capitalize()}</b><br>
                        {issue.get('description', 'N/A')}
                        {f"<br><i>💡 Suggestion: {issue['suggestion']}</i>" if issue.get('suggestion') else ""}
                    </div>
                    """, unsafe_allow_html=True)
        
        if data.get('corrections'):
            with st.expander(f"✏️ Corrections ({len(data['corrections'])})"):
                for corr in data['corrections']:
                    st.markdown(f"""
                    <div style="background-color: #e7f3ff; border-left: 4px solid #2196F3; padding: 1rem; margin: 0.5rem 0; border-radius: 0.3rem;">
                        <b>{corr.get('type', 'N/A')}</b>: <code>{corr.get('original', '')}</code> → <code>{corr.get('corrected', '')}</code>
                        {f"<br><i>{corr['explanation']}</i>" if corr.get('explanation') else ""}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Métadonnées
        with st.expander("📊 Métadonnées"):
            st.json(data['writer_metadata'])

if __name__ == "__main__":
    main()

