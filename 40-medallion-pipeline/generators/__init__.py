# Medallion Pipeline Event Generators
# 
# This package contains event generators that write synthetic
# retail data to Unity Catalog Volumes for Auto Loader ingestion.
#
# **Self-Contained Design:**
# All generators use config/master_data.py as the single source of truth.
# No database connectivity required - generators work standalone.
#
# Generators:
#   - POSEventGenerator: Point-of-sale transactions
#   - EcommerceEventGenerator: Online orders
#   - InventoryEventGenerator: Inventory movements
#   - ClickstreamEventGenerator: Web/app analytics events

__version__ = "0.2.0"

from .base_generator import BaseEventGenerator
from .pos_generator import POSEventGenerator, create_pos_generator
from .ecommerce_generator import EcommerceEventGenerator, create_ecommerce_generator
from .inventory_generator import InventoryEventGenerator, create_inventory_generator
from .clickstream_generator import ClickstreamEventGenerator, create_clickstream_generator

__all__ = [
    # Base
    "BaseEventGenerator",
    # Generators
    "POSEventGenerator",
    "create_pos_generator",
    "EcommerceEventGenerator",
    "create_ecommerce_generator",
    "InventoryEventGenerator",
    "create_inventory_generator",
    "ClickstreamEventGenerator",
    "create_clickstream_generator",
]
