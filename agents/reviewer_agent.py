#!/usr/bin/env python3
"""
Agent de relecture générique configuré par domaine
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

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
            context = self.gather_context()
        
        # Construire le prompt de relecture
        user_prompt = self._build_review_prompt(content, context)
        
        # Analyser avec le LLM
        system_prompt = self._build_system_prompt("reviewer")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = self.llm.invoke(messages)
            review_text = self._to_text(response.content if hasattr(response, 'content') else response)
            
            # Parser les issues et suggestions
            issues, improvements, score = self._parse_review(review_text)
            
            # Générer le contenu amélioré si pertinent
            improved_content = self._generate_improvements(content, improvements) if improvements else content
            
            return ReviewResult(
                success=True,
                content=improved_content,
                metadata={
                    "domain": self.domain,
                    "original_content": content,
                    "raw_review": review_text
                },
                issues=issues,
                improvements=improvements,
                coherence_score=score
            )
        except Exception as e:
            return ReviewResult(
                success=False,
                content=content,
                metadata={"domain": self.domain},
                errors=[str(e)],
                coherence_score=0.0
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
        issues = []
        improvements = []
        score = 0.7  # Score par défaut
        
        # TODO: Implémenter un vrai parser
        # Pour l'instant, extraire basiquement
        
        lines = review_text.split('\n')
        for line in lines:
            # Détecter les issues
            if '[CRITIQUE]' in line or '[MAJEUR]' in line or '[MINEUR]' in line:
                severity = "critical" if '[CRITIQUE]' in line else ("major" if '[MAJEUR]' in line else "minor")
                issues.append(ReviewIssue(
                    severity=severity,
                    category="general",
                    description=line.strip(),
                    suggestion=None
                ))
            
            # Détecter le score
            if 'score' in line.lower() and any(c.isdigit() for c in line):
                try:
                    # Extraire le score (format 0.X ou X/10)
                    import re
                    if '/' in line:
                        match = re.search(r'(\d+)/10', line)
                        if match:
                            score = float(match.group(1)) / 10
                    else:
                        match = re.search(r'0?\.\d+', line)
                        if match:
                            score = float(match.group(0))
                except:
                    pass
        
        # Extraire les suggestions (dernières lignes généralement)
        if "suggestion" in review_text.lower() or "amélioration" in review_text.lower():
            suggestion_lines = [l for l in lines if l.strip().startswith(('-', '•', '*', '1.', '2.', '3.'))]
            improvements = [l.strip().lstrip('-•*123456789.').strip() for l in suggestion_lines[-5:]]
        
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

