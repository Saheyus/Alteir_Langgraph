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

from workflows.content_workflow import ContentWorkflow
from agents.writer_agent import WriterConfig
from config.domain_configs.personnages_config import PERSONNAGES_CONFIG

# Configuration de la page
st.set_page_config(
    page_title="GDD Alteir - Multi-Agents",
    page_icon="🤖",
    layout="wide"
)

# Style CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    text-align: center;
    color: #1f77b4;
    margin-bottom: 2rem;
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
    
    # En-tête
    st.markdown('<p class="main-header">🤖 Système Multi-Agents GDD Alteir</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        st.subheader("Modèle LLM")
        st.info("**GPT-5-nano** (OpenAI)")
        
        st.subheader("Domaine")
        domain = st.selectbox("Domaine", ["Personnages"], index=0)
        
        st.subheader("📊 Statistiques")
        outputs_dir = Path("outputs")
        if outputs_dir.exists():
            nb_files = len(list(outputs_dir.glob("*.json")))
            st.metric("Générations", nb_files)
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["✨ Créer", "📂 Résultats", "ℹ️ À propos"])
    
    # TAB 1: Création
    with tab1:
        st.header("Créer un Personnage")
        
        # Brief
        brief = st.text_area(
            "Description du personnage",
            placeholder="Ex: Un alchimiste qui transforme les émotions en substances physiques. Genre: Non défini. Espèce: Humain modifié. Âge: 38 cycles.",
            height=100
        )
        
        # Initialiser session state pour les paramètres
        import random
        if 'random_seed' not in st.session_state:
            st.session_state.random_seed = 0
        
        # Options disponibles
        intent_options = ["orthogonal_depth", "vocation_pure", "archetype_assume", "mystere_non_resolu"]
        level_options = ["cameo", "standard", "major"]
        dialogue_options = ["parle", "gestuel", "telepathique", "ecrit_only"]
        
        # Initialiser les valeurs par défaut si elles n'existent pas
        if 'intent' not in st.session_state:
            st.session_state.intent = "orthogonal_depth"
        if 'level' not in st.session_state:
            st.session_state.level = "standard"
        if 'dialogue_mode' not in st.session_state:
            st.session_state.dialogue_mode = "parle"
        if 'creativity' not in st.session_state:
            st.session_state.creativity = 0.7
        
        # Fonction helper pour choisir une valeur différente
        def random_different(options, current):
            """Choisit une valeur aléatoire différente de la valeur actuelle"""
            if len(options) <= 1:
                return options[0] if options else current
            available = [opt for opt in options if opt != current]
            return random.choice(available)
        
        # Bouton dé global
        col_dice, col_space = st.columns([1, 5])
        with col_dice:
            if st.button("🎲", help="Mélanger tous les paramètres", use_container_width=True):
                st.session_state.intent = random_different(intent_options, st.session_state.intent)
                st.session_state.level = random_different(level_options, st.session_state.level)
                st.session_state.dialogue_mode = random_different(dialogue_options, st.session_state.dialogue_mode)
                # Pour la créativité, s'assurer d'une différence d'au moins 0.1
                while True:
                    new_creativity = round(random.uniform(0.5, 0.9), 2)
                    if abs(new_creativity - st.session_state.creativity) >= 0.1:
                        st.session_state.creativity = new_creativity
                        break
                st.session_state.random_seed += 1
                st.rerun()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Paramètres Narratifs")
            
            # Intention narrative
            col_intent, col_intent_random = st.columns([4, 1])
            with col_intent_random:
                st.write("")  # Spacer
                st.write("")  # Spacer
                if st.button("🎲", key="random_intent", help="Valeur aléatoire"):
                    st.session_state.intent = random_different(intent_options, st.session_state.intent)
                    st.session_state.random_seed += 1
                    st.rerun()
            with col_intent:
                intent = st.selectbox(
                    "Intention narrative",
                    intent_options,
                    index=intent_options.index(st.session_state.intent),
                    help="Orthogonal = profondeur ≠ rôle visible",
                    key=f"intent_select_{st.session_state.random_seed}"
                )
            
            # Niveau de détail
            col_level, col_level_random = st.columns([4, 1])
            with col_level_random:
                st.write("")  # Spacer
                st.write("")  # Spacer
                if st.button("🎲", key="random_level", help="Valeur aléatoire"):
                    st.session_state.level = random_different(level_options, st.session_state.level)
                    st.session_state.random_seed += 1
                    st.rerun()
            with col_level:
                level = st.selectbox(
                    "Niveau de détail",
                    level_options,
                    index=level_options.index(st.session_state.level),
                    help="cameo: 4-6 répliques | standard: 8-10 | major: 10-12",
                    key=f"level_select_{st.session_state.random_seed}"
                )
            
            # Mode de dialogue
            col_dialogue, col_dialogue_random = st.columns([4, 1])
            with col_dialogue_random:
                st.write("")  # Spacer
                st.write("")  # Spacer
                if st.button("🎲", key="random_dialogue", help="Valeur aléatoire"):
                    st.session_state.dialogue_mode = random_different(dialogue_options, st.session_state.dialogue_mode)
                    st.session_state.random_seed += 1
                    st.rerun()
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
            
            # Créativité avec bouton random
            col_creativity, col_creativity_random = st.columns([4, 1])
            with col_creativity_random:
                st.write("")  # Spacer
                st.write("")  # Spacer
                st.write("")  # Spacer
                st.write("")  # Spacer
                if st.button("🎲", key="random_creativity", help="Valeur aléatoire"):
                    # S'assurer d'une différence d'au moins 0.1
                    while True:
                        new_creativity = round(random.uniform(0.5, 0.9), 2)
                        if abs(new_creativity - st.session_state.creativity) >= 0.1:
                            st.session_state.creativity = new_creativity
                            break
                    st.session_state.random_seed += 1
                    st.rerun()
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
            
            st.info(f"""
            **Configuration:**
            - Intent: `{intent}`
            - Niveau: `{level}`
            - Dialogue: `{dialogue_mode}`
            - Température: `{creativity}`
            """)
        
        # Mettre à jour session state avec les valeurs choisies manuellement
        st.session_state.intent = intent
        st.session_state.level = level
        st.session_state.dialogue_mode = dialogue_mode
        st.session_state.creativity = creativity
        
        # Bouton de génération
        if st.button("🚀 Générer le Personnage", type="primary", use_container_width=True):
            if not brief:
                st.error("⚠️ Veuillez fournir une description du personnage")
            else:
                generate_character(brief, intent, level, dialogue_mode, creativity)
    
    # TAB 2: Résultats
    with tab2:
        st.header("Résultats Générés")
        
        show_results()
    
    # TAB 3: À propos
    with tab3:
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

def generate_character(brief, intent, level, dialogue_mode, creativity):
    """Génère un personnage"""
    
    with st.spinner("🎨 Génération en cours..."):
        
        # Configuration
        writer_config = WriterConfig(
            intent=intent,
            level=level,
            dialogue_mode=dialogue_mode,
            creativity=creativity
        )
        
        # Workflow
        workflow = ContentWorkflow(PERSONNAGES_CONFIG)
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("🖊️ Writer: Génération du contenu...")
            progress_bar.progress(25)
            
            result = workflow.run(brief, writer_config)
            
            status_text.text("✅ Terminé !")
            progress_bar.progress(100)
            
            # Sauvegarder
            json_file, md_file = workflow.save_results(result)
            
            # Afficher résultats
            st.success("✅ Personnage généré avec succès !")
            
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
                        severity_icon = "🔴" if issue['severity'] == 'critical' else "🟡"
                        st.write(f"{severity_icon} **{issue['description']}**")
            
            # Corrections
            if result['corrections']:
                with st.expander(f"✏️ Corrections ({len(result['corrections'])})"):
                    for corr in result['corrections']:
                        st.write(f"**{corr['type']}**: {corr['original']} → {corr['corrected']}")
            
            # Fichiers
            st.info(f"""
            **Fichiers sauvegardés:**
            - 📊 JSON: `{json_file}`
            - 📝 Markdown: `{md_file}`
            """)
            
        except Exception as e:
            st.error(f"❌ Erreur lors de la génération: {e}")

def show_results():
    """Affiche les résultats générés"""
    
    outputs_dir = Path("outputs")
    
    if not outputs_dir.exists() or not list(outputs_dir.glob("*.json")):
        st.info("Aucun résultat généré pour le moment.")
        return
    
    # Lister les fichiers
    json_files = sorted(
        outputs_dir.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    st.write(f"**{len(json_files)} résultat(s) généré(s)**")
    
    # Sélecteur
    file_names = [f.stem for f in json_files]
    selected_file = st.selectbox("Sélectionner un résultat", file_names)
    
    if selected_file:
        json_path = outputs_dir / f"{selected_file}.json"
        md_path = outputs_dir / f"{selected_file}.md"
        
        # Charger le JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Afficher
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Cohérence", f"{data['coherence_score']:.2f}")
        with col2:
            st.metric("Complétude", f"{data['completeness_score']:.2f}")
        with col3:
            st.metric("Qualité", f"{data['quality_score']:.2f}")
        
        # Statut
        if data['ready_for_publication']:
            st.success("✅ Prêt pour publication")
        else:
            st.warning("⚠️ Nécessite révision")
        
        # Contenu
        with st.expander("📄 Contenu", expanded=True):
            st.markdown(data['content'])
        
        # Métadonnées
        with st.expander("📊 Métadonnées"):
            st.json(data['writer_metadata'])

if __name__ == "__main__":
    main()

