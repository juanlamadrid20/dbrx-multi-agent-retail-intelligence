# Medallion Pipeline Event Generators
# 
# This package contains event generators that write synthetic
# retail data to Unity Catalog Volumes for Auto Loader ingestion.
#
# **Self-Contained Design:**
# All generators use config/master_data.py as the single source of truth.
# No database connectivity required - generators work standalone.
#
# **Two Operating Modes:**
#   - Real-time: Events generated with current timestamp (default)
#   - Historical Backfill: Events distributed across a date range
#
# Generators:
#   - POSEventGenerator: Point-of-sale transactions
#   - EcommerceEventGenerator: Online orders
#   - InventoryEventGenerator: Inventory movements
#   - ClickstreamEventGenerator: Web/app analytics events
#
# Historical Backfill Usage:
#   generator = POSEventGenerator(
#       volume_path="/Volumes/catalog/schema/pos",
#       batch_size=500,            # Events per day
#       historical_days=90,        # Generate 90 days of history
#       random_seed=42
#   )
#   files = generator.write_historical_batch(dbutils)

__version__ = "0.3.0"

from .base_generator import BaseEventGenerator
from .pos_generator import POSEventGenerator, create_pos_generator
from .ecommerce_generator import EcommerceEventGenerator, create_ecommerce_generator
from .inventory_generator import InventoryEventGenerator, create_inventory_generator
from .clickstream_generator import ClickstreamEventGenerator, create_clickstream_generator
from .dimension_loader import DimensionLoader, create_dimension_loader

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
    # Dimension Loader
    "DimensionLoader",
    "create_dimension_loader",
]
