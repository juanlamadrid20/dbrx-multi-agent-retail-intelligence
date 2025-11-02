"""
Agent Configuration

Defines domain metadata and agent parameters.
Implements FR-002 (domain identification) and configuration management.
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class DomainConfig:
    """Configuration for a data domain"""
    name: str
    display_name: str
    description: str
    capabilities: List[str]
    genie_space_id: str
    uc_function_name: str


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
        genie_space_id="01f0b7572b3a185d9f69cd89bc4c7579",  # TODO: Set actual space ID
        uc_function_name="juan_dev.genai.query_customer_behavior_genie"
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
        genie_space_id="01f09cdef66116e5940de4b384623be9",  # TODO: Set actual space ID
        uc_function_name="juan_dev.genai.query_inventory_genie"
    )
}

# Agent configuration
AGENT_CONFIG = {
    # Model configuration
    "model_endpoint": "databricks-gpt-5", 
    "temperature": 0.0,  # Deterministic for consistent responses
    "max_tokens": 2000,

    # Performance constraints (FR-012)
    "timeout_seconds": 60,  # Must respond within 60 seconds

    # Response configuration (FR-013)
    "max_suggestions": 3,  # Max 3 proactive suggestions per response

    # Conversation configuration (FR-011)
    "max_history_messages": 20,  # Keep last 20 messages in context

    # Tool configuration
    "tools_catalog": "juan_dev",
    "tools_schema": "genai",
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
        ['juan_dev.genai.query_customer_behavior_genie', 'juan_dev.genai.query_inventory_genie']
    """
    return [domain.uc_function_name for domain in DOMAINS.values()]
