"""Configuration management for Fashion Retail data generation pipeline."""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional


@dataclass
class FashionRetailConfig:
    """Configuration for the Fashion Retail data generation pipeline."""

    # Environment configuration
    catalog: str = "juan_dev"
    schema: str = "retail"
    force_recreate: bool = True

    # Scale parameters
    customers: int = 100_000
    products: int = 10_000
    locations: int = 13
    historical_days: int = 730
    events_per_day: int = 500_000

    # Features
    enable_cdc: bool = True
    enable_liquid_clustering: bool = True

    # Optimization configuration
    z_order_keys: Dict[str, List[str]] = field(default_factory=lambda: {
        'gold_sales_fact': ['date_key', 'product_key'],
        'gold_inventory_fact': ['product_key', 'location_key'],
        'gold_customer_event_fact': ['date_key', 'customer_key']
    })

    # Inventory alignment parameters (Feature: 001-i-want-to)
    random_seed: int = 42
    target_stockout_rate: float = 0.075  # Target 7.5% stockout rate (midpoint of 5-10%)
    cart_abandonment_increase: float = 0.10  # +10 percentage points for low inventory
    return_delay_days: Tuple[int, int] = (1, 3)  # Returns replenish inventory 1-3 days later
    low_inventory_threshold: int = 5  # Trigger cart abandonment increase when qty < 5

    @property
    def full_schema_name(self) -> str:
        """Full schema name for table references."""
        return f"{self.catalog}.{self.schema}"

    def to_dict(self) -> Dict:
        """Convert config to dictionary for backward compatibility."""
        return {
            'catalog': self.catalog,
            'schema': self.schema,
            'force_recreate': self.force_recreate,
            'customers': self.customers,
            'products': self.products,
            'locations': self.locations,
            'historical_days': self.historical_days,
            'events_per_day': self.events_per_day,
            'enable_cdc': self.enable_cdc,
            'enable_liquid_clustering': self.enable_liquid_clustering,
            'z_order_keys': self.z_order_keys,
            'random_seed': self.random_seed,
            'target_stockout_rate': self.target_stockout_rate,
            'cart_abandonment_increase': self.cart_abandonment_increase,
            'return_delay_days': self.return_delay_days,
            'low_inventory_threshold': self.low_inventory_threshold,
        }


def get_config(
    catalog: Optional[str] = None,
    schema: Optional[str] = None,
    **kwargs
) -> FashionRetailConfig:
    """Get the fashion retail configuration with optional overrides."""
    config_kwargs = {}
    
    if catalog is not None:
        config_kwargs['catalog'] = catalog
    if schema is not None:
        config_kwargs['schema'] = schema
    
    # Add any additional keyword arguments
    config_kwargs.update(kwargs)
    
    return FashionRetailConfig(**config_kwargs)


def get_small_config() -> FashionRetailConfig:
    """Get a smaller configuration for testing/development.
    
    Note: The locations parameter is fixed at 13 regardless of this value.
    See dimension_generator.py for details.
    """
    return FashionRetailConfig(
        customers=50_000,
        products=2_000,
        locations=13,  # Fixed at 13 in implementation (10 stores, 2 warehouses, 1 DC)
        historical_days=90,
        events_per_day=100,
    )
