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
    
    def get_system_prompt(self) -> str:
        """Récupère le prompt système depuis la configuration du domaine"""
        return f"""Tu es un générateur de personnages expert pour le GDD Alteir, un RPG narratif exploratoire.

{self.domain_config.get_role_instructions("writer")}

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
            max_tokens=8000,  # Augmenté pour le template narratif complet
        )
        
        # Charger la configuration du domaine personnages
        from config.domain_configs.personnages_config import PERSONNAGES_CONFIG
        self.domain_config = PERSONNAGES_CONFIG
        
        # Template narratif et schéma des colonnes
        self.narrative_template = self.domain_config.template
        self.character_schema = self.domain_config.schema or {}
        
        # Options disponibles pour les champs select/multi_select (depuis la config)
        from config.domain_configs.personnages_config import PERSONNAGES_FIELD_OPTIONS
        self.field_options = PERSONNAGES_FIELD_OPTIONS
    
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

**TEMPLATE NARRATIF OBLIGATOIRE (basé sur la page Notion PNJ important V2):**

{self.narrative_template}

**CHAMPS NOTION (métadonnées à remplir exactement):**
- **Nom**: [Nom du personnage]
- **Alias**: [Alias/surnom]
- **Type**: [Choisir parmi: {', '.join(self.field_options['Type'])}]
- **Occupation**: [Profession/activité]
- **Espèce**: [Choisir parmi les espèces disponibles dans le contexte]
- **Âge**: [Nombre en cycles]
- **Genre**: [Choisir parmi: {', '.join(self.field_options['Genre'])}]
- **Archétype littéraire**: [Choisir 1-2 parmi: {', '.join(self.field_options['Archétype littéraire'])}]
- **Axe idéologique**: [Choisir parmi: {', '.join(self.field_options['Axe idéologique'])}]
- **Qualités**: [Choisir 2-4 parmi: {', '.join(self.field_options['Qualités'][:10])}...]
- **Défauts**: [Choisir 2-4 parmi: {', '.join(self.field_options['Défauts'][:10])}...]
- **Langage**: [Choisir 1-2 parmi: {', '.join(self.field_options['Langage'])}]
- **Communautés**: [Référencer les communautés du contexte]
- **Lieux de vie**: [Référencer les lieux du contexte]
- **Réponse au problème moral**: [Réponse personnelle du personnage]
- **État**: "Brouillon IA"
- **Sprint**: [Choisir parmi: {', '.join(self.field_options['Sprint'])}]

**INSTRUCTIONS SPÉCIFIQUES:**
- Respecter EXACTEMENT la structure du template narratif ci-dessus
- Remplir chaque section avec du contenu cohérent et détaillé
- Les dialogues doivent être {specs['dialogues']} variées (mode: {self.config.dialogue_mode})
- Les relations doivent avoir un ENJEU CONCRET (prix, dette, délai, tabou)
- Appliquer les principes narratifs (orthogonalité, show>tell, blancs actifs)

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
            {"role": "system", "content": self.get_system_prompt()},
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
        
        Extrait les champs Notion du texte généré par le LLM
        """
        import re
        
        parsed = self.character_schema.copy()
        parsed["_raw_text"] = text
        parsed["État"] = "Brouillon IA"
        
        # Patterns pour extraire les champs Notion
        patterns = {
            "Nom": r"\*\*Nom\*\*:\s*(.+)",
            "Alias": r"\*\*Alias\*\*:\s*(.+)",
            "Type": r"\*\*Type\*\*:\s*(.+)",
            "Occupation": r"\*\*Occupation\*\*:\s*(.+)",
            "Espèce": r"\*\*Espèce\*\*:\s*(.+)",
            "Âge": r"\*\*Âge\*\*:\s*(\d+)",
            "Genre": r"\*\*Genre\*\*:\s*(.+)",
            "Archétype littéraire": r"\*\*Archétype littéraire\*\*:\s*(.+)",
            "Axe idéologique": r"\*\*Axe idéologique\*\*:\s*(.+)",
            "Qualités": r"\*\*Qualités\*\*:\s*(.+)",
            "Défauts": r"\*\*Défauts\*\*:\s*(.+)",
            "Langage": r"\*\*Langage\*\*:\s*(.+)",
            "Communautés": r"\*\*Communautés\*\*:\s*(.+)",
            "Lieux de vie": r"\*\*Lieux de vie\*\*:\s*(.+)",
            "Réponse au problème moral": r"\*\*Réponse au problème moral\*\*:\s*(.+)",
            "Sprint": r"\*\*Sprint\*\*:\s*(.+)"
        }
        
        # Extraire les champs avec regex
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                
                # Traitement spécial selon le type de champ
                if field in ["Archétype littéraire", "Qualités", "Défauts", "Langage"]:
                    # Multi-select: séparer par virgule et nettoyer
                    parsed[field] = [item.strip() for item in value.split(",") if item.strip()]
                elif field == "Âge":
                    # Number: convertir en entier
                    try:
                        parsed[field] = int(value)
                    except ValueError:
                        parsed[field] = 0
                else:
                    # Text/Select: garder tel quel
                    parsed[field] = value
        
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

