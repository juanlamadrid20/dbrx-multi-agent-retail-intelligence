"""
Clickstream Event Generator

Generates synthetic web/app clickstream events simulating:
- Page views
- Product views
- Add to cart
- Remove from cart
- Checkout events
- Search queries

**Self-Contained Design:**
Uses master_data.py as the single source of truth for reference data.
No database connectivity required.
"""

from typing import Any, Dict, List, Optional
from .base_generator import BaseEventGenerator

# Import master data (single source of truth, no DB dependency)
from config.master_data import (
    SKUS, CUSTOMER_IDS, ECOMMERCE_CHANNELS, PRODUCT_CATALOG,
    CUSTOMER_SEGMENT_MAP, get_customer_segment
)


class ClickstreamEventGenerator(BaseEventGenerator):
    """
    Generate clickstream events for web and mobile apps.
    
    Uses master_data.py for all reference data.
    
    Example event:
    {
        "event_id": "EVT-20260123-143215-1234",
        "session_id": "sess_abc123def456",
        "event_type": "product_view",
        "timestamp": "2026-01-23T14:32:15.123456",
        "channel": "WEB_DESKTOP",
        "customer_id": "CUST_00000042",
        "page_url": "/product/SKU_000123",
        "product_sku": "SKU_000123",
        "device_type": "desktop",
        "browser": "Chrome",
        "referrer": "google.com"
    }
    """
    
    # Event types with weights (simulating funnel)
    EVENT_TYPES = [
        ("page_view", 0.40),
        ("product_view", 0.25),
        ("add_to_cart", 0.12),
        ("remove_from_cart", 0.03),
        ("begin_checkout", 0.08),
        ("complete_checkout", 0.05),
        ("search", 0.07)
    ]
    
    # Device types by channel
    DEVICE_TYPES = {
        "WEB_DESKTOP": "desktop",
        "WEB_MOBILE": "mobile",
        "APP_IOS": "mobile",
        "APP_ANDROID": "mobile"
    }
    
    # Browsers by channel
    BROWSERS = {
        "WEB_DESKTOP": ["Chrome", "Safari", "Firefox", "Edge"],
        "WEB_MOBILE": ["Chrome Mobile", "Safari Mobile", "Samsung Internet"],
        "APP_IOS": ["iOS App"],
        "APP_ANDROID": ["Android App"]
    }
    
    # Page URLs by event type
    PAGES = {
        "page_view": ["/", "/shop", "/sale", "/new-arrivals", "/about", "/stores"],
        "product_view": None,  # Generated from SKU
        "add_to_cart": None,
        "remove_from_cart": "/cart",
        "begin_checkout": "/checkout",
        "complete_checkout": "/checkout/confirm",
        "search": "/search"
    }
    
    # Referrers
    REFERRERS = [
        None, None, None,  # 30% direct
        "google.com",
        "google.com",
        "facebook.com",
        "instagram.com",
        "pinterest.com",
        "email",
        "bing.com"
    ]
    
    # Search terms
    SEARCH_TERMS = [
        "dress", "jeans", "shoes", "jacket", "sweater",
        "t-shirt", "pants", "skirt", "coat", "boots",
        "summer dress", "black jeans", "running shoes"
    ]
    
    def __init__(
        self,
        volume_path: str,
        batch_size: int = 100,
        random_seed: Optional[int] = None,
        # Override master data if needed
        skus: Optional[List[str]] = None,
        customer_ids: Optional[List[str]] = None,
        channels: Optional[List[str]] = None
    ):
        """
        Initialize clickstream generator with master data.
        
        Args:
            volume_path: Path to clickstream volume
            batch_size: Events per batch
            random_seed: Optional seed for reproducibility
            skus: Override SKUs (defaults to master_data.SKUS)
            customer_ids: Override customer IDs (defaults to master_data.CUSTOMER_IDS)
            channels: Override channels (defaults to master_data.ECOMMERCE_CHANNELS)
        """
        super().__init__(volume_path, batch_size, random_seed)
        
        # Use master data or overrides
        self.skus = skus or SKUS
        self.customer_ids = customer_ids or CUSTOMER_IDS
        self.channels = channels or ECOMMERCE_CHANNELS
        
        self._event_counter = 0
        self._session_counter = 0
    
    @property
    def source_name(self) -> str:
        return "clickstream"
    
    def _select_event_type(self) -> str:
        """Select event type based on weights."""
        r = self.random_float(0, 1)
        cumulative = 0
        for etype, weight in self.EVENT_TYPES:
            cumulative += weight
            if r <= cumulative:
                return etype
        return "page_view"
    
    def _generate_session_id(self) -> str:
        """Generate a session ID."""
        self._session_counter += 1
        return f"sess_{self._session_counter:08d}_{self.random_int(100000, 999999)}"
    
    def generate_event(self) -> Dict[str, Any]:
        """Generate a single clickstream event."""
        self._event_counter += 1
        
        timestamp = self.current_timestamp()
        event_type = self._select_event_type()
        channel = self.random_choice(self.channels)
        
        # Customer (60% logged in for online)
        customer_id = None
        customer_segment = None
        if self.random_bool(0.6):
            customer_id = self.random_choice(self.customer_ids)
            customer_segment = CUSTOMER_SEGMENT_MAP.get(customer_id, 'regular')
        
        # Product SKU for product-related events
        product_sku = None
        if event_type in ("product_view", "add_to_cart"):
            product_sku = self.random_choice(self.skus)
        
        # Page URL
        if event_type == "product_view" and product_sku:
            page_url = f"/product/{product_sku}"
        elif event_type == "add_to_cart" and product_sku:
            page_url = f"/product/{product_sku}"
        elif event_type == "search":
            search_term = self.random_choice(self.SEARCH_TERMS)
            page_url = f"/search?q={search_term.replace(' ', '+')}"
        else:
            pages = self.PAGES.get(event_type, ["/"])
            page_url = self.random_choice(pages) if pages else "/"
        
        # Cart data for cart events
        cart_data = None
        if event_type in ("add_to_cart", "remove_from_cart", "begin_checkout"):
            cart_items = self.random_int(1, 5)
            cart_value = round(self.random_float(25.0, 500.0), 2)
            cart_data = {"items": cart_items, "value": cart_value}
        
        # Device type (handle channels not in predefined dict)
        device_type = self.DEVICE_TYPES.get(channel, "desktop")
        
        # Browser (handle channels not in predefined dict)
        browsers = self.BROWSERS.get(channel, ["Chrome"])
        browser = self.random_choice(browsers)
        
        return {
            "event_id": f"EVT-{timestamp[:10].replace('-', '')}-{self._event_counter:08d}",
            "session_id": self._generate_session_id(),
            "event_type": event_type,
            "timestamp": timestamp,
            "channel": channel,
            "customer_id": customer_id,
            "customer_segment": customer_segment,
            "page_url": page_url,
            "product_sku": product_sku,
            "device_type": device_type,
            "browser": browser,
            "referrer": self.random_choice(self.REFERRERS),
            "cart": cart_data
        }


def create_clickstream_generator(
    catalog: str = "juan_dev",
    schema: str = "retail",
    **kwargs
) -> ClickstreamEventGenerator:
    """
    Create a clickstream generator using master data.
    
    No Spark or database connection required.
    
    Args:
        catalog: Unity Catalog name (for volume path)
        schema: Schema name (for volume path)
        **kwargs: Additional arguments for ClickstreamEventGenerator
        
    Returns:
        Configured ClickstreamEventGenerator instance
    """
    volume_path = f"/Volumes/{catalog}/{schema}/data/clickstream"
    
    return ClickstreamEventGenerator(volume_path, **kwargs)
