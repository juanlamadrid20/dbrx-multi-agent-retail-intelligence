"""
Agent configuration modules.

Contains domain definitions, system prompts, and relationship graphs for the agent.
"""

from .agent_config import DomainConfig, DOMAINS, AGENT_CONFIG
from .prompts import SYSTEM_PROMPT, SUGGESTION_PROMPT
from .domain_relationships import DOMAIN_RELATIONSHIPS, get_suggestions_for_domain

__all__ = [
    'DomainConfig',
    'DOMAINS',
    'AGENT_CONFIG',
    'SYSTEM_PROMPT',
    'SUGGESTION_PROMPT',
    'DOMAIN_RELATIONSHIPS',
    'get_suggestions_for_domain',
]
