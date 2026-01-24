"""
Inventory Movement Event Generator

Generates synthetic inventory movement events simulating:
- Receipts (inbound from suppliers)
- Transfers (between locations)
- Adjustments (cycle counts, damages, shrinkage)
- Allocations (reserved for orders)

**Self-Contained Design:**
Uses master_data.py as the single source of truth for reference data.
No database connectivity required.
"""

from typing import Any, Dict, List, Optional
from .base_generator import BaseEventGenerator

# Import master data (single source of truth, no DB dependency)
from config.master_data import (
    SKUS, ALL_LOCATION_IDS, STORE_IDS, WAREHOUSE_IDS, DC_IDS,
    PRODUCT_CATALOG, get_product_by_sku
)


class InventoryEventGenerator(BaseEventGenerator):
    """
    Generate inventory movement events.
    
    Uses master_data.py for all reference data.
    
    Example event:
    {
        "movement_id": "INV-20260123-143215-1234",
        "movement_type": "receipt",
        "timestamp": "2026-01-23T14:32:15.123456",
        "location_id": "LOC_001",
        "sku": "SKU_000123",
        "quantity": 50,
        "reason_code": "PO_RECEIPT",
        "reference_id": "PO-2026-00001",
        "cost_per_unit": 25.50
    }
    """
    
    # Movement types with weights
    MOVEMENT_TYPES = [
        ("receipt", 0.30),      # Inbound from suppliers
        ("transfer_in", 0.15),  # Transfer from another location
        ("transfer_out", 0.15), # Transfer to another location
        ("sale", 0.25),         # Sold (decrement)
        ("return", 0.05),       # Customer return
        ("adjustment", 0.10)    # Cycle count, damage, shrinkage
    ]
    
    REASON_CODES = {
        "receipt": ["PO_RECEIPT", "ASN_RECEIPT", "VENDOR_RETURN"],
        "transfer_in": ["STORE_TRANSFER", "DC_REPLENISHMENT", "REBALANCE"],
        "transfer_out": ["STORE_TRANSFER", "DC_RETURN", "REBALANCE"],
        "sale": ["POS_SALE", "ONLINE_SALE", "WHOLESALE"],
        "return": ["CUSTOMER_RETURN", "DEFECTIVE_RETURN", "EXCHANGE"],
        "adjustment": ["CYCLE_COUNT", "DAMAGE", "SHRINKAGE", "FOUND"]
    }
    
    def __init__(
        self,
        volume_path: str,
        batch_size: int = 100,
        random_seed: Optional[int] = None,
        # Override master data if needed
        skus: Optional[List[str]] = None,
        location_ids: Optional[List[str]] = None
    ):
        """
        Initialize inventory generator with master data.
        
        Args:
            volume_path: Path to inventory volume
            batch_size: Movements per batch
            random_seed: Optional seed for reproducibility
            skus: Override SKUs (defaults to master_data.SKUS)
            location_ids: Override location IDs (defaults to master_data.ALL_LOCATION_IDS)
        """
        super().__init__(volume_path, batch_size, random_seed)
        
        # Use master data or overrides
        self.skus = skus or SKUS
        self.location_ids = location_ids or ALL_LOCATION_IDS
        
        # Separate location types for realistic movements
        self.store_ids = STORE_IDS
        self.warehouse_ids = WAREHOUSE_IDS
        self.dc_ids = DC_IDS
        
        # Build product cost lookup from master data
        self._product_costs = {p.sku: p.unit_cost for p in PRODUCT_CATALOG}
        
        self._movement_counter = 0
        self._po_counter = 0
        self._transfer_counter = 0
    
    @property
    def source_name(self) -> str:
        return "inventory"
    
    def _select_movement_type(self) -> str:
        """Select movement type based on weights."""
        r = self.random_float(0, 1)
        cumulative = 0
        for mtype, weight in self.MOVEMENT_TYPES:
            cumulative += weight
            if r <= cumulative:
                return mtype
        return "receipt"
    
    def _get_location_for_movement(self, movement_type: str) -> str:
        """Get appropriate location based on movement type."""
        if movement_type == "receipt":
            # Receipts usually go to warehouses/DCs
            if self.random_bool(0.7) and self.warehouse_ids:
                return self.random_choice(self.warehouse_ids + self.dc_ids)
            return self.random_choice(self.location_ids)
        elif movement_type in ("sale", "return"):
            # Sales/returns happen at stores
            if self.store_ids:
                return self.random_choice(self.store_ids)
            return self.random_choice(self.location_ids)
        else:
            return self.random_choice(self.location_ids)
    
    def generate_event(self) -> Dict[str, Any]:
        """Generate a single inventory movement."""
        self._movement_counter += 1
        
        timestamp = self.current_timestamp()
        movement_type = self._select_movement_type()
        location_id = self._get_location_for_movement(movement_type)
        sku = self.random_choice(self.skus)
        
        # Quantity varies by type
        if movement_type == "receipt":
            quantity = self.random_int(20, 100)
        elif movement_type in ("transfer_in", "transfer_out"):
            quantity = self.random_int(5, 30)
        elif movement_type == "sale":
            quantity = -self.random_int(1, 5)  # Negative for decrements
        elif movement_type == "return":
            quantity = self.random_int(1, 3)
        else:  # adjustment
            quantity = self.random_int(-10, 10)
        
        # Reference ID based on type
        reference_id = None
        if movement_type == "receipt":
            self._po_counter += 1
            reference_id = f"PO-2026-{self._po_counter:05d}"
        elif movement_type in ("transfer_in", "transfer_out"):
            self._transfer_counter += 1
            reference_id = f"TFR-2026-{self._transfer_counter:05d}"
        elif movement_type == "sale":
            reference_id = f"TXN-{timestamp[:10].replace('-', '')}-{self.random_int(1, 99999):05d}"
        
        # Cost per unit from master data
        cost_per_unit = None
        if movement_type in ("receipt", "transfer_in"):
            cost_per_unit = self._product_costs.get(sku, round(self.random_float(10.0, 100.0), 2))
        
        return {
            "movement_id": f"INV-{timestamp[:10].replace('-', '')}-{self._movement_counter:06d}",
            "movement_type": movement_type,
            "timestamp": timestamp,
            "location_id": location_id,
            "sku": sku,
            "quantity": quantity,
            "reason_code": self.random_choice(self.REASON_CODES[movement_type]),
            "reference_id": reference_id,
            "cost_per_unit": cost_per_unit
        }


def create_inventory_generator(
    catalog: str = "juan_dev",
    schema: str = "retail",
    **kwargs
) -> InventoryEventGenerator:
    """
    Create an inventory generator using master data.
    
    No Spark or database connection required.
    
    Args:
        catalog: Unity Catalog name (for volume path)
        schema: Schema name (for volume path)
        **kwargs: Additional arguments for InventoryEventGenerator
        
    Returns:
        Configured InventoryEventGenerator instance
    """
    volume_path = f"/Volumes/{catalog}/{schema}/data/inventory"
    
    return InventoryEventGenerator(volume_path, **kwargs)
