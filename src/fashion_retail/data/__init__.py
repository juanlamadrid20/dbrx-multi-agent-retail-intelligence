"""Data generation modules for fashion retail analytics.

This package contains modules for generating dimensions, facts, and aggregates
for a comprehensive fashion retail star schema.
"""

__all__ = [
    "DimensionGenerator",
    "FactGenerator", 
    "AggregateGenerator",
]

def __getattr__(name):
    """Lazy import for PySpark-dependent modules."""
    if name == "DimensionGenerator":
        from .dimension_generator import DimensionGenerator
        return DimensionGenerator
    elif name == "FactGenerator":
        from .fact_generator import FactGenerator
        return FactGenerator
    elif name == "AggregateGenerator":
        from .aggregates import AggregateGenerator
        return AggregateGenerator
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
