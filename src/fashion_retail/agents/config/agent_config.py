"""
Agent Configuration

Defines domain metadata and agent parameters.
Implements FR-002 (domain identification) and configuration management.

Configuration values are loaded from:
1. Environment variables (highest priority)
2. Main config.yaml file (for catalog/schema)
3. Default values (lowest priority)
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from ...config import load_config, FashionRetailConfig
from ...constants import AGENT_DEFAULTS


def _get_config_value(key: str, default: Any = None) -> Any:
    """Get configuration value from environment or config file.
    
    Priority:
    1. Environment variable (AGENT_{KEY} or FASHION_RETAIL_{KEY})
    2. Default value from constants
    
    Args:
        key: Configuration key name
        default: Default value if not found
        
    Returns:
        Configuration value
    """
    # Check environment variables first
    env_key = f"AGENT_{key.upper()}"
    env_value = os.environ.get(env_key)
    if env_value is not None:
        return env_value
    
    # Check alternative env var format
    alt_env_key = f"FASHION_RETAIL_{key.upper()}"
    alt_env_value = os.environ.get(alt_env_key)
    if alt_env_value is not None:
        return alt_env_value
    
    # Fall back to default
    return default


def _load_base_config() -> Optional[FashionRetailConfig]:
    """Load base configuration from config.yaml.
    
    Returns:
        FashionRetailConfig or None if file not found
    """
    try:
        return load_config()
    except FileNotFoundError:
        return None


# Load base config once at module import
_BASE_CONFIG = _load_base_config()


@dataclass
class DomainConfig:
    """Configuration for a data domain."""
    name: str
    display_name: str
    description: str
    capabilities: List[str]
    genie_space_id: str
    uc_function_name: str


# Get catalog from config file or environment
_TOOLS_CATALOG = _get_config_value(
    'tools_catalog',
    _BASE_CONFIG.catalog if _BASE_CONFIG else 'juan_use1_catalog'
)

# Domain definitions (FR-002: Identify relevant domains)
DOMAINS = {
    "customer_behavior": DomainConfig(
        name="customer_behavior",
        display_name="Customer Behavior",
        description="Customer purchasing patterns, cart abandonment, segmentation",
        capabilities=[
            "Cart abandonment analysis",
            "Customer segmentation (RFM)",
            "Product affinity",
            "Purchase patterns",
            "Customer lifecycle analysis",
            "Basket analysis"
        ],
        genie_space_id=_get_config_value(
            'customer_behavior_genie_space_id',
            "01f09cdbacf01b5fa7ff7c237365502c"
        ),
        uc_function_name=f"{_TOOLS_CATALOG}.genai.query_customer_behavior_genie"
    ),
    "inventory": DomainConfig(
        name="inventory",
        display_name="Inventory Management",
        description="Stock levels, stockouts, replenishment delays",
        capabilities=[
            "Inventory status",
            "Stockout events",
            "Inventory constraints",
            "Replenishment tracking",
            "Inventory turnover analysis",
            "Supply chain issues"
        ],
        genie_space_id=_get_config_value(
            'inventory_genie_space_id',
            "01f09cdef66116e5940de4b384623be9"
        ),
        uc_function_name=f"{_TOOLS_CATALOG}.genai.query_inventory_genie"
    )
}

# Agent configuration - values from environment, constants, or defaults
AGENT_CONFIG = {
    # Model configuration
    "model_endpoint": _get_config_value(
        'model_endpoint',
        AGENT_DEFAULTS.get('model_endpoint', 'databricks-gpt-5')
    ),
    "temperature": float(_get_config_value(
        'temperature',
        AGENT_DEFAULTS.get('temperature', 0.0)
    )),
    "max_tokens": int(_get_config_value(
        'max_tokens',
        AGENT_DEFAULTS.get('max_tokens', 2000)
    )),

    # Performance constraints (FR-012)
    "timeout_seconds": int(_get_config_value(
        'timeout_seconds',
        AGENT_DEFAULTS.get('timeout_seconds', 60)
    )),

    # Response configuration (FR-013)
    "max_suggestions": int(_get_config_value(
        'max_suggestions',
        AGENT_DEFAULTS.get('max_suggestions', 3)
    )),

    # Conversation configuration (FR-011)
    "max_history_messages": int(_get_config_value(
        'max_history_messages',
        AGENT_DEFAULTS.get('max_history_messages', 20)
    )),

    # Tool configuration - from config file or environment
    "tools_catalog": _TOOLS_CATALOG,
    "tools_schema": _get_config_value('tools_schema', 'genai'),
}


def get_domain_by_name(domain_name: str) -> DomainConfig:
    """
    Get domain configuration by name.

    Args:
        domain_name: Name of the domain (e.g., "customer_behavior")

    Returns:
        DomainConfig object

    Raises:
        ValueError: If domain not found
    """
    if domain_name not in DOMAINS:
        raise ValueError(
            f"Domain '{domain_name}' not found. Available domains: {list(DOMAINS.keys())}"
        )
    return DOMAINS[domain_name]


def list_available_domains() -> List[Dict]:
    """
    List all available data domains for the agent.

    Returns:
        List of domain metadata dictionaries

    Example:
        >>> domains = list_available_domains()
        >>> for domain in domains:
        >>>     print(f"{domain['display_name']}: {domain['description']}")
    """
    return [
        {
            "name": domain.name,
            "display_name": domain.display_name,
            "description": domain.description,
            "capabilities": domain.capabilities
        }
        for domain in DOMAINS.values()
    ]


def get_all_uc_function_names() -> List[str]:
    """
    Get list of all UC Function names for toolkit initialization.

    Returns:
        List of fully-qualified UC Function names

    Example:
        >>> functions = get_all_uc_function_names()
        >>> print(functions)
        ['juan_use1_catalog.genai.query_customer_behavior_genie', 'juan_use1_catalog.genai.query_inventory_genie']
    """
    return [domain.uc_function_name for domain in DOMAINS.values()]

