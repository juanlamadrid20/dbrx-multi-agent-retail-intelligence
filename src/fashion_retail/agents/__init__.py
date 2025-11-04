"""
Agent modules for multi-domain retail intelligence.

Contains configuration, Genie utilities, tools, and utilities for the retail intelligence agent.
"""

# Import main modules for convenience
from .config import (
    DomainConfig,
    DOMAINS,
    AGENT_CONFIG,
    SYSTEM_PROMPT,
    SUGGESTION_PROMPT,
    DOMAIN_RELATIONSHIPS,
    get_suggestions_for_domain,
)
from .genie import test_genie_space, test_all_genie_spaces
from .utils import GenieClientError, safe_genie_query

__all__ = [
    # Config exports
    'DomainConfig',
    'DOMAINS',
    'AGENT_CONFIG',
    'SYSTEM_PROMPT',
    'SUGGESTION_PROMPT',
    'DOMAIN_RELATIONSHIPS',
    'get_suggestions_for_domain',
    # Genie exports
    'test_genie_space',
    'test_all_genie_spaces',
    # Utils exports
    'GenieClientError',
    'safe_genie_query',
]

