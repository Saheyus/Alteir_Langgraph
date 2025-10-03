#!/usr/bin/env python3
"""
Classe de base pour tous les agents du système multi-agents
"""
import logging
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI

# Ajouter le répertoire racine au path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config.notion_config import NotionConfig
from agents.base.domain_config import DomainConfig

@dataclass
class AgentResult:
    """Résultat d'un agent"""
    success: bool
    content: str
    metadata: Dict[str, Any]
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class BaseAgent(ABC):
    """
    Classe abstraite de base pour tous les agents
    
    Tous les agents héritent de cette classe et implémentent:
    - process(): méthode principale de traitement
    - Accès au contexte Notion via MCP
    - Construction de prompts avec spécificités du domaine
    """
    
    # Prompt de base commun à tous les agents (à surcharger dans les sous-classes)
    BASE_PROMPT = """Tu es un agent expert du système multi-agents pour le GDD Alteir."""
    
    def __init__(self, domain_config: DomainConfig, llm: ChatOpenAI = None):
        """
        Initialise l'agent avec une configuration de domaine
        
        Args:
            domain_config: Configuration spécifique au domaine
            llm: Modèle LLM optionnel (créé par défaut si non fourni)
        """
        self.domain_config = domain_config
        self.domain = domain_config.domain
        self.template = domain_config.template
        self.validation_rules = domain_config.validation_rules
        self.context_sources = domain_config.context_sources

        # LLM
        self.llm = llm or self._create_default_llm()

        # Config Notion
        self.notion_config = NotionConfig()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.debug("Agent initialisé pour le domaine %s", self.domain)
    
    def _create_default_llm(self) -> ChatOpenAI:
        """Crée un LLM par défaut avec des paramètres standards"""
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=2000,
        )
    
    @abstractmethod
    def process(self, input_data: Any, context: Dict[str, Any]) -> AgentResult:
        """
        Méthode principale à implémenter par chaque agent
        
        Args:
            input_data: Données d'entrée (peut varier selon l'agent)
            context: Contexte Notion et autres données
            
        Returns:
            AgentResult avec le résultat du traitement
        """
        pass
    
    def gather_context(self) -> Dict[str, Any]:
        """
        Récupère le contexte depuis Notion pour ce domaine
        
        Returns:
            Dictionnaire de contexte avec les données des sources liées
        """
        context = {
            "domain": self.domain,
            "template_fields": self.domain_config.get_template_fields(),
            "required_fields": self.domain_config.get_required_fields(),
        }

        # TODO: Implémenter la récupération réelle via MCP
        # Pour l'instant, retourner un contexte simulé
        simulated_context = self._get_simulated_context()
        context.update(simulated_context)
        self.logger.debug(
            "Contexte récupéré pour %s (sources: %s)",
            self.domain,
            ", ".join(sorted(simulated_context.keys())),
        )

        return context
    
    def _get_simulated_context(self) -> Dict[str, Any]:
        """Contexte simulé (à remplacer par vrais appels MCP)"""
        # Sera remplacé par de vrais appels MCP fetch/search
        return {
            "especes": ["Humain modifié", "Croc d'Améthyste", "Gedroth"],
            "lieux": ["Le Léviathan Pétrifié", "La Vieille", "Les Vertèbres du Monde"],
            "communautes": ["Les Cartographes", "La Guilde des Enlumineurs"],
        }
    
    def _build_system_prompt(self, role_name: str) -> str:
        """
        Construit le prompt système avec spécificités du domaine
        
        Args:
            role_name: Nom du rôle (writer, reviewer, corrector, validator)
            
        Returns:
            Prompt système complet
        """
        # Prompt de base de la classe
        base_prompt = self.BASE_PROMPT
        
        # Instructions du domaine pour ce rôle
        domain_instructions = self.domain_config.get_role_instructions(role_name)
        
        # Contexte du template
        template_info = f"""
**TEMPLATE {self.domain_config.display_name.upper()}:**
Champs disponibles: {', '.join(self.domain_config.get_template_fields())}
Champs obligatoires: {', '.join(self.domain_config.get_required_fields())}
"""
        
        return f"""{base_prompt}

**DOMAINE:** {self.domain_config.display_name}
{template_info}

**INSTRUCTIONS DU DOMAINE:**
{domain_instructions}
"""
    
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
    
    def validate_output(self, content: Dict[str, Any], context: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Valide le contenu selon les règles du domaine
        
        Args:
            content: Contenu à valider
            context: Contexte pour la validation
            
        Returns:
            (valid, errors)
        """
        valid, errors = self.domain_config.validate(content, context)
        if valid:
            self.logger.debug("Validation réussie pour %s", self.domain)
        else:
            self.logger.warning("Validation échouée (%d erreurs)", len(errors))
        return valid, errors
    
    def get_role_name(self) -> str:
        """Retourne le nom du rôle de l'agent (à surcharger)"""
        return self.__class__.__name__.lower().replace("agent", "")

