#!/usr/bin/env python3
"""
Agent d'écriture générique configuré par domaine
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass

# Ajouter le répertoire racine au path
sys.path.append(str(Path(__file__).parent.parent))

from agents.base.base_agent import BaseAgent, AgentResult
from agents.base.domain_config import DomainConfig

@dataclass
class WriterConfig:
    """Configuration additionnelle pour l'agent d'écriture"""
    # Paramètres génériques
    creativity: float = 0.7  # Température du LLM
    max_length: int = 2000   # Longueur max de sortie
    
    # Paramètres spécifiques au domaine personnages (optionnels)
    intent: Optional[Literal["orthogonal_depth", "vocation_pure", "archetype_assume", "mystere_non_resolu"]] = None
    level: Optional[Literal["cameo", "standard", "major"]] = None
    dialogue_mode: Optional[Literal["parle", "gestuel", "telepathique", "ecrit_only"]] = None
    calendar_spec: Optional[str] = None
    inspiration_mode: Optional[Literal["off", "lite", "full"]] = None

class WriterAgent(BaseAgent):
    """
    Agent d'écriture générique configuré par domaine
    
    Peut être utilisé pour n'importe quel type de contenu:
    - Personnages
    - Lieux
    - Communautés
    - Espèces
    - Objets
    - Chronologie
    
    La spécialisation se fait via la DomainConfig
    """
    
    BASE_PROMPT = """Tu es un agent d'écriture expert pour le GDD Alteir, un RPG narratif exploratoire.

**PRINCIPES GÉNÉRAUX D'ÉCRITURE:**

1. **Cohérence narrative**: Tous les éléments créés doivent s'intégrer harmonieusement dans l'univers Alteir.

2. **Show > Tell**: Privilégier la démonstration par des détails concrets plutôt que l'exposition directe.

3. **Richesse sans surcharge**: Créer du contenu dense et évocateur, mais lisible et utilisable.

4. **Originalité**: Éviter les clichés, inventer des détails uniques qui enrichissent l'univers.

5. **Recherche & autonomie**: Pour chaque concept, vérifier s'il existe dans le contexte fourni. Si manquant, proposer une hypothèse cohérente marquée par ◊.

**LANGUE & STYLE:**
- Français clair, précis, sans méta
- Prose continue (pas de tableaux comparatifs)
- Néologismes autorisés avec glose brève (5-8 mots) à la première mention
- Éviter les anglicismes non nécessaires
- Décrire sans euphémiser, de façon crue mais non esthétisante

Tu es extrêmement pro-actif pour t'approprier les concepts existants de l'univers."""
    
    def __init__(self, domain_config: DomainConfig, writer_config: WriterConfig = None, llm=None):
        """
        Initialise l'agent d'écriture
        
        Args:
            domain_config: Configuration du domaine (personnages, lieux, etc.)
            writer_config: Configuration additionnelle pour l'écriture
            llm: Modèle LLM optionnel
        """
        super().__init__(domain_config, llm)
        self.writer_config = writer_config or WriterConfig()
        
        # Ajuster la température du LLM selon la config
        if hasattr(self.llm, 'temperature'):
            self.llm.temperature = self.writer_config.creativity
    
    def process(self, brief: str, context: Dict[str, Any] = None) -> AgentResult:
        """
        Génère du contenu basé sur un brief
        
        Args:
            brief: Description du contenu à créer
            context: Contexte Notion optionnel (récupéré auto si None)
            
        Returns:
            AgentResult avec le contenu généré
        """
        # Récupérer le contexte si non fourni
        if context is None:
            context = self.gather_context()
        
        # Construire le prompt
        user_prompt = self._build_prompt(brief, context)
        
        # Générer avec le LLM
        system_prompt = self._build_system_prompt("writer")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = self.llm.invoke(messages)
            content_text = self._to_text(response.content if hasattr(response, 'content') else response)
            
            # Parser si nécessaire (pour l'instant, retourner le texte brut)
            structured = self._parse_content(content_text)
            
            return AgentResult(
                success=True,
                content=content_text,
                metadata={
                    "domain": self.domain,
                    "brief": brief,
                    "structured": structured,
                    "writer_config": vars(self.writer_config)
                }
            )
        except Exception as e:
            return AgentResult(
                success=False,
                content="",
                metadata={"domain": self.domain, "brief": brief},
                errors=[str(e)]
            )
    
    def _build_prompt(self, brief: str, context: Dict[str, Any]) -> str:
        """Construit le prompt utilisateur avec le brief et le contexte"""
        
        # Spécifications selon la config (si domaine personnages)
        spec_section = self._build_spec_section()
        
        # Contexte formaté
        context_section = self._format_context(context)
        
        # Structure du template
        template_section = self._build_template_section()
        
        # Champs Notion (métadonnées)
        notion_fields_section = self._build_notion_fields_section()
        
        prompt = f"""**BRIEF:** {brief}

{spec_section}

**CONTEXTE ({self.domain_config.display_name.upper()}):**
{context_section}

{notion_fields_section}

**STRUCTURE NARRATIVE OBLIGATOIRE:**
{template_section}

Produis le contenu dans cet ordre exact:
1. D'abord les CHAMPS NOTION (métadonnées)
2. Puis le CONTENU NARRATIF complet

Sans apartés méthodologiques."""
        
        return prompt
    
    def _build_spec_section(self) -> str:
        """Construit la section de spécifications (si applicable)"""
        if self.domain != "personnages" or not self.writer_config.intent:
            return ""
        
        intent_desc = {
            "orthogonal_depth": "La profondeur doit être NON ALIGNÉE au rôle visible",
            "vocation_pure": "La profondeur PEUT s'aligner au rôle",
            "archetype_assume": "MONOMOTEUR VOLONTAIRE (show>tell)",
            "mystere_non_resolu": "[Profondeur] ELLIPTIQUE avec indices"
        }
        
        level_specs = {
            "cameo": "4-6 répliques, 0-1 relation, 0-1 artefact",
            "standard": "8-10 répliques, 1-3 relations, 1-2 artefacts",
            "major": "10-12 répliques, 2-4 relations, 2-3 artefacts"
        }
        
        parts = []
        
        if self.writer_config.intent:
            parts.append(f"- Intention: {self.writer_config.intent} — {intent_desc.get(self.writer_config.intent, '')}")
        
        if self.writer_config.level:
            parts.append(f"- Niveau: {self.writer_config.level} — {level_specs.get(self.writer_config.level, '')}")
        
        if self.writer_config.dialogue_mode:
            parts.append(f"- Mode dialogue: {self.writer_config.dialogue_mode}")
        
        if self.writer_config.calendar_spec:
            parts.append(f"- Système calendaire: {self.writer_config.calendar_spec}")
        
        if not parts:
            return ""
        
        return "**SPÉCIFICATIONS:**\n" + "\n".join(parts)
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Formate le contexte en texte lisible"""
        parts = []
        
        if context.get("especes"):
            parts.append("**Espèces disponibles:** " + ", ".join(context["especes"][:5]))
        
        if context.get("lieux"):
            parts.append("**Lieux majeurs:** " + ", ".join(context["lieux"][:5]))
        
        if context.get("communautes"):
            parts.append("**Communautés:** " + ", ".join(context["communautes"][:5]))
        
        return "\n".join(parts) if parts else "Contexte en cours de chargement..."
    
    def _build_template_section(self) -> str:
        """Construit la description de la structure attendue"""
        # Utiliser le template narratif complet s'il existe
        if self.domain_config.template:
            return self.domain_config.template
        
        # Sinon, fallback sur la liste des champs
        fields = self.domain_config.get_template_fields()
        required = self.domain_config.get_required_fields()
        
        return f"""Champs à remplir: {', '.join(fields)}
Champs obligatoires: {', '.join(required)}

Structure la sortie de manière claire et organisée."""
    
    def _build_notion_fields_section(self) -> str:
        """Construit la section des champs Notion (métadonnées de la base de données)"""
        if not self.domain_config.schema:
            return ""
        
        # Récupérer les field_options depuis le domaine config si disponibles
        field_options = {}
        if self.domain == "personnages":
            try:
                from config.domain_configs.personnages_config import PERSONNAGES_FIELD_OPTIONS
                field_options = PERSONNAGES_FIELD_OPTIONS
            except ImportError:
                pass
        
        schema_fields = []
        schema_fields.append("**CHAMPS NOTION (métadonnées de la base de données à remplir en fin de fiche):**\n")
        
        for field_name in self.domain_config.schema.keys():
            # Formatage selon si les options sont disponibles
            if field_name in field_options:
                options = field_options[field_name]
                if len(options) <= 5:
                    options_str = ", ".join(options)
                else:
                    options_str = ", ".join(options[:5]) + f"... ({len(options)} options)"
                schema_fields.append(f"- **{field_name}**: [Choisir parmi: {options_str}]")
            elif field_name in ["Communautés", "Lieux de vie", "Détient"]:
                schema_fields.append(f"- **{field_name}**: [Référencer depuis le contexte]")
            elif field_name in ["Âge"]:
                schema_fields.append(f"- **{field_name}**: [Nombre en cycles]")
            elif field_name == "Nom":
                schema_fields.append(f"- **{field_name}**: [Nom du personnage]")
            else:
                schema_fields.append(f"- **{field_name}**: [Texte libre]")
        
        # Toujours mettre État à "Brouillon IA"
        schema_fields.append("\n- **État**: \"Brouillon IA\" (obligatoire)")
        
        return "\n".join(schema_fields)
    
    def _parse_content(self, content_text: str) -> Dict[str, Any]:
        """Parse le contenu généré en structure (à améliorer)"""
        # TODO: Implémenter un vrai parser
        return {
            "_raw_text": content_text,
            "État": "Brouillon IA"
        }

def main():
    """Test de l'agent d'écriture générique"""
    print("=== Test WriterAgent Générique ===\n")
    
    # Test avec le domaine Personnages
    from config.domain_configs.personnages_config import PERSONNAGES_CONFIG
    
    writer_config = WriterConfig(
        intent="orthogonal_depth",
        level="standard",
        dialogue_mode="parle",
        creativity=0.7
    )
    
    agent = WriterAgent(PERSONNAGES_CONFIG, writer_config)
    
    brief = "Un médecin qui soigne les Gedroths mais cache une obsession étrange. Genre: Non défini. Espèce: Humain modifié. Âge: 35 cycles."
    
    print(f"Domaine: {agent.domain}")
    print(f"Brief: {brief}\n")
    print("Génération...\n")
    
    result = agent.process(brief)
    
    if result.success:
        print("=" * 60)
        print("CONTENU GÉNÉRÉ:")
        print("=" * 60)
        print(result.content)
        print("\n" + "=" * 60)
        print(f"\nMétadonnées: {result.metadata}")
    else:
        print(f"Erreur: {result.errors}")

if __name__ == "__main__":
    main()

