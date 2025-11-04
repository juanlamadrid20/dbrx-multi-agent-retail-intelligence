"""
Domain Relationship Graph

Defines relationships between domains to power proactive suggestions (FR-013).
Helps the agent suggest related queries from complementary data domains.
"""

from typing import Dict, List
import random


# Domain relationship graph for suggestions (FR-013)
DOMAIN_RELATIONSHIPS = {
    "customer_behavior": {
        "related_domains": ["inventory"],
        "suggestion_templates": [
            "Check inventory levels for the products mentioned",
            "View stockout events for these items",
            "Analyze inventory constraints affecting these products",
            "Review replenishment delays for high-abandonment products",
            "Check if inventory issues correlate with cart abandonment patterns"
        ]
    },
    "inventory": {
        "related_domains": ["customer_behavior"],
        "suggestion_templates": [
            "View customer purchase patterns for these products",
            "Analyze cart abandonment for items with low stock",
            "Check customer segments affected by stockouts",
            "Review customer behavior during replenishment delays",
            "Analyze impact of inventory levels on customer satisfaction"
        ]
    }
}


def get_suggestions_for_domain(domain: str, context: str = "", max_suggestions: int = 3) -> List[str]:
    """
    Generate proactive suggestions based on domain and context.

    This function implements FR-013 by suggesting related insights from other domains
    based on the current query's domain.

    Args:
        domain: Current domain being queried (e.g., "customer_behavior")
        context: Optional context from the query (e.g., "cart abandonment")
        max_suggestions: Maximum number of suggestions to return (default: 3)

    Returns:
        List of suggestion strings (up to max_suggestions)

    Example:
        >>> suggestions = get_suggestions_for_domain("customer_behavior", "cart abandonment")
        >>> for s in suggestions:
        >>>     print(f"- {s}")
        - Check inventory levels for the products mentioned
        - View stockout events for these items
    """
    if domain not in DOMAIN_RELATIONSHIPS:
        # If domain not found, provide generic suggestions
        return [
            "Explore data from other available domains",
            "Check for correlations with related data sources"
        ][:max_suggestions]

    relationship = DOMAIN_RELATIONSHIPS[domain]
    templates = relationship["suggestion_templates"]

    # Select up to max_suggestions templates
    # Use random sample to provide variety across multiple queries
    num_suggestions = min(len(templates), max_suggestions)
    selected_templates = random.sample(templates, num_suggestions)

    # TODO: In future, could use context to customize suggestions
    # For now, return templates as-is

    return selected_templates


def get_related_domains(domain: str) -> List[str]:
    """
    Get list of domains related to the given domain.

    Args:
        domain: Domain name (e.g., "customer_behavior")

    Returns:
        List of related domain names

    Example:
        >>> related = get_related_domains("customer_behavior")
        >>> print(related)
        ['inventory']
    """
    if domain not in DOMAIN_RELATIONSHIPS:
        return []

    return DOMAIN_RELATIONSHIPS[domain]["related_domains"]


def get_cross_domain_suggestions(domains_used: List[str], max_suggestions: int = 3) -> List[str]:
    """
    Get suggestions for domains NOT yet queried.

    This is useful after multi-domain queries to suggest additional domains
    that haven't been explored yet.

    Args:
        domains_used: List of domains already queried in conversation
        max_suggestions: Maximum suggestions to return

    Returns:
        List of suggestion strings

    Example:
        >>> suggestions = get_cross_domain_suggestions(["customer_behavior"])
        >>> # Returns suggestions pointing to inventory domain
    """
    all_domains = set(DOMAIN_RELATIONSHIPS.keys())
    used_domains = set(domains_used)
    unused_domains = all_domains - used_domains

    suggestions = []
    for domain in unused_domains:
        if domain in DOMAIN_RELATIONSHIPS:
            templates = DOMAIN_RELATIONSHIPS[domain]["suggestion_templates"]
            # Pick one random suggestion from each unused domain
            if templates:
                suggestions.append(random.choice(templates))

    return suggestions[:max_suggestions]


def format_suggestions(suggestions: List[str]) -> str:
    """
    Format suggestions as a numbered list for agent response.

    Args:
        suggestions: List of suggestion strings

    Returns:
        Formatted string with numbered list

    Example:
        >>> formatted = format_suggestions(["Check inventory", "View stockouts"])
        >>> print(formatted)

        Suggested Next Steps:
        1. Check inventory
        2. View stockouts
    """
    if not suggestions:
        return ""

    formatted = "\n**Suggested Next Steps:**\n"
    for i, suggestion in enumerate(suggestions, 1):
        formatted += f"{i}. {suggestion}\n"

    return formatted

