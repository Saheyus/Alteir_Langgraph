#!/usr/bin/env python3
"""
Agent de validation générique configuré par domaine
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
class ValidationError:
    """Erreur de validation"""
    field: str
    error_type: str  # "missing", "invalid", "inconsistent", "incomplete"
    description: str
    severity: str  # "critical", "warning"

@dataclass
class ValidationResult(AgentResult):
    """Résultat spécifique de la validation"""
    is_valid: bool = False
    validation_errors: List[ValidationError] = None
    completeness_score: float = 0.0
    quality_score: float = 0.0
    ready_for_publication: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        if self.validation_errors is None:
            self.validation_errors = []

class ValidatorAgent(BaseAgent):
    """
    Agent de validation générique configuré par domaine
    
    Responsabilités:
    - Validation finale du contenu
    - Vérification des champs obligatoires
    - Validation des références croisées
    - Contrôle de la complétude
    - Décision de publication
    """
    
    BASE_PROMPT = """Tu es un agent de validation expert pour le GDD Alteir.

**MISSION PRINCIPALE:**
Effectuer une validation finale et complète du contenu avant publication.

**AXES DE VALIDATION:**

1. **Complétude**:
   - Tous les champs obligatoires sont présents et remplis
   - L'information est suffisamment détaillée
   - Aucun élément critique ne manque
   - La structure est complète

2. **Références Croisées**:
   - Toutes les références à d'autres entités sont valides
   - Les liens entre éléments sont cohérents
   - Les dépendances sont satisfaites
   - Pas de références à des éléments inexistants

3. **Qualité Narrative**:
   - Le contenu respecte les principes du domaine
   - La cohérence narrative est assurée
   - L'originalité est présente
   - Le niveau de détail est approprié

4. **Standards Techniques**:
   - Le format est correct
   - Les données structurées sont valides
   - Les contraintes du domaine sont respectées
   - Les règles de validation sont satisfaites

**DÉCISION DE PUBLICATION:**
Le contenu est prêt pour publication SI ET SEULEMENT SI:
- Aucune erreur CRITIQUE
- Score de complétude ≥ 0.8
- Score de qualité ≥ 0.7
- Toutes les références sont valides

Tu es rigoureux et exigeant, garant de la qualité finale du GDD."""
    
    def __init__(self, domain_config: DomainConfig, llm=None):
        """Initialise l'agent de validation"""
        super().__init__(domain_config, llm)
    
    def process(self, content: str, context: Dict[str, Any] = None) -> ValidationResult:
        """
        Valide le contenu
        
        Args:
            content: Contenu à valider
            context: Contexte Notion optionnel
            
        Returns:
            ValidationResult avec le statut de validation
        """
        # Récupérer le contexte si nécessaire
        if context is None:
            self.logger.debug("Contexte absent pour le validateur, récupération automatique")
            context = self.gather_context()
        
        # Construire le prompt de validation
        user_prompt = self._build_validation_prompt(content, context)
        
        # Valider avec le LLM (Structured Outputs si dispo)
        system_prompt = self._build_system_prompt("validator")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            self.logger.info("Validation finale en cours")
            # 1) Structured Outputs via LLMAdapter
            from agents.base.llm_utils import LLMAdapter

            class _VError(BaseModel):
                field: str
                error_type: str
                description: str
                severity: str

            class _VSchema(BaseModel):
                validation_errors: _List[_VError] = Field(default_factory=list)
                completeness_score: float = 0.0
                quality_score: float = 0.0
                is_valid: bool = False
                ready_for_publication: bool = False

            adapter = LLMAdapter(self.llm)
            try:
                structured = adapter.get_structured_output(messages, _VSchema)
                validation_text = ""
                errors = [
                    ValidationError(
                        field=e.field,
                        error_type=e.error_type,
                        description=e.description,
                        severity=e.severity,
                    )
                    for e in structured.validation_errors
                ]
                completeness = float(structured.completeness_score)
                quality = float(structured.quality_score)
                is_valid = bool(structured.is_valid)
                ready = bool(structured.ready_for_publication)
            except Exception:
                # 2) Fallback: texte + parser existant
                response = self.llm.invoke(messages)
                validation_text = self._to_text(response.content if hasattr(response, 'content') else response)
                errors, completeness, quality, is_valid, ready = self._parse_validation(validation_text)

            self.logger.debug(
                "Validation complétée | errors=%d | completeness=%.2f | quality=%.2f | ready=%s",
                len(errors),
                completeness,
                quality,
                ready,
            )

            return ValidationResult(
                success=True,
                content=content,
                metadata={
                    "domain": self.domain,
                    "raw_validation": validation_text
                },
                is_valid=is_valid,
                validation_errors=errors,
                completeness_score=completeness,
                quality_score=quality,
                ready_for_publication=ready
            )
        except Exception as e:
            self.logger.exception("Erreur lors de la validation")
            return ValidationResult(
                success=False,
                content=content,
                metadata={"domain": self.domain},
                errors=[str(e)],
                is_valid=False,
                ready_for_publication=False
            )
    
    def _build_validation_prompt(self, content: str, context: Dict[str, Any]) -> str:
        """Construit le prompt de validation"""
        
        required_fields = self.domain_config.get_required_fields()
        
        prompt = f"""**CONTENU À VALIDER:**

{content}

**CONTEXTE ({self.domain_config.display_name.upper()}):**
{self._format_context(context)}

**CHAMPS OBLIGATOIRES:**
{', '.join(required_fields)}

**VALIDATION COMPLÈTE:**

1. **COMPLÉTUDE** (score /10):
   - Présence de tous les champs obligatoires: {', '.join(required_fields)}
   - Niveau de détail suffisant
   - Structure complète
   
2. **RÉFÉRENCES CROISÉES**:
   - Espèces mentionnées existent dans: {', '.join(context.get('especes', [])[:5])}
   - Lieux mentionnés existent dans: {', '.join(context.get('lieux', [])[:5])}
   - Communautés mentionnées existent dans: {', '.join(context.get('communautes', [])[:5])}
   
3. **QUALITÉ NARRATIVE** (score /10):
   - Respect des principes du domaine
   - Cohérence narrative
   - Originalité
   - Niveau de détail approprié
   
4. **STANDARDS TECHNIQUES**:
   - Format correct
   - Données structurées valides
   - Contraintes respectées

**FORMAT DE RÉPONSE:**

[COMPLÉTUDE: X/10]
[QUALITÉ: X/10]

[ERREUR CRITIQUE] Champ / Description (si applicable)
[ERREUR CRITIQUE] ...

[AVERTISSEMENT] Champ / Description (si applicable)
[AVERTISSEMENT] ...

[STATUT: VALIDE/INVALIDE]
[PUBLICATION: OUI/NON]

Justification finale en 2-3 phrases."""
        
        return prompt
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Formate le contexte"""
        parts = []
        
        for key in ["especes", "lieux", "communautes"]:
            if context.get(key):
                parts.append(f"**{key.capitalize()}:** " + ", ".join(context[key][:5]))
        
        return "\n".join(parts) if parts else "Contexte minimal"
    
    def _parse_validation(self, validation_text: str) -> tuple[List[ValidationError], float, float, bool, bool]:
        """Parse le résultat de validation"""
        
        errors = []
        completeness = 0.5
        quality = 0.5
        is_valid = False
        ready = False
        
        lines = validation_text.split('\n')
        
        for line in lines:
            # Extraire les scores
            if '[COMPLÉTUDE:' in line or '[COMPLETUDE:' in line:
                try:
                    score_text = line.split(':')[1].strip().rstrip(']')
                    if '/' in score_text:
                        completeness = float(score_text.split('/')[0].strip()) / 10
                    else:
                        completeness = float(score_text)
                except:
                    pass
            
            if '[QUALITÉ:' in line or '[QUALITE:' in line:
                try:
                    score_text = line.split(':')[1].strip().rstrip(']')
                    if '/' in score_text:
                        quality = float(score_text.split('/')[0].strip()) / 10
                    else:
                        quality = float(score_text)
                except:
                    pass
            
            # Extraire les erreurs
            if '[ERREUR CRITIQUE]' in line:
                parts = line.split(']', 1)
                if len(parts) > 1:
                    desc = parts[1].strip()
                    field = desc.split('/')[0].strip() if '/' in desc else "général"
                    errors.append(ValidationError(
                        field=field,
                        error_type="critical",
                        description=desc,
                        severity="critical"
                    ))
            
            if '[AVERTISSEMENT]' in line:
                parts = line.split(']', 1)
                if len(parts) > 1:
                    desc = parts[1].strip()
                    field = desc.split('/')[0].strip() if '/' in desc else "général"
                    errors.append(ValidationError(
                        field=field,
                        error_type="warning",
                        description=desc,
                        severity="warning"
                    ))
            
            # Extraire les statuts
            if '[STATUT:' in line:
                is_valid = 'VALIDE' in line.upper()
            
            if '[PUBLICATION:' in line:
                ready = 'OUI' in line.upper()
        
        return errors, completeness, quality, is_valid, ready

def main():
    """Test de l'agent de validation"""
    print("=== Test ValidatorAgent ===\n")
    
    from config.domain_configs.personnages_config import PERSONNAGES_CONFIG
    
    agent = ValidatorAgent(PERSONNAGES_CONFIG)
    
    # Contenu de test avec quelques problèmes
    test_content = """**Nom:** Zephira la Tisseuse
**Alias:** La Gardienne des Fils
**Type:** PNJ principal
**Occupation:** Tisseuse de destins
**Espèce:** Humain modifié
**Âge:** 45 cycles
**Genre:** Féminin
**Archétype littéraire:** Magicienne / Sorcier
**Axe idéologique:** Connexion
**Qualités:** Empathique, Patiente, Visionnaire
**Défauts:** Obsessionnelle, Secrète
**Langage:** Métaphorique, poétique
**Communautés:** Les Cartographes
**Lieux de vie:** Le Léviathan Pétrifié
**Réponse au problème moral:** Chaque fil a son importance dans la tapisserie

**Dialogue:**
1. "Les fils du destin s'entrelacent de manières mystérieuses."
2. "Je vois les connexions que d'autres ignorent."
3. "Chaque choix tisse un nouveau motif dans la toile."
"""
    
    print(f"Domaine: {agent.domain}\n")
    print("Contenu à valider:")
    print("-" * 60)
    print(test_content)
    print("-" * 60)
    print("\nValidation en cours...\n")
    
    result = agent.process(test_content)
    
    if result.success:
        print("=" * 60)
        print("RÉSULTAT DE LA VALIDATION:")
        print("=" * 60)
        print(f"\nStatut: {'VALIDE' if result.is_valid else 'INVALIDE'}")
        print(f"Score de completude: {result.completeness_score:.2f}")
        print(f"Score de qualite: {result.quality_score:.2f}")
        print(f"Pret pour publication: {'OUI' if result.ready_for_publication else 'NON'}")
        
        if result.validation_errors:
            print(f"\nProblemes detectes ({len(result.validation_errors)}):")
            for i, error in enumerate(result.validation_errors, 1):
                icon = "[!]" if error.severity == "critical" else "[~]"
                print(f"{i}. {icon} [{error.field}] {error.description}")
        else:
            print("\nAucun probleme detecte !")
        
        print("\n" + "=" * 60)
    else:
        print(f"Erreur: {result.errors}")

if __name__ == "__main__":
    main()

