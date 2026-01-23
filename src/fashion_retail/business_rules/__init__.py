"""
Business Rules Module

Shared business logic for fashion retail data generation.
Used by both batch (FactGenerator) and streaming (medallion pipeline) generators.

This module provides:
- Seasonality calculations
- Pricing and discount logic
- Customer segment behavior
"""

from .seasonality import (
    apply_seasonality_multiplier,
    get_monthly_multiplier,
    is_peak_season,
    SeasonalityContext,
)

from .pricing import (
    calculate_discount,
    get_segment_discount_range,
    determine_discount_type,
    PricingContext,
)

__all__ = [
    # Seasonality
    "apply_seasonality_multiplier",
    "get_monthly_multiplier",
    "is_peak_season",
    "SeasonalityContext",
    # Pricing
    "calculate_discount",
    "get_segment_discount_range",
    "determine_discount_type",
    "PricingContext",
]
