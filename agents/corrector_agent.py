#!/usr/bin/env python3
"""
Agent de correction générique configuré par domaine
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
class Correction:
    """Correction effectuée"""
    type: str  # "orthographe", "grammaire", "style", "clarté"
    original: str
    corrected: str
    explanation: Optional[str] = None

@dataclass
class CorrectionResult(AgentResult):
    """Résultat spécifique de la correction"""
    corrections: List[Correction] = None
    improvement_summary: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        if self.corrections is None:
            self.corrections = []

class CorrectorAgent(BaseAgent):
    """
    Agent de correction générique configuré par domaine
    
    Responsabilités:
    - Correction orthographique et grammaticale
    - Amélioration de la clarté et du style
    - Respect des conventions d'écriture
    - Maintien de la richesse et des spécificités du domaine
    """
    
    BASE_PROMPT = """Tu es un agent de correction expert pour le GDD Alteir.

**MISSION PRINCIPALE:**
Corriger et améliorer la qualité linguistique du contenu tout en préservant sa richesse narrative.

**AXES DE CORRECTION:**

1. **Orthographe et Grammaire**:
   - Corriger les fautes d'orthographe
   - Corriger les erreurs grammaticales
   - Respecter les accords
   - Vérifier la ponctuation

2. **Clarté et Lisibilité**:
   - Améliorer la structure des phrases
   - Éliminer les ambiguïtés
   - Simplifier les formulations complexes sans perdre le sens
   - Assurer la fluidité de lecture

3. **Style et Conventions**:
   - Respecter le style du GDD (cru mais non esthétisant)
   - Éviter les anglicismes non nécessaires
   - Maintenir les néologismes avec leurs gloses
   - Préserver la richesse du vocabulaire

4. **Cohérence Linguistique**:
   - Uniformiser les termes récurrents
   - Respecter les conventions de capitalisation
   - Maintenir la cohérence des temps verbaux
   - Préserver les tournures spécifiques à l'univers

**RÈGLES IMPÉRATIVES:**
- NE PAS modifier le sens ou le contenu narratif
- NE PAS supprimer les détails importants
- PRÉSERVER les néologismes et termes spécifiques
- MAINTENIR le ton et l'atmosphère
- RESPECTER les gloses (5-8 mots) pour les termes inventés

Tu es précis et respectueux du travail créatif, améliorant la forme sans altérer le fond."""
    
    def __init__(self, domain_config: DomainConfig, llm=None):
        """Initialise l'agent de correction"""
        super().__init__(domain_config, llm)
    
    def process(self, content: str, context: Dict[str, Any] = None) -> CorrectionResult:
        """
        Corrige le contenu
        
        Args:
            content: Contenu à corriger
            context: Contexte Notion optionnel
            
        Returns:
            CorrectionResult avec le contenu corrigé et les modifications
        """
        # Récupérer le contexte si nécessaire
        if context is None:
            self.logger.debug("Contexte absent pour le correcteur, récupération automatique")
            context = self.gather_context()
        
        # Construire le prompt de correction
        user_prompt = self._build_correction_prompt(content, context)
        
        # Corriger avec le LLM (Structured Outputs si dispo)
        system_prompt = self._build_system_prompt("corrector")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            self.logger.info("Correction linguistique en cours")
            # 1) Structured Outputs via LLMAdapter
            from agents.base.llm_utils import LLMAdapter

            class _Corr(BaseModel):
                type: str
                original: str
                corrected: str
                explanation: str | None = None

            class _CorrSchema(BaseModel):
                corrected_content: str
                corrections: _List[_Corr] = Field(default_factory=list)
                improvement_summary: str = ""

            adapter = LLMAdapter(self.llm)
            try:
                structured = adapter.get_structured_output(messages, _CorrSchema)
                correction_text = ""
                corrected_content = structured.corrected_content or content
                corrections = [
                    Correction(
                        type=c.type,
                        original=c.original,
                        corrected=c.corrected,
                        explanation=c.explanation,
                    )
                    for c in structured.corrections
                ]
                summary = structured.improvement_summary or ""
            except Exception:
                # 2) Fallback: texte + parser existant
                response = self.llm.invoke(messages)
                correction_text = self._to_text(response.content if hasattr(response, 'content') else response)
                corrected_content, corrections, summary = self._parse_corrections(content, correction_text)

            self.logger.debug(
                "Corrections appliquées | total=%d", len(corrections)
            )
            return CorrectionResult(
                success=True,
                content=corrected_content,
                metadata={
                    "domain": self.domain,
                    "original_content": content,
                    "raw_response": correction_text,
                },
                corrections=corrections,
                improvement_summary=summary,
            )
        except Exception as e:
            self.logger.exception("Erreur lors de la correction")
            return CorrectionResult(
                success=False,
                content=content,
                metadata={"domain": self.domain},
                errors=[str(e)],
            )
    
    def process_stream(self, content: str, context: Dict[str, Any] = None, include_reasoning: bool = False):
        """Stream correction text deltas when not using structured outputs.
        Yields dict events {"text", "reasoning"?} and finally returns CorrectionResult.
        """
        if context is None:
            self.logger.debug("Contexte absent pour le correcteur, récupération automatique")
            context = self.gather_context()

        user_prompt = self._build_correction_prompt(content, context)
        system_prompt = self._build_system_prompt("corrector")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

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

            correction_text = "".join(accumulated_parts)
            corrected_content, corrections, summary = self._parse_corrections(content, correction_text)
            return CorrectionResult(
                success=True,
                content=corrected_content,
                metadata={"domain": self.domain, "original_content": content, "raw_response": correction_text},
                corrections=corrections,
                improvement_summary=summary,
            )
        except Exception as e:
            self.logger.exception("Erreur lors du streaming de correction; fallback non-streaming")
            try:
                return self.process(content, context)
            except Exception as e2:
                return CorrectionResult(
                    success=False,
                    content=content,
                    metadata={"domain": self.domain},
                    errors=[str(e), str(e2)],
                )

    
    def _build_correction_prompt(self, content: str, context: Dict[str, Any]) -> str:
        """Construit le prompt de correction"""
        
        prompt = f"""**CONTENU À CORRIGER:**

{content}

**INSTRUCTIONS DE CORRECTION:**

Corrige ce contenu selon les axes suivants:

1. **ORTHOGRAPHE ET GRAMMAIRE**:
   - Fautes d'orthographe
   - Erreurs grammaticales
   - Accords (genre, nombre)
   - Ponctuation

2. **CLARTÉ ET LISIBILITÉ**:
   - Structure des phrases
   - Ambiguïtés
   - Formulations lourdes
   - Fluidité

3. **STYLE ET CONVENTIONS**:
   - Anglicismes à éviter
   - Cohérence du vocabulaire
   - Ton approprié (cru mais non esthétisant)

4. **PRÉSERVATION**:
   - NE PAS modifier le sens narratif
   - GARDER tous les néologismes et gloses
   - MAINTENIR les détails importants
   - RESPECTER l'atmosphère

**FORMAT DE SORTIE:**

1. D'abord, fournis le contenu corrigé complet.

2. Ensuite, liste les corrections effectuées:
[CORRECTION: type] Original → Corrigé (explication optionnelle)

3. Enfin, un bref résumé des améliorations (2-3 phrases).

Commence directement par le contenu corrigé."""
        
        return prompt
    
    def _parse_corrections(self, original: str, correction_text: str) -> tuple[str, List[Correction], str]:
        """Parse le résultat pour extraire le contenu corrigé et les modifications"""
        import re
        
        # Nettoyer les sections parasites (instructions, etc.)
        cleaned_text = correction_text
        
        # Supprimer les sections "INSTRUCTIONS" et "Corrections effectuées:" vides
        cleaned_text = re.sub(r'INSTRUCTIONS DE CORRECTION:.*?(?=\n\n|\Z)', '', cleaned_text, flags=re.DOTALL)
        cleaned_text = re.sub(r'Corrections effectuées:\s*$', '', cleaned_text, flags=re.MULTILINE)
        
        # Séparer le contenu corrigé des corrections listées
        parts = cleaned_text.split('[CORRECTION:', 1)
        corrected_content = parts[0].strip()
        
        # Aussi séparer si format "- [CORRECTION:" (avec tiret)
        if len(parts) == 1 and '- [CORRECTION:' in cleaned_text:
            parts = cleaned_text.split('- [CORRECTION:', 1)
            corrected_content = parts[0].strip()
        
        corrections = []
        summary = ""
        
        if len(parts) > 1:
            # Extraire les corrections
            corrections_part = '[CORRECTION:' + parts[1]
            lines = corrections_part.split('\n')
            
            for line in lines:
                # Gérer aussi le format avec tiret: "- [CORRECTION: ..."
                if '[CORRECTION:' in line or '- [CORRECTION:' in line:
                    try:
                        # Format: [CORRECTION: type] Original → Corrigé (explication)
                        # ou: - [CORRECTION: type] Original → Corrigé (explication)
                        line = line.replace('- [CORRECTION:', '[CORRECTION:')
                        parts_line = line.split(']', 1)
                        if len(parts_line) > 1:
                            corr_type = parts_line[0].replace('[CORRECTION:', '').strip()
                            rest = parts_line[1].strip()
                            
                            if '→' in rest:
                                orig_corr = rest.split('→')
                                original_text = orig_corr[0].strip()
                                
                                if len(orig_corr) > 1:
                                    corr_expl = orig_corr[1].strip()
                                    if '(' in corr_expl:
                                        corrected_text = corr_expl.split('(')[0].strip()
                                        explanation = corr_expl.split('(')[1].rstrip(')')
                                    else:
                                        corrected_text = corr_expl
                                        explanation = None
                                    
                                    # Vérifier que c'est une vraie correction (pas juste un titre)
                                    if original_text and corrected_text and original_text != corrected_text:
                                        corrections.append(Correction(
                                            type=corr_type,
                                            original=original_text,
                                            corrected=corrected_text,
                                            explanation=explanation
                                        ))
                    except:
                        pass
            
            # Extraire le résumé (dernières lignes non vides après corrections)
            summary_lines = [l.strip() for l in lines 
                           if l.strip() and not l.startswith(('[CORRECTION:', '- [CORRECTION:', 'Corrections effectuées'))
                           and len(l.strip()) > 20]
            if summary_lines:
                summary = ' '.join(summary_lines[-3:])
        
        return corrected_content, corrections, summary

def main():
    """Test de l'agent de correction"""
    print("=== Test CorrectorAgent ===\n")
    
    from config.domain_configs.personnages_config import PERSONNAGES_CONFIG
    
    agent = CorrectorAgent(PERSONNAGES_CONFIG)
    
    # Contenu de test avec des fautes volontaires
    test_content = """**Nom:** Thélius le Savant
**Alias:** Le Chroniqueure des Ombres
**Type:** PNJ principal
**Occupation:** Historien et archéologue

**Dialogue:**
1. "Les vérité du passé sont souvent plus sombre qu'ont ne le pense."
2. "J'ais découvert des artefact qui change tout ce qu'on savait."
3. "Les Vertèbres du Monde cachent des secret inimaginable."
4. "Parfois, je me demande si certain connaissance devrait resté enterré."

**Background:**
Thélius est un érudit renomé qui à consacré sa vie a l'étude des anciennes civilisation. 
Il parcour le monde à la recherche d'artefacts oubliés, guidé par une curiosité insatiable 
qui le pousse parfois à franchir des limite éthique. Ses découvertes ont révolutionés 
la compréhension de l'histoire d'Alteir, mais certain le considère comme dangereux."""
    
    print(f"Domaine: {agent.domain}\n")
    print("Contenu à corriger:")
    print("-" * 60)
    print(test_content)
    print("-" * 60)
    print("\nCorrection en cours...\n")
    
    result = agent.process(test_content)
    
    if result.success:
        print("=" * 60)
        print("CONTENU CORRIGÉ:")
        print("=" * 60)
        print(result.content)
        
        if result.corrections:
            print(f"\n\nCorrections effectuees ({len(result.corrections)}):")
            for i, corr in enumerate(result.corrections, 1):
                expl = f" ({corr.explanation})" if corr.explanation else ""
                print(f"{i}. [{corr.type}] {corr.original} -> {corr.corrected}{expl}")
        
        if result.improvement_summary:
            print(f"\nResume: {result.improvement_summary}")
        
        print("\n" + "=" * 60)
    else:
        print(f"Erreur: {result.errors}")

if __name__ == "__main__":
    main()

