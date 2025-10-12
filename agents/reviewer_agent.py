#!/usr/bin/env python3
"""
Agent de relecture générique configuré par domaine
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field
from typing import List as _List

# Ajouter le répertoire racine au path
sys.path.append(str(Path(__file__).parent.parent))

from agents.base.base_agent import BaseAgent, AgentResult
from agents.base.domain_config import DomainConfig

@dataclass
class ReviewIssue:
    """Problème identifié lors de la relecture"""
    severity: str  # "critical", "major", "minor"
    category: str  # "coherence", "structure", "relations", "lore"
    description: str
    suggestion: Optional[str] = None

@dataclass
class ReviewResult(AgentResult):
    """Résultat spécifique de la relecture"""
    issues: List[ReviewIssue] = None
    improvements: List[str] = None
    coherence_score: float = 0.0
    
    def __post_init__(self):
        super().__post_init__()
        if self.issues is None:
            self.issues = []
        if self.improvements is None:
            self.improvements = []

class ReviewerAgent(BaseAgent):
    """
    Agent de relecture générique configuré par domaine
    
    Responsabilités:
    - Vérification de la cohérence narrative
    - Validation des liens entre éléments
    - Contrôle de la structure
    - Vérification du respect des principes du domaine
    """
    
    BASE_PROMPT = """Tu es un agent de relecture expert pour le GDD Alteir.

**MISSION PRINCIPALE:**
Analyser le contenu pour identifier les problèmes de cohérence, structure et qualité narrative.

**AXES D'ANALYSE:**

1. **Cohérence narrative**: 
   - Le contenu s'intègre-t-il harmonieusement dans l'univers ?
   - Y a-t-il des contradictions avec les éléments existants ?
   - Les références sont-elles valides ?

2. **Structure et complétude**:
   - Tous les champs obligatoires sont-ils présents ?
   - La structure est-elle respectée ?
   - L'information est-elle organisée logiquement ?

3. **Relations et liens**:
   - Les relations avec d'autres entités sont-elles cohérentes ?
   - Les liens croisés sont-ils valides ?
   - Les dépendances sont-elles respectées ?

4. **Qualité narrative**:
   - Le contenu est-il original et évocateur ?
   - Évite-t-il les clichés ?
   - Respecte-t-il les principes du domaine ?

**MÉTHODOLOGIE:**
1. Identifier les problèmes (critiques, majeurs, mineurs)
2. Proposer des améliorations spécifiques
3. Évaluer la cohérence globale (score 0-1)
4. Suggérer des optimisations

Tu es rigoureux mais constructif, toujours orienté vers l'amélioration."""
    
    def __init__(self, domain_config: DomainConfig, llm=None):
        """Initialise l'agent de relecture"""
        super().__init__(domain_config, llm)
    
    def process(self, content: str, context: Dict[str, Any] = None) -> ReviewResult:
        """
        Analyse le contenu et identifie les problèmes
        
        Args:
            content: Contenu à relire
            context: Contexte Notion optionnel
            
        Returns:
            ReviewResult avec les issues et suggestions
        """
        # Récupérer le contexte si non fourni
        if context is None:
            self.logger.debug("Contexte manquant pour la relecture, récupération automatique")
            context = self.gather_context()
        
        # Construire le prompt de relecture
        user_prompt = self._build_review_prompt(content, context)
        
        # Analyser avec le LLM (Structured Outputs si dispo)
        system_prompt = self._build_system_prompt("reviewer")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            self.logger.info("Analyse de cohérence en cours")
            # 1) Essayer structured outputs via LLMAdapter
            from agents.base.llm_utils import LLMAdapter

            class _Issue(BaseModel):
                severity: str = Field(description="critical|major|minor")
                category: str = Field(description="coherence|structure|relations|lore|general")
                description: str
                suggestion: str | None = None

            class _ReviewSchema(BaseModel):
                issues: _List[_Issue] = Field(default_factory=list)
                improvements: _List[str] = Field(default_factory=list)
                coherence_score: float = 0.7
                improved_content: str | None = None

            adapter = LLMAdapter(self.llm)
            try:
                structured = adapter.get_structured_output(messages, _ReviewSchema)
                review_text = ""  # optional
                issues = [
                    ReviewIssue(
                        severity=i.severity,
                        category=i.category,
                        description=i.description,
                        suggestion=i.suggestion,
                    )
                    for i in structured.issues
                ]
                improvements = list(structured.improvements)
                score = float(structured.coherence_score)
                improved_content = structured.improved_content or content
            except Exception:
                # 2) Fallback: texte + parser existant
                response = self.llm.invoke(messages)
                review_text = self._to_text(response.content if hasattr(response, 'content') else response)
                issues, improvements, score = self._parse_review(review_text)
                improved_content = self._generate_improvements(content, improvements) if improvements else content

            # Générer le contenu amélioré si pertinent
            # (déjà géré ci-dessus pour structured; conservé pour cohérence)

            self.logger.debug(
                "Relecture réussie | issues=%d | score=%.2f",
                len(issues),
                score,
            )

            return ReviewResult(
                success=True,
                content=improved_content,
                metadata={
                    "domain": self.domain,
                    "original_content": content,
                    "raw_review": review_text,
                },
                issues=issues,
                improvements=improvements,
                coherence_score=score,
            )
        except Exception as e:
            self.logger.exception("Erreur lors de la relecture")
            return ReviewResult(
                success=False,
                content=content,
                metadata={"domain": self.domain},
                errors=[str(e)],
                coherence_score=0.0,
            )

    def process_stream(self, content: str, context: Dict[str, Any] = None, include_reasoning: bool = False):
        """Stream review text deltas when not using structured outputs.
        Yields dict events {"text", "reasoning"?} and finally returns ReviewResult.
        """
        if context is None:
            self.logger.debug("Contexte manquant pour la relecture, récupération automatique")
            context = self.gather_context()

        user_prompt = self._build_review_prompt(content, context)
        system_prompt = self._build_system_prompt("reviewer")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # If we have native structured outputs, skip streaming to preserve structure
        try:
            from agents.base.llm_utils import LLMAdapter
            adapter = LLMAdapter(self.llm)
            if adapter.supports_structured:
                return self.process(content, context)

            accumulated_parts: list[str] = []
            for delta in adapter.stream_text(messages, include_reasoning=include_reasoning):
                if isinstance(delta, dict):
                    text_part = delta.get("text", "")
                    reasoning_part = delta.get("reasoning")
                    if text_part:
                        accumulated_parts.append(text_part)
                    yield {"text": text_part, **({"reasoning": reasoning_part} if reasoning_part else {})}
                else:
                    if delta:
                        accumulated_parts.append(delta)
                        yield {"text": delta}

            review_text = "".join(accumulated_parts)
            issues, improvements, score = self._parse_review(review_text)
            improved_content = self._generate_improvements(content, improvements) if improvements else content
            return ReviewResult(
                success=True,
                content=improved_content,
                metadata={"domain": self.domain, "original_content": content, "raw_review": review_text},
                issues=issues,
                improvements=improvements,
                coherence_score=score,
            )
        except Exception as e:
            self.logger.exception("Erreur lors du streaming de relecture")
            # Fallback to non-streaming so we still produce a result
            try:
                return self.process(content, context)
            except Exception as e2:
                return ReviewResult(
                    success=False,
                    content=content,
                    metadata={"domain": self.domain},
                    errors=[str(e), str(e2)],
                    coherence_score=0.0,
                )
        
    
    def _build_review_prompt(self, content: str, context: Dict[str, Any]) -> str:
        """Construit le prompt de relecture"""
        
        required_fields = self.domain_config.get_required_fields()
        
        prompt = f"""**CONTENU À RELIRE:**

{content}

**CONTEXTE ({self.domain_config.display_name.upper()}):**
{self._format_context(context)}

**CHAMPS OBLIGATOIRES:**
{', '.join(required_fields)}

**INSTRUCTIONS:**
Analyse ce contenu selon les axes suivants:

1. **COHÉRENCE NARRATIVE** (score /10):
   - Intégration dans l'univers Alteir
   - Absence de contradictions
   - Validité des références

2. **STRUCTURE ET COMPLÉTUDE**:
   - Présence des champs obligatoires
   - Respect de la structure
   - Organisation logique

3. **RELATIONS ET LIENS**:
   - Cohérence des relations
   - Validité des liens croisés
   - Respect des dépendances

4. **QUALITÉ NARRATIVE**:
   - Originalité
   - Évitement des clichés
   - Respect des principes du domaine

Pour chaque problème identifié, indique:
- Sévérité: [CRITIQUE] / [MAJEUR] / [MINEUR]
- Catégorie: cohérence / structure / relations / lore
- Description précise
- Suggestion d'amélioration

Termine par un score de cohérence globale (0.0 à 1.0) et 3-5 suggestions d'amélioration prioritaires."""
        
        return prompt
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Formate le contexte"""
        parts = []
        
        for key in ["especes", "lieux", "communautes"]:
            if context.get(key):
                parts.append(f"**{key.capitalize()}:** " + ", ".join(context[key][:5]))
        
        return "\n".join(parts) if parts else "Contexte minimal"
    
    def _parse_review(self, review_text: str) -> tuple[List[ReviewIssue], List[str], float]:
        """Parse la relecture pour extraire issues, suggestions et score"""
        import re
        
        issues = []
        improvements = []
        score = 0.7  # Score par défaut
        
        lines = review_text.split('\n')
        
        # Parser les problèmes avec contexte
        current_severity = None
        current_category = None
        current_description = []
        current_suggestion = []
        in_suggestion = False
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Détecter un nouveau problème
            severity_match = re.search(r'Sévérité:\s*\[?(CRITIQUE|MAJEUR|MINEUR)\]?', line, re.IGNORECASE)
            if severity_match:
                # Sauvegarder le problème précédent s'il existe
                if current_severity and current_description:
                    desc = ' '.join(current_description).strip()
                    sugg = ' '.join(current_suggestion).strip() if current_suggestion else None
                    if desc and desc not in ["- Sévérité: [CRITIQUE]", "- Sévérité: [MAJEUR]", "- Sévérité: [MINEUR]"]:
                        issues.append(ReviewIssue(
                            severity=current_severity,
                            category=current_category or "general",
                            description=desc,
                            suggestion=sugg
                        ))
                
                # Nouveau problème
                current_severity = severity_match.group(1).lower()
                if current_severity == "critique":
                    current_severity = "critical"
                elif current_severity == "majeur":
                    current_severity = "major"
                elif current_severity == "mineur":
                    current_severity = "minor"
                    
                current_description = []
                current_suggestion = []
                in_suggestion = False
                continue
            
            # Détecter la catégorie
            category_match = re.search(r'Catégorie:\s*(.+)', line, re.IGNORECASE)
            if category_match:
                current_category = category_match.group(1).strip()
                continue
            
            # Détecter la description
            desc_match = re.search(r'Description:\s*(.+)', line, re.IGNORECASE)
            if desc_match:
                current_description.append(desc_match.group(1).strip())
                continue
            
            # Détecter la suggestion
            if re.search(r'Suggestion.*:', line, re.IGNORECASE):
                in_suggestion = True
                sugg_match = re.search(r'Suggestion[^:]*:\s*(.+)', line, re.IGNORECASE)
                if sugg_match:
                    current_suggestion.append(sugg_match.group(1).strip())
                continue
            
            # Continuer description ou suggestion
            if current_severity:
                if in_suggestion and line_stripped:
                    current_suggestion.append(line_stripped)
                elif not in_suggestion and line_stripped and not line_stripped.startswith(('Problème', 'Sévérité', 'Catégorie')):
                    # C'est probablement la suite de la description
                    if i > 0 and current_description:  # Seulement si on a déjà une description
                        current_description.append(line_stripped)
            
            # Détecter le score
            if 'score' in line.lower() and any(c.isdigit() for c in line):
                try:
                    # Format avec deux points : "Score ... : 0.65"
                    if ':' in line:
                        match = re.search(r':\s*(\d*\.?\d+)\s*$', line)
                        if match:
                            score_val = float(match.group(1))
                            # Si > 1, c'est probablement sur 10
                            score = score_val / 10 if score_val > 1 else score_val
                    # Format avec fraction : "8/10"
                    elif '/' in line:
                        match = re.search(r'(\d+)/10', line)
                        if match:
                            score = float(match.group(1)) / 10
                    # Format décimal simple : "0.65"
                    else:
                        match = re.search(r'0?\.\d+', line)
                        if match:
                            score = float(match.group(0))
                except:
                    pass
        
        # Sauvegarder le dernier problème
        if current_severity and current_description:
            desc = ' '.join(current_description).strip()
            sugg = ' '.join(current_suggestion).strip() if current_suggestion else None
            if desc and desc not in ["- Sévérité: [CRITIQUE]", "- Sévérité: [MAJEUR]", "- Sévérité: [MINEUR]"]:
                issues.append(ReviewIssue(
                    severity=current_severity,
                    category=current_category or "general",
                    description=desc,
                    suggestion=sugg
                ))
        
        # Extraire les suggestions d'amélioration générales
        if "suggestion" in review_text.lower() or "amélioration" in review_text.lower():
            suggestion_section = re.split(r'Suggestions? d[\'e]amélioration', review_text, flags=re.IGNORECASE)
            if len(suggestion_section) > 1:
                suggestion_lines = [l.strip() for l in suggestion_section[-1].split('\n') 
                                   if l.strip() and l.strip().startswith(('-', '•', '*', '1.', '2.', '3.'))]
                improvements = [l.lstrip('-•*123456789.').strip() for l in suggestion_lines[:5]]
        
        return issues, improvements, score
    
    def _generate_improvements(self, content: str, improvements: List[str]) -> str:
        """Applique les améliorations suggérées (optionnel)"""
        # Pour l'instant, retourner le contenu original
        # Dans une vraie implémentation, appliquer les suggestions
        return content

def main():
    """Test de l'agent de relecture"""
    print("=== Test ReviewerAgent ===\n")
    
    from config.domain_configs.personnages_config import PERSONNAGES_CONFIG
    
    agent = ReviewerAgent(PERSONNAGES_CONFIG)
    
    # Contenu de test avec quelques problèmes volontaires
    test_content = """**Nom:** Kira la Silencieuse
**Alias:** L'Ombre du Léviathan
**Type:** PNJ principal
**Occupation:** Voleuse
**Espèce:** Espèce Inexistante
**Âge:** 200 cycles
**Genre:** Féminin
**Archétype littéraire:** Friponne / Menteur
**Axe idéologique:** Destruction
**Qualités:** Discrète, Agile
**Défauts:** Traîtresse, Méfiante
**Communautés:** Guilde Inconnue
**Lieux de vie:** Ville Inexistante
**Réponse au problème moral:** Le vol est justifié par la survie

**Dialogue:**
1. "Les ombres sont mes alliées."
2. "Je prends ce qui m'appartient de droit."
"""
    
    print(f"Domaine: {agent.domain}\n")
    print("Contenu à relire:")
    print("-" * 60)
    print(test_content)
    print("-" * 60)
    print("\nAnalyse en cours...\n")
    
    result = agent.process(test_content)
    
    if result.success:
        print("=" * 60)
        print("RÉSULTAT DE LA RELECTURE:")
        print("=" * 60)
        print(f"\nScore de cohérence: {result.coherence_score:.2f}")
        
        if result.issues:
            print(f"\nProblemes identifies ({len(result.issues)}):")
            for i, issue in enumerate(result.issues, 1):
                print(f"\n{i}. [{issue.severity.upper()}] {issue.description}")
        
        if result.improvements:
            print(f"\nSuggestions d'amelioration ({len(result.improvements)}):")
            for i, improvement in enumerate(result.improvements, 1):
                print(f"{i}. {improvement}")
        
        print("\n" + "=" * 60)
    else:
        print(f"Erreur: {result.errors}")

if __name__ == "__main__":
    main()

