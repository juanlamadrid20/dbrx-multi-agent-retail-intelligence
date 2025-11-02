"""Fashion Retail Data Generation Package.

A comprehensive package for generating synthetic fashion retail data
with proper inventory alignment and realistic customer behavior patterns.
"""

__version__ = "1.0.0"

# Import config classes (no PySpark dependency)
from .config import FashionRetailConfig, get_config, get_small_config

# Main classes with PySpark dependencies - import on demand
__all__ = [
    "FashionRetailDataGenerator",
    "FashionRetailConfig", 
    "get_config",
    "get_small_config",
    "TableCleanup",
]

def __getattr__(name):
    """Lazy import for PySpark-dependent modules."""
    if name == "FashionRetailDataGenerator":
        from .main import FashionRetailDataGenerator
        return FashionRetailDataGenerator
    elif name == "TableCleanup":
        from .cleanup import TableCleanup
        return TableCleanup
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
