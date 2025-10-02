#!/usr/bin/env python3
"""
Agent d'écriture de personnages pour le GDD Alteir
Basé sur les instructions du Générateur de Personnages (Notion)
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass
from langchain_openai import ChatOpenAI

# Ajouter le répertoire racine au path
sys.path.append(str(Path(__file__).parent.parent))

from config.notion_config import NotionConfig

@dataclass
class CharacterWriterConfig:
    """Configuration pour l'agent d'écriture de personnages"""
    intent: Literal["orthogonal_depth", "vocation_pure", "archetype_assume", "mystere_non_resolu"] = "orthogonal_depth"
    level: Literal["cameo", "standard", "major"] = "standard"
    dialogue_mode: Literal["parle", "gestuel", "telepathique", "ecrit_only"] = "parle"
    calendar_spec: str = "cycles"  # cycles, fragments, ères
    inspiration_mode: Literal["off", "lite", "full"] = "lite"
    figures_pref: List[str] = None
    
    def __post_init__(self):
        if self.figures_pref is None:
            self.figures_pref = ["métaphore", "oxymore", "synesthésie"]

class CharacterWriterAgent:
    """
    Agent d'écriture de personnages pour le GDD Alteir
    
    Principes:
    - Orthogonalité rôle ↔ profondeur
    - Surface / Profondeur / Monde
    - Temporalité IS / WAS / COULD-HAVE-BEEN
    - Show > Tell
    - Blancs actifs
    """
    
    SYSTEM_PROMPT = """Tu es un générateur de personnages expert pour le GDD Alteir, un RPG narratif exploratoire.

**PRINCIPES FONDAMENTAUX:**

1. **Orthogonalité rôle ↔ profondeur**: La profondeur du personnage ne doit PAS être explicable par son rôle visible seul (sauf indication contraire).

2. **Surface / Profondeur / Monde**:
   - Surface = gestes, objets, micro-règles, répliques brèves SANS backstory
   - Profondeur = indices, artefacts, témoins, lieux, analepses par strates
   - Monde = contraintes institutionnelles/écologiques/économiques

3. **Temporalité IS / WAS / COULD-HAVE-BEEN**: Montrer le présent, un passé concret, ET une voie non empruntée.

4. **Show > Tell**: Privilégier objets, rituels, silences, traces. Réserver l'exposition directe aux rubriques qui l'exigent.

5. **Blancs actifs**: Toute zone d'ombre ouvre une ACTION (parler à X, aller à Y, utiliser Z). Éviter le "mystère inerte".

**LANGUE & STYLE:**
- Français clair, précis, sans méta
- Prose continue (pas de tableaux "avant/après")
- Néologismes autorisés avec glose brève (5-8 mots) à la première mention si nécessaire
- Éviter les anglicismes non nécessaires
- Décrire violences/immoralités sans euphémiser, de façon crue mais non esthétisante

**ANTI-CLICHÉS:**
Éviter l'archétype omniprésent, l'exposition torrentielle, la "voix off" méta. Le rôle fonctionnel reste FAÇADE.

**RECHERCHE & AUTONOMIE:**
Pour chaque nom propre inventé ou terme capitalisé:
1. Tenter de le résoudre à partir des données Notion disponibles
2. Si manquant, proposer une hypothèse minimale cohérente marquée par ◊
3. Ajouter "voir aussi" intégrés vers entrées liées

Tu es extrêmement pro-actif pour t'approprier les concepts, lieux et personnages de l'univers via recherches Notion/MCP."""
    
    def __init__(self, config: CharacterWriterConfig = None, llm: ChatOpenAI = None):
        """Initialise l'agent d'écriture de personnages"""
        self.config = config or CharacterWriterConfig()
        self.notion_config = NotionConfig()
        
        # LLM avec paramètres optimisés pour l'écriture créative
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",  # Modèle accessible et performant
            temperature=0.7,  # Créativité modérée
            max_tokens=2000,  # Plus long pour les fiches complètes
        )
        
        # Template Notion pour personnages (basé sur la structure récupérée)
        self.character_template = {
            "Nom": "",
            "Alias": "",
            "Type": "",  # PJ, PNJ, PNJ principal, etc.
            "Occupation": "",
            "Espèce": "",
            "Âge": 0,
            "Genre": "",
            "Archétype littéraire": [],
            "Axe idéologique": "",
            "Qualités": [],
            "Défauts": [],
            "Langage": [],
            "Communautés": [],
            "Lieux de vie": [],
            "Réponse au problème moral": "",
            "État": "Brouillon IA"
        }
    
    def _build_character_prompt(self, brief: str, context_data: Dict[str, Any]) -> str:
        """
        Construit le prompt pour générer un personnage
        
        Args:
            brief: Description courte du personnage à créer
            context_data: Données de contexte depuis Notion (lieux, espèces, etc.)
        """
        # Adapter selon le niveau
        level_specs = {
            "cameo": {
                "dialogues": "4-6 répliques (10-20 mots)",
                "relations": "0-1 relation",
                "artefacts": "0-1 artefact"
            },
            "standard": {
                "dialogues": "8-10 répliques (10-20 mots)",
                "relations": "1-3 relations avec enjeu concret",
                "artefacts": "1-2 artefacts"
            },
            "major": {
                "dialogues": "10-12 répliques (10-20 mots)",
                "relations": "2-4 relations avec enjeu concret",
                "artefacts": "2-3 artefacts"
            }
        }
        
        specs = level_specs[self.config.level]
        
        # Adapter selon l'intention
        intent_instructions = {
            "orthogonal_depth": "La profondeur doit être NON ALIGNÉE au rôle visible. Le personnage cache quelque chose d'inattendu.",
            "vocation_pure": "La profondeur PEUT s'aligner au rôle. Le personnage est ce qu'il paraît, mais avec nuances.",
            "archetype_assume": "MONOMOTEUR VOLONTAIRE. Le personnage assume pleinement son archétype (toujours en show>tell).",
            "mystere_non_resolu": "[Profondeur] ELLIPTIQUE. Donner des indices sans synthèse explicative."
        }
        
        # Adapter le dialogue selon le mode
        dialogue_instructions = {
            "parle": "Répliques parlées variées, jouables, sans backstory.",
            "gestuel": "Décrire gestes/signaux/rites au lieu de paroles.",
            "telepathique": "Pensées transmises, sensations partagées, images mentales.",
            "ecrit_only": "Billets, ardoises, inscriptions. Pas de parole orale."
        }
        
        prompt = f"""**BRIEF:** {brief}

**CONFIGURATION:**
- Intention: {self.config.intent} — {intent_instructions[self.config.intent]}
- Niveau: {self.config.level}
- Mode dialogue: {self.config.dialogue_mode} — {dialogue_instructions[self.config.dialogue_mode]}
- Système calendaire: {self.config.calendar_spec}

**SPÉCIFICATIONS ({self.config.level.upper()}):**
- Dialogues: {specs['dialogues']}
- Relations: {specs['relations']}
- Artefacts/Indices: {specs['artefacts']}

**CONTEXTE NOTION (univers Alteir):**
{self._format_context(context_data)}

**STRUCTURE OBLIGATOIRE (template Notion):**

## Caractérisation
**[Surface]**: Traits visibles concrets, gestes/tics, objets portés. Pas de backstory.

**[Profondeur]**: 2 noyaux latents formulés sans pathos + comment ils se découvrent (artefact/témoin/lieu).

## Dialogue
{specs['dialogues']} variées. Mode: {self.config.dialogue_mode}.

[Exemples de répliques ici, selon le mode]

## Background / Histoire
Paragraphe compact (80-120 mots), neutre. Les détails sensibles vont en [Profondeur].

## Relations
{specs['relations']}. Chaque relation doit avoir un ENJEU CONCRET (prix, dette, délai, tabou).

## Arcs / Quêtes
- Au moins une micro-quête principale
- Une alternative "low combat"
- CONSÉQUENCE D'ÉCHEC
- ÉTAT PERSISTANT si retour

## Chronologie
Mini-table âge/événement/date (système: {self.config.calendar_spec})

## Indices profonds
Au moins 1 artefact OU 1 témoin vivant OU 1 lieu actif (pas d'obligation cumulée).

**CONTRÔLE QUALITÉ:**
✓ Aucune fuite de backstory en [Surface]
✓ Chaque info profonde montrée par artefact/témoin/lieu
✓ Orthogonalité respectée (selon intention)
✓ Chronologie cohérente
✓ Blancs actifs (chaque mystère ouvre une action)

Produis la fiche DIRECTEMENT dans cette structure, sans apartés méthodologiques."""
        
        return prompt
    
    def _format_context(self, context_data: Dict[str, Any]) -> str:
        """Formate les données de contexte Notion"""
        parts = []
        
        if context_data.get("especes"):
            parts.append("**Espèces disponibles:** " + ", ".join(context_data["especes"][:5]))
        
        if context_data.get("lieux"):
            parts.append("**Lieux majeurs:** " + ", ".join([l.get("name", "") for l in context_data["lieux"][:5]]))
        
        if context_data.get("communautes"):
            parts.append("**Communautés:** " + ", ".join(context_data["communautes"][:5]))
        
        if context_data.get("archetypes"):
            parts.append("**Archétypes littéraires:** " + ", ".join(context_data["archetypes"][:8]))
        
        if context_data.get("axes_ideologiques"):
            parts.append("**Axes idéologiques:** " + ", ".join(context_data["axes_ideologiques"]))
        
        return "\n".join(parts) if parts else "Contexte en cours de chargement depuis Notion..."
    
    def gather_context_from_notion(self) -> Dict[str, Any]:
        """
        Récupère le contexte depuis Notion pour informer la génération
        
        Note: Dans une vraie implémentation, utiliser les outils MCP
        pour fetch les données depuis les bases Notion
        """
        # Simulation basée sur les données récupérées précédemment
        context = {
            "especes": [
                "Humain modifié", "Croc d'Améthyste", "Gedroth", 
                "Entité vertébrale", "Créature abyssale"
            ],
            "lieux": [
                {"name": "Le Léviathan Pétrifié", "type": "Lieu majeur"},
                {"name": "La Vieille", "type": "Cité"},
                {"name": "Les Vertèbres du Monde", "type": "Structure cosmique"}
            ],
            "communautes": [
                "Les Cartographes", "La Guilde des Enlumineurs", 
                "Les Flagellants", "Gardiens du Périmètre"
            ],
            "archetypes": [
                "Artiste / Cynique", "Amoureuse / Faire-valoir",
                "Magicienne / Sorcier", "Rebelle / Destructeur",
                "Guerrière / Surhomme", "Friponne / Menteur",
                "Mentor / Gourou", "Reine / Tyran"
            ],
            "axes_ideologiques": [
                "Retrait", "Destruction", "Rébellion",
                "Connexion", "Subversion", "Contrôle"
            ],
            "langages": [
                "Abraldique ancien", "Principit", "Kesh-Varash",
                "Néo-Frémissant", "Langage vertébral", "Mécanaqueux"
            ]
        }
        
        return context
    
    def generate_character(self, brief: str, context_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Génère un personnage complet
        
        Args:
            brief: Description courte du personnage à créer
            context_data: Contexte Notion optionnel (récupéré automatiquement si None)
            
        Returns:
            Fiche de personnage complète
        """
        # Récupérer le contexte si non fourni
        if context_data is None:
            context_data = self.gather_context_from_notion()
        
        # Construire le prompt
        user_prompt = self._build_character_prompt(brief, context_data)
        
        # Générer avec le LLM
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.llm.invoke(messages)
        
        # Normaliser le contenu (même fonction que dans agents_demo.py)
        character_text = self._to_text(response.content if hasattr(response, 'content') else response)
        
        # Parser le résultat en structure Notion
        character_data = self._parse_character_text(character_text)
        
        return {
            "text": character_text,
            "structured": character_data,
            "config": {
                "intent": self.config.intent,
                "level": self.config.level,
                "dialogue_mode": self.config.dialogue_mode
            }
        }
    
    def _to_text(self, content: Any) -> str:
        """
        Normalise le contenu renvoyé par LangChain/Responses en texte
        """
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for p in content:
                if isinstance(p, dict):
                    if "text" in p and isinstance(p["text"], str):
                        parts.append(p["text"])
                    elif "type" in p and p["type"] == "output_text" and "content" in p:
                        parts.append(str(p["content"]))
                    else:
                        parts.append(str(p))
                else:
                    txt = getattr(p, "text", None)
                    parts.append(txt if isinstance(txt, str) else str(p))
            return "".join(parts).strip()
        return str(content)
    
    def _parse_character_text(self, text: str) -> Dict[str, Any]:
        """
        Parse le texte généré en structure Notion
        
        Note: Implémentation simplifiée, à améliorer avec regex/parsing robuste
        """
        # TODO: Implémenter un vrai parser pour extraire les champs Notion
        # Pour l'instant, retourner le template avec le texte brut
        parsed = self.character_template.copy()
        parsed["_raw_text"] = text
        parsed["État"] = "Brouillon IA"
        
        return parsed

def main():
    """Test de l'agent d'écriture de personnages"""
    print("=== Test Agent d'Écriture de Personnages ===\n")
    
    # Configuration de test
    config = CharacterWriterConfig(
        intent="orthogonal_depth",
        level="standard",
        dialogue_mode="parle"
    )
    
    # Créer l'agent
    agent = CharacterWriterAgent(config)
    
    # Brief de test
    brief = """Un cartographe solitaire qui trace les Vertèbres du Monde, 
    mais cache une autre vocation. Genre: Féminin. Espèce: Humain modifié. 
    Âge approximatif: 40 cycles."""
    
    print(f"Brief: {brief}\n")
    print("Génération du personnage...\n")
    
    # Générer le personnage
    result = agent.generate_character(brief)
    
    print("=" * 60)
    print("FICHE GÉNÉRÉE:")
    print("=" * 60)
    print(result["text"])
    print("\n" + "=" * 60)
    print(f"\nConfiguration: {result['config']}")

if __name__ == "__main__":
    main()

