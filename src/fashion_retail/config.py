"""Configuration management for Fashion Retail data generation pipeline.

This module provides configuration loading from YAML files and validation
via the FashionRetailConfig dataclass.

Usage:
    from fashion_retail.config import load_config
    
    # Load from default config.yaml at project root
    config = load_config()
    
    # Load from a specific file
    config = load_config("config.small.yaml")
    
    # Programmatic overrides still work
    config = load_config(catalog="my_catalog", schema="my_schema")
"""

import os
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml


def _find_config_file(filename: str = "config.yaml") -> Path:
    """Find the config file, searching from current directory up to project root.
    
    Args:
        filename: Name of the config file to find
        
    Returns:
        Path to the config file
        
    Raises:
        FileNotFoundError: If config file cannot be found
    """
    # First, check if it's an absolute path or exists in current directory
    if os.path.isabs(filename):
        path = Path(filename)
        if path.exists():
            return path
        raise FileNotFoundError(f"Config file not found: {filename}")
    
    # Search from current directory upward
    current = Path.cwd()
    
    # Check current directory and parent directories
    for parent in [current] + list(current.parents):
        candidate = parent / filename
        if candidate.exists():
            return candidate
        
        # Stop at common project root indicators
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            # Check one more time at the project root
            if candidate.exists():
                return candidate
            break
    
    # Also check relative to this file's location (for package imports)
    package_root = Path(__file__).parent.parent.parent  # src/fashion_retail -> project root
    candidate = package_root / filename
    if candidate.exists():
        return candidate
    
    raise FileNotFoundError(
        f"Config file '{filename}' not found. "
        f"Searched from {current} up to project root. "
        f"Create a config.yaml at your project root or specify an absolute path."
    )


def _load_yaml(path: Path) -> Dict[str, Any]:
    """Load and parse a YAML file.
    
    Args:
        path: Path to the YAML file
        
    Returns:
        Dictionary of configuration values
    """
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    return data if data else {}


def _convert_return_delay_days(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert return_delay_days from YAML format to tuple format.
    
    YAML format:
        return_delay_days:
          min: 1
          max: 3
          
    Tuple format:
        return_delay_days: (1, 3)
    """
    if 'return_delay_days' in data:
        rdd = data['return_delay_days']
        if isinstance(rdd, dict):
            data['return_delay_days'] = (rdd.get('min', 1), rdd.get('max', 3))
    return data


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

    def __post_init__(self):
        """Validate configuration parameters after initialization."""
        # Validate scale parameters
        if self.customers <= 0:
            raise ValueError(f"customers must be positive, got {self.customers}")
        if self.products <= 0:
            raise ValueError(f"products must be positive, got {self.products}")
        if self.locations <= 0:
            raise ValueError(f"locations must be positive, got {self.locations}")
        if self.historical_days <= 0:
            raise ValueError(f"historical_days must be positive, got {self.historical_days}")
        if self.events_per_day < 0:
            raise ValueError(f"events_per_day must be non-negative, got {self.events_per_day}")
        
        # Validate inventory alignment parameters
        if not 0 < self.target_stockout_rate < 1:
            raise ValueError(f"target_stockout_rate must be between 0 and 1, got {self.target_stockout_rate}")
        if not 0 <= self.cart_abandonment_increase < 1:
            raise ValueError(f"cart_abandonment_increase must be between 0 and 1, got {self.cart_abandonment_increase}")
        if self.low_inventory_threshold < 0:
            raise ValueError(f"low_inventory_threshold must be non-negative, got {self.low_inventory_threshold}")
        
        # Validate return_delay_days tuple
        if len(self.return_delay_days) != 2:
            raise ValueError(f"return_delay_days must be a tuple of 2 integers, got {self.return_delay_days}")
        if self.return_delay_days[0] < 0 or self.return_delay_days[1] < 0:
            raise ValueError(f"return_delay_days values must be non-negative, got {self.return_delay_days}")
        if self.return_delay_days[0] > self.return_delay_days[1]:
            raise ValueError(f"return_delay_days[0] must be <= return_delay_days[1], got {self.return_delay_days}")
        
        # Validate catalog and schema names (basic validation)
        if not self.catalog or not self.catalog.strip():
            raise ValueError("catalog name cannot be empty")
        if not self.schema or not self.schema.strip():
            raise ValueError("schema name cannot be empty")

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


def load_config(
    path: str = "config.yaml",
    **overrides
) -> FashionRetailConfig:
    """Load configuration from a YAML file.
    
    Args:
        path: Path to the YAML config file. Defaults to "config.yaml".
              Can be an absolute path or a filename to search for.
        **overrides: Keyword arguments to override values from the YAML file.
        
    Returns:
        FashionRetailConfig: Validated configuration object
        
    Raises:
        FileNotFoundError: If the config file cannot be found
        ValueError: If configuration validation fails
        
    Example:
        # Load default config
        config = load_config()
        
        # Load with overrides
        config = load_config(catalog="test_catalog", historical_days=30)
        
        # Load from specific file
        config = load_config("config.small.yaml")
    """
    config_path = _find_config_file(path)
    data = _load_yaml(config_path)
    
    # Convert YAML-specific formats
    data = _convert_return_delay_days(data)
    
    # Apply overrides
    data.update(overrides)
    
    return FashionRetailConfig(**data)


def get_config(
    catalog: Optional[str] = None,
    schema: Optional[str] = None,
    **kwargs
) -> FashionRetailConfig:
    """Get configuration, loading from config.yaml with optional overrides.
    
    This function loads from config.yaml and applies any provided overrides.
    For full control, use load_config() directly.
    
    Args:
        catalog: Override the catalog name
        schema: Override the schema name
        **kwargs: Additional overrides for any config parameter
        
    Returns:
        FashionRetailConfig: Validated configuration object
    """
    overrides = {}
    
    if catalog is not None:
        overrides['catalog'] = catalog
    if schema is not None:
        overrides['schema'] = schema
    
    overrides.update(kwargs)
    
    try:
        return load_config(**overrides)
    except FileNotFoundError:
        # Fall back to defaults if no config file exists
        warnings.warn(
            "config.yaml not found, using default configuration. "
            "Create a config.yaml at your project root for customization.",
            UserWarning
        )
        return FashionRetailConfig(**overrides)


def get_small_config() -> FashionRetailConfig:
    """Get a smaller configuration for testing/development.
    
    .. deprecated::
        Use `load_config("config.small.yaml")` instead, or copy 
        config.small.yaml to config.yaml.
    
    Note: The locations parameter is fixed at 13 regardless of this value.
    See dimension_generator.py for details.
    """
    warnings.warn(
        "get_small_config() is deprecated. Use load_config('config.small.yaml') instead, "
        "or copy config.small.yaml to config.yaml.",
        DeprecationWarning,
        stacklevel=2
    )
    try:
        return load_config("config.small.yaml")
    except FileNotFoundError:
        # Fall back to hardcoded values for backward compatibility
        return FashionRetailConfig(
            customers=50_000,
            products=2_000,
            locations=13,
            historical_days=90,
            events_per_day=100,
        )
