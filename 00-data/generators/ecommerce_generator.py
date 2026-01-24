"""
E-commerce Order Event Generator

Generates synthetic online order events simulating web and app purchases.
Each order contains:
- Order metadata (ID, channel, timestamp)
- Customer ID (required for online orders)
- Shipping address and method
- Line items with SKU, quantity, price, discount
- Payment details

**Self-Contained Design:**
Uses master_data.py as the single source of truth for reference data.
No database connectivity required.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from .base_generator import BaseEventGenerator

# Import master data (single source of truth, no DB dependency)
# master_data.py is now at 00-data/ alongside generators/
from master_data import (
    SKUS, CUSTOMER_IDS, PRODUCT_CATALOG, ECOMMERCE_CHANNELS,
    CUSTOMER_SEGMENT_MAP, CUSTOMER_SEGMENTS, SEGMENT_DISCOUNT_RANGES,
    get_customer_segment, get_segment_basket_size, get_segment_discount,
    is_sale_period
)


class EcommerceEventGenerator(BaseEventGenerator):
    """
    Generate e-commerce order events for online channels.
    
    Uses master_data.py for all reference data.
    
    Example event:
    {
        "order_id": "ORD-20260123-143215-1234",
        "channel": "WEB_DESKTOP",
        "timestamp": "2026-01-23T14:32:15.123456",
        "customer_id": "CUST_00000042",
        "customer_segment": "premium",
        "shipping_address": {...},
        "items": [
            {"sku": "SKU_000123", "qty": 2, "price": 59.99, "discount": 8.99, "discount_type": "segment"}
        ],
        "payment_method": "credit_card",
        "promo_code": "SAVE10"
    }
    """
    
    # Shipping methods
    SHIPPING_METHODS = [
        "standard",
        "express",
        "next_day",
        "pickup"
    ]
    
    # Payment methods for online
    PAYMENT_METHODS = [
        "credit_card",
        "debit_card",
        "paypal",
        "apple_pay",
        "google_pay",
        "affirm",
        "klarna"
    ]
    
    # Promo codes with segment targeting
    PROMO_CODES = {
        'vip': ["VIP25", "EXCLUSIVE30", None],
        'premium': ["PREMIUM20", "SAVE15", None, None],
        'loyal': ["LOYAL15", "SAVE10", None, None, None],
        'regular': ["SAVE10", "WELCOME15", None, None, None, None],
        'new': ["WELCOME15", "FIRSTORDER20", None, None],
    }
    
    # Sample cities/states
    CITIES = [
        ("New York", "NY", "10001"),
        ("Los Angeles", "CA", "90001"),
        ("Chicago", "IL", "60601"),
        ("Houston", "TX", "77001"),
        ("Phoenix", "AZ", "85001"),
        ("Philadelphia", "PA", "19101"),
        ("San Antonio", "TX", "78201"),
        ("San Diego", "CA", "92101"),
        ("Dallas", "TX", "75201"),
        ("San Jose", "CA", "95101"),
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
        # Override master data if needed
        skus: Optional[List[str]] = None,
        customer_ids: Optional[List[str]] = None,
        channels: Optional[List[str]] = None,
        sale_period_override: Optional[bool] = None
    ):
        """
        Initialize e-commerce generator with master data.
        
        Args:
            volume_path: Path to ecommerce volume
            batch_size: Orders per batch (real-time) or per day (backfill)
            random_seed: Optional seed for reproducibility
            historical_days: Days of historical data to generate (enables backfill mode)
            start_date: Explicit start date for backfill
            end_date: End date for backfill (defaults to today)
            skus: Override SKUs (defaults to master_data.SKUS)
            customer_ids: Override customer IDs (defaults to master_data.CUSTOMER_IDS)
            channels: Override channels (defaults to master_data.ECOMMERCE_CHANNELS)
            sale_period_override: Force sale period (auto-detect if None)
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
        self.skus = skus or SKUS
        self.customer_ids = customer_ids or CUSTOMER_IDS
        self.channels = channels or ECOMMERCE_CHANNELS
        
        # Build product price lookup from master data
        self._product_prices = {p.sku: p.base_price for p in PRODUCT_CATALOG}
        
        self.sale_period_override = sale_period_override
        self._order_counter = 0
    
    def _is_sale_period(self) -> bool:
        """Check if current date is a sale period."""
        if self.sale_period_override is not None:
            return self.sale_period_override
        # Use historical date if in backfill mode, otherwise current date
        check_date = self._current_historical_date or datetime.now()
        return is_sale_period(check_date.month)
    
    def _get_customer_segment(self, customer_id: str) -> str:
        """Get segment for customer ID from master data."""
        return CUSTOMER_SEGMENT_MAP.get(customer_id, 'regular')
    
    @property
    def source_name(self) -> str:
        return "ecommerce"
    
    def generate_event(self) -> Dict[str, Any]:
        """Generate a single e-commerce order."""
        self._order_counter += 1
        
        timestamp = self.current_timestamp()
        channel = self.random_choice(self.channels)
        
        # Online orders require logged-in customer
        customer_id = self.random_choice(self.customer_ids)
        customer_segment = self._get_customer_segment(customer_id)
        
        # Shipping address
        city, state, zip_code = self.random_choice(self.CITIES)
        
        # Get segment-appropriate basket size (online tends to be smaller)
        num_items = min(get_segment_basket_size(customer_segment, self._rng), 4)
        
        # Generate items with segment-aware pricing
        items = [
            self._generate_item(customer_segment) 
            for _ in range(num_items)
        ]
        
        # Segment-targeted promo codes
        promo_codes = self.PROMO_CODES.get(customer_segment, [None])
        promo_code = self.random_choice(promo_codes)
        
        return {
            "order_id": f"ORD-{timestamp[:10].replace('-', '')}-{self._order_counter:06d}",
            "channel": channel,
            "timestamp": timestamp,
            "customer_id": customer_id,
            "customer_segment": customer_segment,
            "shipping_address": {
                "city": city,
                "state": state,
                "zip": zip_code
            },
            "shipping_method": self.random_choice(self.SHIPPING_METHODS),
            "items": items,
            "payment_method": self.random_choice(self.PAYMENT_METHODS),
            "promo_code": promo_code
        }
    
    def _generate_item(self, customer_segment: str) -> Dict[str, Any]:
        """Generate a line item with segment-aware pricing."""
        sku = self.random_choice(self.skus)
        
        # Get base price from master data
        base_price = self._product_prices.get(sku, self.random_float(15.0, 250.0))
        
        qty = 1
        if self.random_bool(0.15):
            qty = self.random_int(2, 3)
        
        # Calculate discount using segment rules from master data
        discount = 0.0
        discount_type = 'none'
        
        segment_config = CUSTOMER_SEGMENTS.get(customer_segment, CUSTOMER_SEGMENTS['regular'])
        discount_sensitivity = segment_config.get('discount_sensitivity', 0.5)
        
        if self.random_bool(discount_sensitivity):
            discount_pct = get_segment_discount(customer_segment, self._rng)
            
            if self._is_sale_period():
                discount_type = 'sale'
                discount_pct = min(discount_pct * 1.2, 0.5)
            elif discount_pct > 0.2:
                discount_type = 'clearance'
            else:
                discount_type = 'promo'
            
            discount = round(base_price * discount_pct, 2)
        
        return {
            "sku": sku,
            "qty": qty,
            "price": round(base_price, 2),
            "discount": discount,
            "discount_type": discount_type
        }


def create_ecommerce_generator(
    catalog: Optional[str] = None,
    schema: Optional[str] = None,
    **kwargs
) -> EcommerceEventGenerator:
    """
    Create an e-commerce generator using master data and pipeline config.
    
    No Spark or database connection required.
    
    Args:
        catalog: Unity Catalog name (defaults to config)
        schema: Schema name (defaults to config)
        **kwargs: Additional arguments for EcommerceEventGenerator
        
    Returns:
        Configured EcommerceEventGenerator instance
    """
    from config import get_catalog, get_schema, get_volume_path, get_generator_config
    
    # Use config values if not explicitly provided
    catalog = catalog or get_catalog()
    schema = schema or get_schema()
    
    # Get volume path from config
    volume_path = get_volume_path('ecommerce')
    
    # Get generator-specific config (batch_size, etc.)
    gen_config = get_generator_config('ecommerce')
    if 'batch_size' not in kwargs and 'batch_size' in gen_config:
        kwargs['batch_size'] = gen_config['batch_size']
    
    return EcommerceEventGenerator(volume_path, **kwargs)
