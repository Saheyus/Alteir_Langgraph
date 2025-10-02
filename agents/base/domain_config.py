#!/usr/bin/env python3
"""
Configuration par domaine pour les agents multi-agents
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from abc import ABC, abstractmethod

@dataclass
class ValidationRule(ABC):
    """Règle de validation abstraite"""
    
    @abstractmethod
    def validate(self, content: Dict[str, Any], context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Valide le contenu selon la règle
        
        Returns:
            (valid, error_message)
        """
        pass

@dataclass
class RequiredFieldRule(ValidationRule):
    """Règle pour champs obligatoires"""
    required_fields: List[str]
    
    def validate(self, content: Dict[str, Any], context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        missing = [f for f in self.required_fields if not content.get(f)]
        if missing:
            return False, f"Champs obligatoires manquants: {', '.join(missing)}"
        return True, None

@dataclass
class CoherenceRule(ValidationRule):
    """Règle de cohérence entre champs"""
    field: str
    related_field: str
    validator: Optional[Callable] = None
    
    def validate(self, content: Dict[str, Any], context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        if self.validator:
            return self.validator(content.get(self.field), content.get(self.related_field))
        return True, None

@dataclass
class RelationRule(ValidationRule):
    """Règle pour les relations avec autres entités"""
    field: str
    context_source: str
    
    def validate(self, content: Dict[str, Any], context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        relations = content.get(self.field, [])
        available = context.get(self.context_source, [])
        
        # Vérifier que les relations existent dans le contexte
        if isinstance(relations, list):
            invalid = [r for r in relations if r not in available]
            if invalid:
                return False, f"Relations invalides dans {self.field}: {', '.join(invalid)}"
        
        return True, None

@dataclass
class DomainConfig:
    """Configuration spécifique à un domaine de contenu"""
    
    # Identité du domaine
    domain: str  # "personnages", "lieux", "communautes", etc.
    display_name: str  # "Personnages", "Lieux", etc.
    
    # Template Notion
    template: Dict[str, Any]
    
    # Instructions spécifiques au domaine
    domain_instructions: str
    
    # Règles de validation
    validation_rules: List[ValidationRule] = field(default_factory=list)
    
    # Sources de contexte Notion (IDs des bases liées)
    context_sources: Dict[str, str] = field(default_factory=dict)
    
    # Exemples de sortie
    examples: List[Dict[str, str]] = field(default_factory=list)
    
    # Paramètres spécifiques au domaine
    specific_params: Dict[str, Any] = field(default_factory=dict)
    
    # Prompts additionnels par rôle d'agent
    role_specific_prompts: Dict[str, str] = field(default_factory=dict)
    
    def get_role_instructions(self, role: str) -> str:
        """Récupère les instructions spécifiques à un rôle pour ce domaine"""
        base = self.domain_instructions
        role_specific = self.role_specific_prompts.get(role, "")
        return f"{base}\n\n{role_specific}" if role_specific else base
    
    def validate(self, content: Dict[str, Any], context: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Valide le contenu selon toutes les règles du domaine
        
        Returns:
            (all_valid, list_of_errors)
        """
        errors = []
        for rule in self.validation_rules:
            valid, error = rule.validate(content, context)
            if not valid and error:
                errors.append(error)
        
        return len(errors) == 0, errors
    
    def get_context_source_ids(self) -> List[str]:
        """Retourne les IDs des sources de contexte"""
        return list(self.context_sources.values())
    
    def get_template_fields(self) -> List[str]:
        """Retourne la liste des champs du template"""
        return list(self.template.keys())
    
    def get_required_fields(self) -> List[str]:
        """Retourne les champs obligatoires basés sur les règles"""
        required = []
        for rule in self.validation_rules:
            if isinstance(rule, RequiredFieldRule):
                required.extend(rule.required_fields)
        return list(set(required))

# Factory pour créer des configs de domaine courantes
class DomainConfigFactory:
    """Factory pour créer des configurations de domaine"""
    
    @staticmethod
    def create_personnages_config() -> DomainConfig:
        """Crée la configuration pour le domaine Personnages"""
        from config.domain_configs.personnages_config import PERSONNAGES_CONFIG
        return PERSONNAGES_CONFIG
    
    @staticmethod
    def create_lieux_config() -> DomainConfig:
        """Crée la configuration pour le domaine Lieux"""
        from config.domain_configs.lieux_config import LIEUX_CONFIG
        return LIEUX_CONFIG
    
    @staticmethod
    def get_config(domain: str) -> DomainConfig:
        """Récupère la configuration pour un domaine donné"""
        configs = {
            "personnages": DomainConfigFactory.create_personnages_config,
            "lieux": DomainConfigFactory.create_lieux_config,
            # Ajoutez d'autres domaines ici
        }
        
        if domain not in configs:
            raise ValueError(f"Domaine inconnu: {domain}. Domaines disponibles: {list(configs.keys())}")
        
        return configs[domain]()

