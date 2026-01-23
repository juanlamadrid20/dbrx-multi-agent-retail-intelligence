"""
Dimension Data Loader

Loads actual values from dimension tables to ensure generated events
align with existing dimension data for proper joins.

This module provides utilities to:
1. Load dimension values from Unity Catalog tables
2. Cache values for efficient generator access
3. Provide fallback static values for local testing

Usage:
    # In Databricks notebook:
    loader = DimensionLoader(spark, catalog="juan_dev", schema="retail")
    loader.load_all()
    
    # Get values for generators
    skus = loader.get_skus()
    store_ids = loader.get_store_ids()
    customer_ids = loader.get_customer_ids()
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class DimensionData:
    """Container for dimension data loaded from tables."""
    
    # Product dimension
    skus: List[str] = field(default_factory=list)
    products: List[Dict[str, Any]] = field(default_factory=list)
    
    # Location dimension (stores only)
    store_ids: List[str] = field(default_factory=list)
    locations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Customer dimension
    customer_ids: List[str] = field(default_factory=list)
    
    # Channel dimension
    channel_codes: List[str] = field(default_factory=list)
    pos_channel_code: str = "STORE_POS"


class DimensionLoader:
    """
    Loads dimension data from Unity Catalog tables.
    
    Attributes:
        spark: SparkSession
        catalog: Unity Catalog name
        schema: Schema/database name
        data: DimensionData container
    """
    
    def __init__(self, spark=None, catalog: str = "juan_dev", schema: str = "retail"):
        """
        Initialize dimension loader.
        
        Args:
            spark: SparkSession (optional, uses static data if None)
            catalog: Unity Catalog name
            schema: Schema/database name
        """
        self.spark = spark
        self.catalog = catalog
        self.schema = schema
        self.data = DimensionData()
        self._loaded = False
    
    def load_all(self) -> "DimensionLoader":
        """Load all dimension data from tables."""
        if self.spark is None:
            self._load_static_data()
        else:
            self._load_from_tables()
        self._loaded = True
        return self
    
    def _load_from_tables(self) -> None:
        """Load dimension data from Unity Catalog tables."""
        # Load products (SKUs)
        products_df = self.spark.sql(f"""
            SELECT sku, product_key, product_name, base_price, unit_cost,
                   category_level_1, brand
            FROM {self.catalog}.{self.schema}.gold_product_dim
            WHERE sku IS NOT NULL
        """)
        
        self.data.skus = [row.sku for row in products_df.select("sku").collect()]
        self.data.products = [row.asDict() for row in products_df.collect()]
        
        # Load locations (stores only)
        locations_df = self.spark.sql(f"""
            SELECT location_id, location_key, location_name, location_type,
                   store_format, city, state_province, 
                   COALESCE(state_tax_rate, 0.07) as state_tax_rate
            FROM {self.catalog}.{self.schema}.gold_location_dim
            WHERE location_type = 'store' AND is_active = true
        """)
        
        self.data.store_ids = [row.location_id for row in locations_df.select("location_id").collect()]
        self.data.locations = [row.asDict() for row in locations_df.collect()]
        
        # Load customers
        customers_df = self.spark.sql(f"""
            SELECT customer_id
            FROM {self.catalog}.{self.schema}.gold_customer_dim
            WHERE is_current = true
            LIMIT 10000
        """)
        
        self.data.customer_ids = [row.customer_id for row in customers_df.collect()]
        
        # Load channels
        channels_df = self.spark.sql(f"""
            SELECT channel_code
            FROM {self.catalog}.{self.schema}.gold_channel_dim
        """)
        
        self.data.channel_codes = [row.channel_code for row in channels_df.collect()]
        
        # Verify POS channel exists
        if "STORE_POS" in self.data.channel_codes:
            self.data.pos_channel_code = "STORE_POS"
    
    def _load_static_data(self) -> None:
        """Load static fallback data for local testing."""
        # Static SKUs matching dimension format
        self.data.skus = [f"SKU_{i:06d}" for i in range(1, 501)]
        
        # Static store IDs matching dimension format
        self.data.store_ids = [f"LOC_{i:03d}" for i in range(1, 11)]
        
        # Static customer IDs matching dimension format
        self.data.customer_ids = [f"CUST_{i:08d}" for i in range(1, 1001)]
        
        # Static channel codes
        self.data.channel_codes = [
            "WEB_DESKTOP", "WEB_MOBILE", "APP_IOS", "APP_ANDROID",
            "STORE_POS", "STORE_KIOSK", "SOCIAL_FB", "MARKETPLACE_AMAZON"
        ]
        self.data.pos_channel_code = "STORE_POS"
    
    # Accessor methods for generators
    
    def get_skus(self, limit: Optional[int] = None) -> List[str]:
        """Get list of valid SKUs."""
        if not self._loaded:
            self.load_all()
        return self.data.skus[:limit] if limit else self.data.skus
    
    def get_store_ids(self) -> List[str]:
        """Get list of valid store IDs."""
        if not self._loaded:
            self.load_all()
        return self.data.store_ids
    
    def get_customer_ids(self, limit: Optional[int] = None) -> List[str]:
        """Get list of valid customer IDs."""
        if not self._loaded:
            self.load_all()
        return self.data.customer_ids[:limit] if limit else self.data.customer_ids
    
    def get_channel_codes(self) -> List[str]:
        """Get list of valid channel codes."""
        if not self._loaded:
            self.load_all()
        return self.data.channel_codes
    
    def get_pos_channel_code(self) -> str:
        """Get the POS channel code."""
        if not self._loaded:
            self.load_all()
        return self.data.pos_channel_code
    
    def get_products(self) -> List[Dict[str, Any]]:
        """Get full product records with pricing info."""
        if not self._loaded:
            self.load_all()
        return self.data.products
    
    def get_locations(self) -> List[Dict[str, Any]]:
        """Get full location records with details."""
        if not self._loaded:
            self.load_all()
        return self.data.locations
    
    def summary(self) -> str:
        """Return summary of loaded dimension data."""
        if not self._loaded:
            return "Dimensions not loaded. Call load_all() first."
        
        return f"""
Dimension Data Summary:
=======================
Products (SKUs):    {len(self.data.skus):,}
Store Locations:    {len(self.data.store_ids):,}
Customers:          {len(self.data.customer_ids):,}
Channel Codes:      {len(self.data.channel_codes):,}
POS Channel:        {self.data.pos_channel_code}

Sample SKUs:        {self.data.skus[:3]}
Sample Store IDs:   {self.data.store_ids[:3]}
Sample Customer IDs: {self.data.customer_ids[:3]}
"""


# Factory function for convenience
def create_dimension_loader(spark=None, catalog: str = "juan_dev", schema: str = "retail") -> DimensionLoader:
    """
    Create and load a DimensionLoader.
    
    Args:
        spark: SparkSession (optional)
        catalog: Unity Catalog name
        schema: Schema name
        
    Returns:
        Loaded DimensionLoader instance
    """
    return DimensionLoader(spark, catalog, schema).load_all()
