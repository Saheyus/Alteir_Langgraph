"""
Classes de base pour le système multi-agents
"""
from .base_agent import BaseAgent, AgentResult
from .domain_config import DomainConfig, ValidationRule

__all__ = [
    "BaseAgent",
    "AgentResult", 
    "DomainConfig",
    "ValidationRule"
]

