"""Inventory management and alignment modules.

This package contains modules for managing inventory state, validating sales
against available inventory, and generating stockout events.
"""

__all__ = [
    "InventoryManager",
    "SalesValidator",
    "StockoutGenerator",
]

def __getattr__(name):
    """Lazy import for PySpark-dependent modules."""
    if name == "InventoryManager":
        from .manager import InventoryManager
        return InventoryManager
    elif name == "SalesValidator":
        from .validator import SalesValidator
        return SalesValidator
    elif name == "StockoutGenerator":
        from .stockout_generator import StockoutGenerator
        return StockoutGenerator
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
