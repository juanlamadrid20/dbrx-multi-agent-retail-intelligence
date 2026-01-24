# Medallion Pipeline Configuration
# 
# This package contains configuration for the streaming medallion pipeline.
#
# Modules:
#   - master_data: Single source of truth for all reference/master data
#   - pipeline_config: Runtime pipeline configuration

from .master_data import (
    # Products
    PRODUCT_CATALOG, SKUS, ACTIVE_SKUS,
    CATEGORIES, BRANDS, COLORS, MATERIALS, SEASONS,
    generate_product_catalog, get_product_by_sku,
    
    # Locations
    LOCATIONS, STORE_IDS, WAREHOUSE_IDS, DC_IDS, ALL_LOCATION_IDS,
    get_location_by_id,
    
    # Channels
    CHANNELS, CHANNEL_CODES, ECOMMERCE_CHANNELS, POS_CHANNEL,
    get_channel_by_code,
    
    # Customers
    CUSTOMER_IDS, CUSTOMER_SEGMENT_MAP, CUSTOMER_SEGMENTS, SEGMENT_DISCOUNT_RANGES,
    generate_customer_ids, generate_customer_segments,
    get_random_customer_segment, get_customer_segment,
    get_segment_basket_size, get_segment_discount,
    
    # Seasonality
    MONTHLY_SEASONALITY, PEAK_SEASON_MONTHS, SALE_PERIODS, HOLIDAYS,
    get_seasonality_multiplier, is_sale_period, is_peak_season,
    
    # Dimension table data
    get_products_for_dimension, get_locations_for_dimension, get_channels_for_dimension,
)

__all__ = [
    # Products
    'PRODUCT_CATALOG', 'SKUS', 'ACTIVE_SKUS',
    'CATEGORIES', 'BRANDS', 'COLORS', 'MATERIALS', 'SEASONS',
    'generate_product_catalog', 'get_product_by_sku',
    
    # Locations
    'LOCATIONS', 'STORE_IDS', 'WAREHOUSE_IDS', 'DC_IDS', 'ALL_LOCATION_IDS',
    'get_location_by_id',
    
    # Channels
    'CHANNELS', 'CHANNEL_CODES', 'ECOMMERCE_CHANNELS', 'POS_CHANNEL',
    'get_channel_by_code',
    
    # Customers
    'CUSTOMER_IDS', 'CUSTOMER_SEGMENT_MAP', 'CUSTOMER_SEGMENTS', 'SEGMENT_DISCOUNT_RANGES',
    'generate_customer_ids', 'generate_customer_segments',
    'get_random_customer_segment', 'get_customer_segment',
    'get_segment_basket_size', 'get_segment_discount',
    
    # Seasonality
    'MONTHLY_SEASONALITY', 'PEAK_SEASON_MONTHS', 'SALE_PERIODS', 'HOLIDAYS',
    'get_seasonality_multiplier', 'is_sale_period', 'is_peak_season',
    
    # Dimension table data
    'get_products_for_dimension', 'get_locations_for_dimension', 'get_channels_for_dimension',
]
