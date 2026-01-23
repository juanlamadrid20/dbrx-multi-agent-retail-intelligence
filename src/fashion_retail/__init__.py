"""Fashion Retail Data Generation Package.

A comprehensive package for generating synthetic fashion retail data
with proper inventory alignment and realistic customer behavior patterns.

Configuration:
    The package reads configuration from config.yaml at the project root.
    Use load_config() to load the configuration:
    
        from fashion_retail import load_config
        config = load_config()  # Loads config.yaml
        config = load_config("config.small.yaml")  # Load a different preset
"""

__version__ = "1.1.0"

# Main classes with PySpark dependencies - import on demand
__all__ = [
    "FashionRetailDataGenerator",
    "FashionRetailConfig",
    "load_config",
    "get_config",
    "get_small_config",  # Deprecated, use load_config("config.small.yaml")
    "TableCleanup",
    # Constants
    "DIMENSION_TABLES",
    "FACT_TABLES",
    "AGGREGATE_TABLES",
    "ALL_TABLES",
    # Business rules (shared with streaming generators)
    "business_rules",
]

def __getattr__(name):
    """Lazy import for all modules to avoid yaml dependency at import time."""
    if name == "FashionRetailDataGenerator":
        from .main import FashionRetailDataGenerator
        return FashionRetailDataGenerator
    elif name == "TableCleanup":
        from .cleanup import TableCleanup
        return TableCleanup
    elif name in ("DIMENSION_TABLES", "FACT_TABLES", "AGGREGATE_TABLES", "ALL_TABLES"):
        from . import constants
        return getattr(constants, name)
    elif name == "business_rules":
        from . import business_rules
        return business_rules
    elif name in ("FashionRetailConfig", "get_config", "get_small_config", "load_config"):
        # Lazy import config to avoid yaml dependency unless actually needed
        from . import config
        return getattr(config, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
