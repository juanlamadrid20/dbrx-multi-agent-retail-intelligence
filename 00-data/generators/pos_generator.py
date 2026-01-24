"""
POS Transaction Event Generator

Generates synthetic point-of-sale transaction events simulating
retail store registers. Each transaction contains:
- Transaction metadata (ID, store, register, timestamp)
- Customer ID (optional - some transactions are guest checkouts)
- Line items with SKU, quantity, price, discount
- Payment method and sales associate

**Self-Contained Design:**
Uses master_data.py as the single source of truth for reference data.
No database connectivity required - enables:
- Local testing without Databricks
- True raw → bronze → silver → gold flow
- Reproducible data generation
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .base_generator import BaseEventGenerator

# Import master data (single source of truth, no DB dependency)
# master_data.py is now at 00-data/ alongside generators/
from master_data import (
    SKUS, STORE_IDS, CUSTOMER_IDS, PRODUCT_CATALOG,
    CUSTOMER_SEGMENT_MAP, CUSTOMER_SEGMENTS, SEGMENT_DISCOUNT_RANGES,
    get_product_by_sku, get_customer_segment, get_segment_basket_size,
    get_segment_discount, get_seasonality_multiplier, is_sale_period,
    POS_CHANNEL
)


class POSEventGenerator(BaseEventGenerator):
    """
    Generate POS transaction events for retail stores.
    
    Uses master_data.py for all reference data:
    - Product SKUs and prices
    - Store locations
    - Customer IDs and segment assignments
    - Pricing and discount rules
    
    Example event:
    {
        "transaction_id": "TXN-20260123-143215-1234",
        "store_id": "LOC_001",
        "register_id": 3,
        "timestamp": "2026-01-23T14:32:15.123456",
        "customer_id": "CUST_00000042",
        "customer_segment": "premium",
        "items": [
            {"sku": "SKU_000123", "qty": 2, "price": 59.99, "discount": 8.99, "discount_type": "segment"}
        ],
        "payment_method": "credit_card",
        "associate_id": "SA-015"
    }
    """
    
    # Payment methods
    PAYMENT_METHODS = [
        "credit_card",
        "debit_card", 
        "cash",
        "apple_pay",
        "google_pay",
        "gift_card"
    ]
    
    def __init__(
        self,
        volume_path: str,
        batch_size: int = 100,
        random_seed: Optional[int] = None,
        # Historical backfill parameters
        historical_days: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        # Override master data if needed (useful for testing)
        stores: Optional[List[str]] = None,
        skus: Optional[List[str]] = None,
        customer_ids: Optional[List[str]] = None,
        num_associates: int = 100,
        sale_period_override: Optional[bool] = None,
        holiday_override: Optional[bool] = None
    ):
        """
        Initialize POS generator with master data.
        
        Args:
            volume_path: Path to pos volume
            batch_size: Transactions per batch (real-time) or per day (backfill)
            random_seed: Optional seed for reproducibility
            historical_days: Days of historical data to generate (enables backfill mode)
            start_date: Explicit start date for backfill
            end_date: End date for backfill (defaults to today)
            stores: Override store IDs (defaults to master_data.STORE_IDS)
            skus: Override SKUs (defaults to master_data.SKUS)
            customer_ids: Override customer IDs (defaults to master_data.CUSTOMER_IDS)
            num_associates: Number of sales associates
            sale_period_override: Force sale period (auto-detect from date if None)
            holiday_override: Force holiday flag (auto-detect from date if None)
        """
        super().__init__(
            volume_path, 
            batch_size, 
            random_seed,
            historical_days=historical_days,
            start_date=start_date,
            end_date=end_date
        )
        
        # Use master data or overrides
        self.stores = stores or STORE_IDS
        self.skus = skus or SKUS
        self.customer_ids = customer_ids or CUSTOMER_IDS
        
        # Build product price lookup from master data
        self._product_prices = {p.sku: p.base_price for p in PRODUCT_CATALOG}
        
        self.num_associates = num_associates
        self.sale_period_override = sale_period_override
        self.holiday_override = holiday_override
        
        self._txn_counter = 0
    
    def _is_sale_period(self) -> bool:
        """Check if current date is a sale period."""
        if self.sale_period_override is not None:
            return self.sale_period_override
        # Use historical date if in backfill mode, otherwise current date
        check_date = self._current_historical_date or datetime.now()
        return is_sale_period(check_date.month)
    
    def _get_customer_segment(self, customer_id: Optional[str]) -> str:
        """Get segment for customer ID from master data."""
        if customer_id is None:
            return 'regular'  # Guest checkout
        return CUSTOMER_SEGMENT_MAP.get(customer_id, 'regular')
    
    @property
    def source_name(self) -> str:
        return "pos"
    
    def generate_event(self) -> Dict[str, Any]:
        """Generate a single POS transaction."""
        self._txn_counter += 1
        
        timestamp = self.current_timestamp()
        store_id = self.random_choice(self.stores)
        
        # Customer (30% chance of guest checkout)
        customer_id = None
        if self.random_bool(0.7):
            customer_id = self.random_choice(self.customer_ids)
        
        customer_segment = self._get_customer_segment(customer_id)
        
        # Get basket size based on segment
        num_items = get_segment_basket_size(customer_segment, self._rng)
        
        # Generate line items with segment-aware pricing
        items = [
            self._generate_item(customer_segment) 
            for _ in range(num_items)
        ]
        
        return {
            "transaction_id": f"TXN-{timestamp[:10].replace('-', '')}-{self._txn_counter:06d}",
            "store_id": store_id,
            "register_id": self.random_int(1, 5),
            "timestamp": timestamp,
            "customer_id": customer_id,
            "customer_segment": customer_segment,
            "channel_code": POS_CHANNEL,
            "items": items,
            "payment_method": self.random_choice(self.PAYMENT_METHODS),
            "associate_id": f"SA-{self.random_int(1, self.num_associates):03d}"
        }
    
    def _generate_item(self, customer_segment: str) -> Dict[str, Any]:
        """Generate a line item with segment-aware pricing."""
        sku = self.random_choice(self.skus)
        
        # Get base price from master data
        base_price = self._product_prices.get(sku, self.random_float(15.0, 250.0))
        
        # Quantity
        qty = 1
        if self.random_bool(0.2):
            qty = self.random_int(2, 3)
        
        # Calculate discount using segment rules from master data
        discount = 0.0
        discount_type = 'none'
        
        segment_config = CUSTOMER_SEGMENTS.get(customer_segment, CUSTOMER_SEGMENTS['regular'])
        discount_sensitivity = segment_config.get('discount_sensitivity', 0.5)
        
        # Higher sensitivity = more likely to get/need discount
        if self.random_bool(discount_sensitivity):
            # Get discount range for segment
            discount_pct = get_segment_discount(customer_segment, self._rng)
            
            # Determine discount type
            if self._is_sale_period():
                discount_type = 'sale'
                discount_pct = min(discount_pct * 1.2, 0.5)  # Up to 50% during sales
            elif discount_pct > 0.2:
                discount_type = 'clearance'
            else:
                discount_type = 'segment'
            
            discount = round(base_price * discount_pct, 2)
        
        return {
            "sku": sku,
            "qty": qty,
            "price": round(base_price, 2),
            "discount": discount,
            "discount_type": discount_type
        }


def create_pos_generator(
    catalog: Optional[str] = None,
    schema: Optional[str] = None,
    **kwargs
) -> POSEventGenerator:
    """
    Create a POS generator using master data and pipeline config.
    
    No Spark or database connection required.
    
    Args:
        catalog: Unity Catalog name (defaults to config)
        schema: Schema name (defaults to config)
        **kwargs: Additional arguments for POSEventGenerator
        
    Returns:
        Configured POSEventGenerator instance
    """
    from config import get_catalog, get_schema, get_volume_path, get_generator_config
    
    # Use config values if not explicitly provided
    catalog = catalog or get_catalog()
    schema = schema or get_schema()
    
    # Get volume path from config
    volume_path = get_volume_path('pos')
    
    # Get generator-specific config (batch_size, etc.)
    gen_config = get_generator_config('pos')
    if 'batch_size' not in kwargs and 'batch_size' in gen_config:
        kwargs['batch_size'] = gen_config['batch_size']
    
    return POSEventGenerator(volume_path, **kwargs)
