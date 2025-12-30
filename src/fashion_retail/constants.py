"""
Fashion Retail Constants Module

This module contains STATIC CODE CONSTANTS - values that are:
  - Part of business logic (not user-configurable)
  - Referenced programmatically throughout the codebase
  - Rarely change (only when business rules change)

For USER-CONFIGURABLE SETTINGS, see:
  - config.yaml: Runtime configuration (catalog, scale, features)
  - config.py: Loads and validates config.yaml

Examples of what belongs here:
  ✓ Table name lists (used for cleanup, optimization)
  ✓ Customer segment definitions (business logic)
  ✓ Seasonality patterns (retail domain knowledge)
  ✓ Source system mappings (data lineage)

Examples of what does NOT belong here:
  ✗ batch_size (user-configurable in config.yaml)
  ✗ low_inventory_threshold (user-configurable in config.yaml)
  ✗ catalog/schema names (environment-specific)
"""

from typing import Dict, List

# =============================================================================
# Table Definitions
# =============================================================================

# Dimension tables (SCD Type 2 for customer, Type 1 for others)
DIMENSION_TABLES: List[str] = [
    'gold_customer_dim',
    'gold_product_dim',
    'gold_location_dim',
    'gold_date_dim',
    'gold_channel_dim',
    'gold_time_dim',
]

# Fact tables (transactional and snapshot)
FACT_TABLES: List[str] = [
    'gold_sales_fact',
    'gold_inventory_fact',
    'gold_customer_event_fact',
    'gold_cart_abandonment_fact',
    'gold_demand_forecast_fact',
    'gold_stockout_events',
]

# Bridge and aggregate tables
AGGREGATE_TABLES: List[str] = [
    'gold_customer_product_affinity_agg',
    'gold_size_fit_bridge',
    'gold_inventory_movement_fact',
]

# Utility/metadata tables
UTILITY_TABLES: List[str] = [
    'sample_queries',
    '_pipeline_checkpoints',
]

# All tables in the schema
ALL_TABLES: List[str] = DIMENSION_TABLES + FACT_TABLES + AGGREGATE_TABLES + UTILITY_TABLES

# Tables that support CDC (Change Data Capture)
CDC_ENABLED_TABLES: List[str] = [
    'gold_sales_fact',
    'gold_inventory_fact',
    'gold_customer_event_fact',
]

# =============================================================================
# Return Rate Multipliers
# =============================================================================
# Fashion retail return rates vary significantly by channel
# E-commerce: 25-40% return rate (high due to fit uncertainty)
# In-store: 8-10% return rate (customers try before buying)

DIGITAL_RETURN_MULTIPLIER: float = 2.5   # Digital channels have ~2.5x base return rate
STORE_RETURN_MULTIPLIER: float = 0.8     # Physical stores have ~0.8x base return rate

# =============================================================================
# Inventory Defaults by Location Type
# =============================================================================
# Initial inventory quantities when generating synthetic data.
# NOT user-configurable - these represent realistic retail distributions.

INVENTORY_DEFAULTS: Dict[str, Dict[str, int]] = {
    'warehouse': {'min': 100, 'max': 500},
    'store': {'min': 20, 'max': 100},
    'outlet': {'min': 10, 'max': 50},
    'dc': {'min': 200, 'max': 800},  # Distribution center
}

# =============================================================================
# Customer Segment Configuration
# =============================================================================

CUSTOMER_SEGMENTS: Dict[str, Dict] = {
    'vip': {
        'probability': 0.05,  # 5% of customers
        'items_range': [3, 4, 5, 6, 7, 8],
        'discount_probability': 0.15,
        'return_probability': 0.05,
        'lifetime_value_range': (5000, 25000),
    },
    'premium': {
        'probability': 0.15,
        'items_range': [2, 3, 4, 5, 6],
        'discount_probability': 0.25,
        'return_probability': 0.08,
        'lifetime_value_range': (2000, 8000),
    },
    'loyal': {
        'probability': 0.25,
        'items_range': [2, 3, 4, 5],
        'discount_probability': 0.30,
        'return_probability': 0.10,
        'lifetime_value_range': (800, 3000),
    },
    'regular': {
        'probability': 0.35,
        'items_range': [1, 2, 3, 4],
        'discount_probability': 0.35,
        'return_probability': 0.12,
        'lifetime_value_range': (200, 1200),
    },
    'new': {
        'probability': 0.20,
        'items_range': [1, 2, 3],
        'discount_probability': 0.40,
        'return_probability': 0.15,
        'lifetime_value_range': (50, 500),
    },
}

# =============================================================================
# Discount Ranges by Segment
# =============================================================================

SEGMENT_DISCOUNT_RANGES: Dict[str, tuple] = {
    'vip': (0.05, 0.15),
    'premium': (0.08, 0.18),
    'loyal': (0.10, 0.20),
    'regular': (0.12, 0.25),
    'new': (0.15, 0.30),
}

# =============================================================================
# Monthly Seasonality Factors
# =============================================================================
# Multipliers for sales volume by month (1.0 = baseline)

MONTHLY_SEASONALITY: Dict[int, float] = {
    1: 0.7,   # January - Post-holiday slowdown
    2: 0.8,   # February
    3: 1.0,   # March - Spring launch
    4: 1.2,   # April
    5: 1.1,   # May
    6: 1.0,   # June
    7: 0.9,   # July - Summer slowdown
    8: 0.9,   # August
    9: 1.1,   # September - Back to school
    10: 1.2,  # October
    11: 1.5,  # November - Black Friday
    12: 1.8,  # December - Holiday peak
}

# Peak season months for stockout analysis
PEAK_SEASON_MONTHS: List[int] = [11, 12]  # November, December

# =============================================================================
# Processing Thresholds (Code Constants)
# =============================================================================
# These are hard limits used in code, not user-configurable batch sizes.
# For configurable batch_size, see config.yaml.

# Maximum records to accumulate before forcing a write (memory safety)
MAX_RECORDS_BEFORE_WRITE: int = 100_000

# =============================================================================
# Agent Configuration Defaults (Fallback Values)
# =============================================================================
# These defaults are used when environment variables or config.yaml
# don't specify agent settings. They represent safe defaults for
# Databricks-hosted model endpoints.

AGENT_DEFAULTS: Dict[str, any] = {
    'model_endpoint': 'databricks-gpt-5',  # Override via AGENT_MODEL_ENDPOINT env var
    'temperature': 0.0,                     # Deterministic responses for analytics
    'max_tokens': 2000,                     # Sufficient for most queries
    'timeout_seconds': 60,                  # FR-012 requirement
    'max_suggestions': 3,                   # FR-013 requirement  
    'max_history_messages': 20,             # FR-011 conversation context
}

# Genie query timeout - leaves 10s buffer for the 60s overall agent limit
GENIE_QUERY_TIMEOUT_SECONDS: int = 50

# =============================================================================
# Data Source Systems
# =============================================================================

SOURCE_SYSTEMS: Dict[str, str] = {
    'customer': 'CRM_SALESFORCE',
    'product': 'PLM_SYSTEM',
    'location': 'STORE_OPS_WMS',
    'sales': 'OMS_POS_ECOMM',
    'inventory': 'WMS_STORE_INV',
    'events': 'GA4_ADOBE_STORE',
    'cart_abandonment': 'SHOPIFY_MOBILE_APP',
    'forecast': 'ML_PLATFORM_PLANNING',
    'channel': 'CHANNEL_MASTER',
    'stockout': 'synthetic_data_generator',
}

