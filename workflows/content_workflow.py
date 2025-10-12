#!/usr/bin/env python3
"""
Workflow complet pour la création de contenu
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict, Iterator, Tuple

# Ajouter le répertoire racine au path
sys.path.append(str(Path(__file__).parent.parent))

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from agents.writer_agent import WriterAgent, WriterConfig
from agents.reviewer_agent import ReviewerAgent
from agents.corrector_agent import CorrectorAgent
from agents.validator_agent import ValidatorAgent
from agents.base.domain_config import DomainConfig

class WorkflowState(TypedDict):
    """État partagé du workflow"""
    # Identité
    domain: str
    brief: str
    
    # Contenu à travers les étapes
    content: str
    
    # Métadonnées de chaque agent
    writer_metadata: Dict[str, Any]
    reviewer_metadata: Dict[str, Any]
    corrector_metadata: Dict[str, Any]
    validator_metadata: Dict[str, Any]
    
    # Résultats intermédiaires
    review_issues: List[Dict]
    corrections: List[Dict]
    validation_errors: List[Dict]
    
    # Scores
    coherence_score: float
    completeness_score: float
    quality_score: float
    
    # Statut final
    is_valid: bool
    ready_for_publication: bool
    
    # Contexte Notion
    context: Dict[str, Any]
    
    # Historique
    history: List[Dict[str, str]]

class ContentWorkflow:
    """
    Workflow complet de création de contenu
    
    Étapes : Writer → Reviewer → Corrector → Validator → (Publish)
    """
    
    def __init__(self, domain_config: DomainConfig, llm: ChatOpenAI = None):
        """
        Initialise le workflow
        
        Args:
            domain_config: Configuration du domaine
            llm: Modèle LLM optionnel
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.domain_config = domain_config
        self.llm = llm or self._create_default_llm()

        # Créer les agents
        self.writer = WriterAgent(domain_config, llm=self.llm)
        self.reviewer = ReviewerAgent(domain_config, llm=self.llm)
        self.corrector = CorrectorAgent(domain_config, llm=self.llm)
        self.validator = ValidatorAgent(domain_config, llm=self.llm)

        # Construire le graphe
        self.graph = self._build_graph()
        self.app = self.graph.compile()
        self.logger.info("Workflow initialisé pour le domaine %s", domain_config.display_name)
    
    def _create_default_llm(self) -> ChatOpenAI:
        """Crée un LLM par défaut"""
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=2000,
        )
    
    def _build_graph(self) -> StateGraph:
        """Construit le graphe LangGraph"""
        graph = StateGraph(WorkflowState)
        
        # Ajouter les nœuds
        graph.add_node("writer", self._writer_node)
        graph.add_node("reviewer", self._reviewer_node)
        graph.add_node("corrector", self._corrector_node)
        graph.add_node("validator", self._validator_node)
        
        # Définir les arêtes
        graph.set_entry_point("writer")
        graph.add_edge("writer", "reviewer")
        graph.add_edge("reviewer", "corrector")
        graph.add_edge("corrector", "validator")
        graph.add_edge("validator", END)
        
        return graph
    
    def _writer_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Nœud Writer"""
        self.logger.info("WRITER → génération du contenu (%s)", state["brief"][:80])

        result = self.writer.process(state["brief"], state.get("context"))

        if not result.success:
            self.logger.error("Échec de la génération initiale: %s", "; ".join(result.errors))
        else:
            self.logger.debug(
                "Contenu généré (%d caractères)",
                len(result.content),
            )
        
        history_entry = {
            "step": "writer",
            "timestamp": datetime.now().isoformat(),
            "summary": f"Contenu genere ({len(result.content)} chars)"
        }
        
        return {
            "content": result.content,
            "writer_metadata": result.metadata,
            "history": state.get("history", []) + [history_entry]
        }
    
    def _reviewer_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Nœud Reviewer"""
        self.logger.info("REVIEWER → analyse de la cohérence")

        result = self.reviewer.process(state["content"], state.get("context"))

        if not result.success:
            self.logger.error("Échec de la relecture: %s", "; ".join(result.errors))
        else:
            self.logger.debug(
                "Relecture terminée: %d problèmes identifiés", len(result.issues)
            )
        
        history_entry = {
            "step": "reviewer",
            "timestamp": datetime.now().isoformat(),
            "summary": f"Score coherence: {result.coherence_score:.2f}, {len(result.issues)} problemes"
        }
        
        return {
            "content": result.content,
            "reviewer_metadata": result.metadata,
            "review_issues": [vars(issue) for issue in result.issues],
            "coherence_score": result.coherence_score,
            "history": state.get("history", []) + [history_entry]
        }
    
    def _corrector_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Nœud Corrector"""
        self.logger.info("CORRECTOR → correction du contenu")

        result = self.corrector.process(state["content"], state.get("context"))

        if not result.success:
            self.logger.error("Échec de la correction: %s", "; ".join(result.errors))
        else:
            self.logger.debug(
                "Corrections appliquées: %d", len(result.corrections)
            )
        
        history_entry = {
            "step": "corrector",
            "timestamp": datetime.now().isoformat(),
            "summary": f"{len(result.corrections)} corrections effectuees"
        }
        
        return {
            "content": result.content,
            "corrector_metadata": result.metadata,
            "corrections": [vars(corr) for corr in result.corrections],
            "history": state.get("history", []) + [history_entry]
        }
    
    def _validator_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Nœud Validator"""
        self.logger.info("VALIDATOR → validation finale")

        result = self.validator.process(state["content"], state.get("context"))

        if not result.success:
            self.logger.error("Échec de la validation finale: %s", "; ".join(result.errors))
        else:
            self.logger.debug(
                "Validation: is_valid=%s | ready=%s",
                result.is_valid,
                result.ready_for_publication,
            )
        
        history_entry = {
            "step": "validator",
            "timestamp": datetime.now().isoformat(),
            "summary": f"Valide: {result.is_valid}, Publication: {result.ready_for_publication}"
        }
        
        return {
            "validator_metadata": result.metadata,
            "validation_errors": [vars(err) for err in result.validation_errors],
            "completeness_score": result.completeness_score,
            "quality_score": result.quality_score,
            "is_valid": result.is_valid,
            "ready_for_publication": result.ready_for_publication,
            "history": state.get("history", []) + [history_entry]
        }
    
    def run(self, brief: str, writer_config: WriterConfig = None, context: Dict[str, Any] = None) -> WorkflowState:
        """
        Exécute le workflow complet
        
        Args:
            brief: Description du contenu à créer
            writer_config: Configuration additionnelle pour le writer
            context: Contexte Notion optionnel
            
        Returns:
            État final du workflow
        """
        # Initialiser l'état
        initial_state: WorkflowState = {
            "domain": self.domain_config.domain,
            "brief": brief,
            "content": "",
            "writer_metadata": {},
            "reviewer_metadata": {},
            "corrector_metadata": {},
            "validator_metadata": {},
            "review_issues": [],
            "corrections": [],
            "validation_errors": [],
            "coherence_score": 0.0,
            "completeness_score": 0.0,
            "quality_score": 0.0,
            "is_valid": False,
            "ready_for_publication": False,
            "context": context or self.writer.gather_context(),
            "history": []
        }
        
        # Si writer_config fourni, mettre à jour l'agent
        if writer_config:
            self.writer.writer_config = writer_config
        
        # Exécuter le workflow
        self.logger.info(
            "Démarrage du workflow %s",
            self.domain_config.display_name,
        )
        self.logger.debug("Brief: %s", brief)

        final_state = self.app.invoke(initial_state)

        self.logger.info("Workflow terminé pour %s", self.domain_config.display_name)

        return final_state

    def run_iter(self, brief: str, writer_config: WriterConfig = None, context: Dict[str, Any] = None) -> Iterator[Tuple[str, WorkflowState]]:
        """
        Exécute le workflow étape par étape et yield l'état après chaque nœud.

        Args:
            brief: Description du contenu à créer
            writer_config: Configuration additionnelle pour le writer
            context: Contexte Notion optionnel

        Yields:
            Tuples (step_name, state) après chaque étape: "writer", "reviewer", "corrector", "validator".
        """
        # Initialiser l'état (même logique que run)
        state: WorkflowState = {
            "domain": self.domain_config.domain,
            "brief": brief,
            "content": "",
            "writer_metadata": {},
            "reviewer_metadata": {},
            "corrector_metadata": {},
            "validator_metadata": {},
            "review_issues": [],
            "corrections": [],
            "validation_errors": [],
            "coherence_score": 0.0,
            "completeness_score": 0.0,
            "quality_score": 0.0,
            "is_valid": False,
            "ready_for_publication": False,
            "context": context or self.writer.gather_context(),
            "history": []
        }

        if writer_config:
            self.writer.writer_config = writer_config

        self.logger.info(
            "Démarrage (itératif) du workflow %s",
            self.domain_config.display_name,
        )

        # Étape: Writer
        delta = self._writer_node(state)
        state.update(delta)
        yield ("writer", state)

        # Étape: Reviewer
        delta = self._reviewer_node(state)
        state.update(delta)
        yield ("reviewer", state)

        # Étape: Corrector
        delta = self._corrector_node(state)
        state.update(delta)
        yield ("corrector", state)

        # Étape: Validator
        delta = self._validator_node(state)
        state.update(delta)
        yield ("validator", state)
    
    def run_iter_live(
        self,
        brief: str,
        writer_config: WriterConfig = None,
        context: Dict[str, Any] = None,
        include_reasoning: bool = False,
    ) -> Iterator[Tuple[str, Any]]:
        """Runs the workflow and streams token deltas per step.
        Yields tuples (event, payload):
          - "writer:start" | None
          - "writer:delta" | {"text", "reasoning"?}
          - "writer:done"  | WorkflowState
        And similarly for other steps: reviewer, corrector, validator.
        """
        state: WorkflowState = {
            "domain": self.domain_config.domain,
            "brief": brief,
            "content": "",
            "writer_metadata": {},
            "reviewer_metadata": {},
            "corrector_metadata": {},
            "validator_metadata": {},
            "review_issues": [],
            "corrections": [],
            "validation_errors": [],
            "coherence_score": 0.0,
            "completeness_score": 0.0,
            "quality_score": 0.0,
            "is_valid": False,
            "ready_for_publication": False,
            "context": context or self.writer.gather_context(),
            "history": [],
        }

        if writer_config:
            self.writer.writer_config = writer_config

        # Writer
        yield ("writer:start", None)
        writer_result = None
        try:
            gen = self.writer.process_stream(brief, context=state.get("context"), include_reasoning=include_reasoning)
            while True:
                try:
                    delta = next(gen)
                    yield ("writer:delta", delta)
                except StopIteration as stop:
                    writer_result = stop.value
                    break
        except Exception:
            # Already logged inside agent; fallback will be handled below
            writer_result = None
        if writer_result is None:
            writer_result = self.writer.process(brief, state.get("context"))
        # Robust fallback: if streaming returned but content is empty, retry non-streaming once
        try:
            if (getattr(writer_result, "content", None) is None) or (not str(getattr(writer_result, "content", "")).strip()):
                self.logger.warning("Writer streaming produced empty content; retrying non-streaming invoke")
                writer_result = self.writer.process(brief, state.get("context"))
        except Exception:
            pass
        # Update state (mirror _writer_node without re-invoking model)
        history_entry = {
            "step": "writer",
            "timestamp": datetime.now().isoformat(),
            "summary": f"Contenu genere ({len(writer_result.content)} chars)",
        }
        state.update({
            "content": writer_result.content,
            "writer_metadata": writer_result.metadata,
            "history": state.get("history", []) + [history_entry],
        })
        yield ("writer:done", state)

        # Reviewer
        yield ("reviewer:start", None)
        reviewer_result = None
        try:
            gen = self.reviewer.process_stream(state["content"], context=state.get("context"), include_reasoning=include_reasoning)
            while True:
                try:
                    delta = next(gen)
                    yield ("reviewer:delta", delta)
                except StopIteration as stop:
                    reviewer_result = stop.value
                    break
        except Exception:
            reviewer_result = None
        if reviewer_result is None:
            reviewer_result = self.reviewer.process(state["content"], state.get("context"))
        history_entry = {
            "step": "reviewer",
            "timestamp": datetime.now().isoformat(),
            "summary": f"Score coherence: {getattr(reviewer_result, 'coherence_score', 0.0):.2f}, {len(getattr(reviewer_result, 'issues', []))} problemes",
        }
        state.update({
            "content": reviewer_result.content,
            "reviewer_metadata": reviewer_result.metadata,
            "review_issues": [vars(issue) for issue in getattr(reviewer_result, 'issues', [])],
            "coherence_score": float(getattr(reviewer_result, 'coherence_score', 0.0)),
            "history": state.get("history", []) + [history_entry],
        })
        yield ("reviewer:done", state)

        # Corrector
        yield ("corrector:start", None)
        corrector_result = None
        try:
            gen = self.corrector.process_stream(state["content"], context=state.get("context"), include_reasoning=include_reasoning)
            while True:
                try:
                    delta = next(gen)
                    yield ("corrector:delta", delta)
                except StopIteration as stop:
                    corrector_result = stop.value
                    break
        except Exception:
            corrector_result = None
        if corrector_result is None:
            corrector_result = self.corrector.process(state["content"], state.get("context"))
        history_entry = {
            "step": "corrector",
            "timestamp": datetime.now().isoformat(),
            "summary": f"{len(getattr(corrector_result, 'corrections', []))} corrections effectuees",
        }
        state.update({
            "content": corrector_result.content,
            "corrector_metadata": corrector_result.metadata,
            "corrections": [vars(c) for c in getattr(corrector_result, 'corrections', [])],
            "history": state.get("history", []) + [history_entry],
        })
        yield ("corrector:done", state)

        # Validator
        yield ("validator:start", None)
        validator_result = None
        try:
            gen = self.validator.process_stream(state["content"], context=state.get("context"), include_reasoning=include_reasoning)
            while True:
                try:
                    delta = next(gen)
                    yield ("validator:delta", delta)
                except StopIteration as stop:
                    validator_result = stop.value
                    break
        except Exception:
            validator_result = None
        if validator_result is None:
            validator_result = self.validator.process(state["content"], state.get("context"))
        history_entry = {
            "step": "validator",
            "timestamp": datetime.now().isoformat(),
            "summary": f"Valide: {getattr(validator_result, 'is_valid', False)}, Publication: {getattr(validator_result, 'ready_for_publication', False)}",
        }
        state.update({
            "validator_metadata": validator_result.metadata,
            "validation_errors": [vars(e) for e in getattr(validator_result, 'validation_errors', [])],
            "completeness_score": float(getattr(validator_result, 'completeness_score', 0.0)),
            "quality_score": float(getattr(validator_result, 'quality_score', 0.0)),
            "is_valid": bool(getattr(validator_result, 'is_valid', False)),
            "ready_for_publication": bool(getattr(validator_result, 'ready_for_publication', False)),
            "history": state.get("history", []) + [history_entry],
        })
        yield ("validator:done", state)
    
    def save_results(self, state: WorkflowState, output_dir: str = "outputs"):
        """
        Sauvegarde les résultats du workflow
        
        Args:
            state: État final du workflow
            output_dir: Répertoire de sortie
        """
        import re
        import unicodedata
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Timestamp pour le nom de fichier
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Extraire le nom de la fiche pour le nom de fichier
        content = state.get('content', '')
        name_match = re.search(r'^-?\s*Nom:\s*(.+)$', content, re.MULTILINE)
        
        if name_match:
            # Nom trouvé - convertir en camelCase sans accents
            name = name_match.group(1).strip()
            # Supprimer les accents
            name_no_accent = ''.join(c for c in unicodedata.normalize('NFD', name) 
                                     if unicodedata.category(c) != 'Mn')
            # Convertir en camelCase
            words = re.split(r'[\s\-\']+', name_no_accent)
            camel_case = words[0].lower() + ''.join(w.capitalize() for w in words[1:] if w)
            # Supprimer caractères non alphanumériques
            camel_case = re.sub(r'[^a-zA-Z0-9]', '', camel_case)
            # Format: domaine_nomCamelCase_timestamp
            filename_base = f"{state['domain']}_{camel_case}"
        else:
            # Nom non trouvé - utiliser domaine par défaut
            filename_base = state['domain']
        
        # Sauvegarder le JSON complet
        json_file = output_path / f"{filename_base}_{timestamp}.json"
        # Ensure JSON-serializable (convert any unexpected objects)
        def _sanitize(obj):
            try:
                json.dumps(obj)
                return obj
            except Exception:
                if isinstance(obj, dict):
                    return {k: _sanitize(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [_sanitize(x) for x in obj]
                return str(obj)

        safe_state = _sanitize(state)
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(safe_state, f, indent=2, ensure_ascii=False)
        
        # Sauvegarder le contenu en Markdown
        md_file = output_path / f"{filename_base}_{timestamp}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            # Utiliser le nom de la fiche si disponible, sinon le domaine
            title = name if name_match else state['domain'].capitalize()
            f.write(f"# {title}\n\n")
            f.write(f"**Brief:** {state['brief']}\n\n")
            f.write(f"---\n\n")
            f.write(f"## Contenu Final\n\n")
            f.write(state["content"])
            f.write(f"\n\n---\n\n")
            f.write(f"## Métriques\n\n")
            f.write(f"- Score de cohérence: {state['coherence_score']:.2f}\n")
            f.write(f"- Score de complétude: {state['completeness_score']:.2f}\n")
            f.write(f"- Score de qualité: {state['quality_score']:.2f}\n")
            f.write(f"- Valide: {state['is_valid']}\n")
            f.write(f"- Prêt pour publication: {state['ready_for_publication']}\n")
            
            if state["review_issues"]:
                f.write(f"\n## Problèmes Identifiés ({len(state['review_issues'])})\n\n")
                for i, issue in enumerate(state["review_issues"], 1):
                    f.write(f"{i}. [{issue['severity']}] {issue['description']}\n")
            
            if state["corrections"]:
                f.write(f"\n## Corrections ({len(state['corrections'])})\n\n")
                for i, corr in enumerate(state["corrections"], 1):
                    f.write(f"{i}. [{corr['type']}] {corr['original']} -> {corr['corrected']}\n")
            
            if state["validation_errors"]:
                f.write(f"\n## Erreurs de Validation ({len(state['validation_errors'])})\n\n")
                for i, err in enumerate(state["validation_errors"], 1):
                    f.write(f"{i}. [{err['severity']}] {err['field']}: {err['description']}\n")
        
        self.logger.info("Résultats sauvegardés | json=%s | markdown=%s", json_file, md_file)
        try:
            # Log a concise summary for quick inspection
            content_len = len(state.get("content", ""))
            num_issues = len(state.get("review_issues", []) or [])
            num_corrections = len(state.get("corrections", []) or [])
            ctx_pages = len((state.get("context") or {}).get("pages", []) or [])
            ctx_tokens = (state.get("context") or {}).get("token_estimate")
            model_used = state.get("model_used")
            model_cfg = state.get("model_config") or {}
            verbosity = None
            # Try to surface verbosity from model kwargs (Responses API) or runtime
            try:
                verbosity = ((model_cfg.get("model_kwargs") or {}).get("verbosity")) or ((model_cfg.get("runtime") or {}).get("verbosity"))
            except Exception:
                verbosity = None

            self.logger.info(
                "OUTPUT SUMMARY | domain=%s | chars=%d | issues=%d | corrections=%d | scores=(coh=%.2f, comp=%.2f, qual=%.2f) | model=%s | reasoning=%s | verbosity=%s | ctx_pages=%d | ctx_tokens=%s",
                state.get("domain"),
                content_len,
                num_issues,
                num_corrections,
                float(state.get("coherence_score", 0.0)),
                float(state.get("completeness_score", 0.0)),
                float(state.get("quality_score", 0.0)),
                model_used,
                (model_cfg.get("default_reasoning") or (state.get("reasoning_effort") if hasattr(state, "get") else None)),
                verbosity,
                ctx_pages,
                ctx_tokens,
            )
        except Exception:
            # Never fail saving due to logging
            pass

        return json_file, md_file

def main():
    """Démo du workflow complet"""
    from config.domain_configs.personnages_config import PERSONNAGES_CONFIG
    
    # Créer le workflow
    workflow = ContentWorkflow(PERSONNAGES_CONFIG)
    
    # Exécuter avec un brief
    brief = """Un alchimiste qui transforme les émotions en substances physiques.
    Genre: Non défini. Espèce: Humain modifié. Âge: 38 cycles.
    Membre d'une guilde secrète, cache une dépendance à ses propres créations."""
    
    writer_config = WriterConfig(
        intent="orthogonal_depth",
        level="standard",
        dialogue_mode="parle",
        creativity=0.8
    )
    
    # Exécuter
    final_state = workflow.run(brief, writer_config)
    
    # Afficher résumé
    print("\n" + "="*60)
    print("RESUME DU WORKFLOW")
    print("="*60)
    print(f"\nDomaine: {final_state['domain']}")
    print(f"Brief: {final_state['brief'][:80]}...")
    print(f"\nScores:")
    print(f"  - Coherence: {final_state['coherence_score']:.2f}")
    print(f"  - Completude: {final_state['completeness_score']:.2f}")
    print(f"  - Qualite: {final_state['quality_score']:.2f}")
    print(f"\nStatut:")
    print(f"  - Valide: {final_state['is_valid']}")
    print(f"  - Pret publication: {final_state['ready_for_publication']}")
    print(f"\nProblemes: {len(final_state['review_issues'])}")
    print(f"Corrections: {len(final_state['corrections'])}")
    print(f"Erreurs validation: {len(final_state['validation_errors'])}")
    
    # Sauvegarder
    workflow.save_results(final_state)

if __name__ == "__main__":
    main()

