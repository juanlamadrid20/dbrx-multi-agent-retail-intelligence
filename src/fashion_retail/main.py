"""
Fashion Retail Gold Layer Data Generator
Main orchestrator for creating synthetic star schema data in Databricks
"""

import sys
import time
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
from delta.tables import DeltaTable
import logging
from typing import Union, Dict, Any

from .config import FashionRetailConfig
from .data.dimension_generator import DimensionGenerator
from .data.fact_generator import FactGenerator
from .data.aggregates import AggregateGenerator
from .inventory.manager import InventoryManager
from .inventory.validator import SalesValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FashionRetailDataGenerator:
    """Main orchestrator for fashion retail data generation"""
    
    def __init__(self, spark: SparkSession, config: Union[FashionRetailConfig, Dict[str, Any]]):
        self.spark = spark
        
        # Handle both config objects and dictionaries for backward compatibility
        if isinstance(config, dict):
            self.config = config
            self.catalog = config['catalog']
            self.schema = config['schema']
        else:
            self.config = config.to_dict()
            self.catalog = config.catalog
            self.schema = config.schema
        
    def setup_catalog(self):
        """Create catalog and schema if they don't exist"""
        logger.info(f"Setting up catalog: {self.catalog}.{self.schema}")
        
        # Create catalog if not exists
        self.spark.sql(f"CREATE CATALOG IF NOT EXISTS {self.catalog}")
        self.spark.sql(f"USE CATALOG {self.catalog}")
        
        # Create schema with comment
        self.spark.sql(f"""
            CREATE SCHEMA IF NOT EXISTS {self.schema}
            COMMENT 'Fashion Retail Gold Layer - Star Schema for Analytics'
        """)
        self.spark.sql(f"USE SCHEMA {self.schema}")
        
        logger.info("Catalog setup completed")
    
    def drop_existing_tables(self):
        """Drop existing tables if force_recreate is True"""
        if self.config.get('force_recreate', False):
            logger.warning("Dropping existing tables...")
            
            tables = [
                # Dimensions
                'gold_customer_dim',
                'gold_product_dim',
                'gold_location_dim',
                'gold_date_dim',
                'gold_channel_dim',
                'gold_time_dim',
                # Facts
                'gold_sales_fact',
                'gold_inventory_fact',
                'gold_customer_event_fact',
                'gold_cart_abandonment_fact',
                'gold_demand_forecast_fact',
                'gold_stockout_events',  # Added new table
                # Bridge/Aggregates
                'gold_customer_product_affinity_agg',
                'gold_size_fit_bridge',
                'gold_inventory_movement_fact'
            ]
            
            for table in tables:
                try:
                    self.spark.sql(f"DROP TABLE IF EXISTS {self.catalog}.{self.schema}.{table}")
                    logger.info(f"Dropped table: {table}")
                except Exception as e:
                    logger.warning(f"Could not drop table {table}: {str(e)}")
    
    def create_dimensions(self):
        """Create dimension tables"""
        logger.info("Creating dimension tables...")
        
        dim_gen = DimensionGenerator(self.spark, self.config)
        
        # Create dimension tables with Delta features
        dim_gen.create_customer_dimension()
        dim_gen.create_product_dimension()
        dim_gen.create_location_dimension()
        dim_gen.create_date_dimension()
        dim_gen.create_channel_dimension()
        dim_gen.create_time_dimension()
        
        logger.info("Dimension tables created successfully")
    
    def create_facts(self):
        """Create fact tables"""
        logger.info("Creating fact tables...")

        # INVENTORY ALIGNMENT - Feature: 001-i-want-to
        # Initialize InventoryManager and SalesValidator
        logger.info("Initializing inventory alignment components...")

        # Initialize components
        inventory_manager = InventoryManager(self.spark, self.config)
        sales_validator = SalesValidator(inventory_manager, self.config)

        # Initialize inventory positions for all product-location combinations
        # Need to load dimensions first
        products_df = self.spark.table(f"{self.catalog}.{self.schema}.gold_product_dim")
        locations_df = self.spark.table(f"{self.catalog}.{self.schema}.gold_location_dim")

        inventory_manager.initialize_inventory(products_df, locations_df)
        inventory_manager.log_statistics()

        logger.info("Inventory alignment components initialized successfully")

        # Pass inventory components to FactGenerator
        fact_gen = FactGenerator(self.spark, self.config,
                                inventory_manager=inventory_manager,
                                sales_validator=sales_validator)

        # Create fact tables IN ORDER (sales must come before inventory snapshots)
        fact_gen.create_sales_fact()  # Uses SalesValidator
        fact_gen.create_inventory_fact()  # Uses InventoryManager
        fact_gen.create_customer_event_fact()
        fact_gen.create_cart_abandonment_fact()  # Uses SalesValidator for low inventory checks
        fact_gen.create_demand_forecast_fact()

        # NEW: Create stockout events table - Feature: 001-i-want-to
        fact_gen.create_stockout_events()  # Uses InventoryManager history

        # Log final statistics
        logger.info("=" * 60)
        logger.info("FINAL INVENTORY ALIGNMENT STATISTICS")
        inventory_manager.log_statistics()
        sales_validator.log_statistics()
        logger.info("=" * 60)

        logger.info("Fact tables created successfully")
    
    def create_bridge_aggregates(self):
        """Create bridge and aggregate tables"""
        logger.info("Creating bridge and aggregate tables...")
        
        agg_gen = AggregateGenerator(self.spark, self.config)
        
        # Create bridge/aggregate tables
        agg_gen.create_customer_product_affinity()
        agg_gen.create_size_fit_bridge()
        agg_gen.create_inventory_movement_fact()
        
        logger.info("Bridge and aggregate tables created successfully")
    
    def optimize_tables(self):
        """Apply Delta optimizations"""
        logger.info("Applying Delta optimizations...")
        
        # Z-ORDER optimization for fact tables
        z_order_config = self.config.get('z_order_keys', {})
        for table, keys in z_order_config.items():
            try:
                self.spark.sql(f"""
                    OPTIMIZE {self.catalog}.{self.schema}.{table}
                    ZORDER BY ({', '.join(keys)})
                """)
                logger.info(f"Z-ORDER optimization applied to {table}")
            except Exception as e:
                logger.warning(f"Could not optimize {table}: {str(e)}")
        
        # Compute statistics
        tables = self.spark.sql(f"""
            SHOW TABLES IN {self.catalog}.{self.schema}
            LIKE 'gold_*'
        """).collect()
        
        for row in tables:
            table_name = row['tableName']
            self.spark.sql(f"ANALYZE TABLE {self.catalog}.{self.schema}.{table_name} COMPUTE STATISTICS")
            logger.info(f"Statistics computed for {table_name}")
    
    def enable_cdc(self):
        """Enable Change Data Capture on specified tables"""
        if self.config.get('enable_cdc', False):
            logger.info("Enabling CDC on fact tables...")
            
            cdc_tables = [
                'gold_sales_fact',
                'gold_inventory_fact',
                'gold_customer_event_fact'
            ]
            
            for table in cdc_tables:
                try:
                    self.spark.sql(f"""
                        ALTER TABLE {self.catalog}.{self.schema}.{table}
                        SET TBLPROPERTIES (delta.enableChangeDataFeed = true)
                    """)
                    logger.info(f"CDC enabled for {table}")
                except Exception as e:
                    logger.warning(f"Could not enable CDC for {table}: {str(e)}")
    
    def validate_data(self):
        """Run validation queries"""
        logger.info("Running data validation...")
        
        validation_queries = {
            'customer_count': f"SELECT COUNT(*) as cnt FROM {self.catalog}.{self.schema}.gold_customer_dim WHERE is_current = true",
            'product_count': f"SELECT COUNT(*) as cnt FROM {self.catalog}.{self.schema}.gold_product_dim",
            'sales_count': f"SELECT COUNT(*) as cnt FROM {self.catalog}.{self.schema}.gold_sales_fact",
            'inventory_positions': f"SELECT COUNT(DISTINCT product_key, location_key) as cnt FROM {self.catalog}.{self.schema}.gold_inventory_fact",
            'orphan_sales': f"""
                SELECT COUNT(*) as cnt 
                FROM {self.catalog}.{self.schema}.gold_sales_fact s
                LEFT JOIN {self.catalog}.{self.schema}.gold_customer_dim c
                ON s.customer_key = c.customer_key
                WHERE c.customer_key IS NULL
            """
        }
        
        for name, query in validation_queries.items():
            result = self.spark.sql(query).collect()[0]['cnt']
            logger.info(f"Validation - {name}: {result:,}")
    
    def generate_sample_queries(self):
        """Generate sample analytical queries"""
        logger.info("Generating sample queries...")
        
        sample_queries = """
        -- ============================================
        -- SAMPLE ANALYTICAL QUERIES FOR USE CASES
        -- ============================================
        
        -- 1. REAL-TIME PERSONALIZATION
        -- Get personalized product recommendations for a customer
        WITH customer_preferences AS (
            SELECT 
                c.customer_key,
                c.preferred_category,
                c.size_profile_tops,
                c.preferred_channel
            FROM gold_customer_dim c
            WHERE c.is_current = true
                AND c.customer_id = 'SAMPLE_CUSTOMER_ID'
        ),
        recommendations AS (
            SELECT 
                cp.customer_key,
                p.product_name,
                p.category_level_2,
                p.base_price,
                cp.affinity_score,
                cp.predicted_cltv_impact,
                i.quantity_available
            FROM gold_customer_product_affinity_agg cp
            JOIN gold_product_dim p ON cp.product_key = p.product_key
            JOIN gold_inventory_fact i ON p.product_key = i.product_key
            JOIN customer_preferences pref ON cp.customer_key = pref.customer_key
            WHERE cp.affinity_score > 0.7
                AND i.date_key = CURRENT_DATE
                AND i.quantity_available > 0
            ORDER BY cp.affinity_score DESC
            LIMIT 10
        )
        SELECT * FROM recommendations;
        
        -- 2. INVENTORY OPTIMIZATION ACROSS CHANNELS
        -- Identify products needing rebalancing between locations
        WITH inventory_imbalance AS (
            SELECT 
                p.product_id,
                p.product_name,
                l.location_type,
                SUM(i.quantity_on_hand) as total_qty,
                AVG(i.days_of_supply) as avg_days_supply,
                SUM(CASE WHEN i.is_stockout THEN 1 ELSE 0 END) as stockout_locations,
                SUM(CASE WHEN i.is_overstock THEN 1 ELSE 0 END) as overstock_locations
            FROM gold_inventory_fact i
            JOIN gold_product_dim p ON i.product_key = p.product_key
            JOIN gold_location_dim l ON i.location_key = l.location_key
            WHERE i.date_key = CURRENT_DATE
            GROUP BY p.product_id, p.product_name, l.location_type
            HAVING stockout_locations > 0 AND overstock_locations > 0
        )
        SELECT * FROM inventory_imbalance;
        
        -- 3. DEMAND FORECASTING
        -- Compare forecast accuracy and identify products needing model adjustment
        WITH forecast_accuracy AS (
            SELECT 
                p.product_id,
                p.product_name,
                p.category_level_2,
                AVG(f.forecast_accuracy) as avg_accuracy,
                AVG(f.mape) as avg_mape,
                SUM(f.actual_quantity) as total_actual,
                SUM(f.forecast_quantity) as total_forecast,
                COUNT(*) as forecast_count
            FROM gold_demand_forecast_fact f
            JOIN gold_product_dim p ON f.product_key = p.product_key
            JOIN gold_date_dim d ON f.date_key = d.date_key
            WHERE d.calendar_date >= DATE_SUB(CURRENT_DATE, 30)
            GROUP BY p.product_id, p.product_name, p.category_level_2
            HAVING avg_accuracy < 0.80  -- Below 80% accuracy threshold
        )
        SELECT * FROM forecast_accuracy
        ORDER BY avg_accuracy ASC;
        
        -- 4. SIZE/FIT PREDICTION
        -- Analyze size fit patterns for better recommendations
        WITH size_patterns AS (
            SELECT 
                p.product_id,
                p.product_name,
                sf.ordered_size,
                sf.kept_size,
                COUNT(*) as order_count,
                SUM(CASE WHEN sf.is_returned THEN 1 ELSE 0 END) as return_count,
                AVG(sf.fit_score) as avg_fit_score,
                MODE(sf.fit_description) as most_common_feedback
            FROM gold_size_fit_bridge sf
            JOIN gold_product_dim p ON sf.product_key = p.product_key
            GROUP BY p.product_id, p.product_name, sf.ordered_size, sf.kept_size
            HAVING order_count > 10  -- Minimum sample size
        )
        SELECT * FROM size_patterns
        WHERE return_count > order_count * 0.3  -- High return rate
        ORDER BY return_count DESC;
        """
        
        # Save sample queries to a table for reference
        self.spark.sql(f"""
            CREATE OR REPLACE TABLE {self.catalog}.{self.schema}.sample_queries
            (query_text STRING)
            USING DELTA
        """)
        
        logger.info("Sample queries generated - see sample_queries table")
    
    def run(self):
        """Execute the complete data generation pipeline"""
        start_time = time.time()
        logger.info("="*60)
        logger.info("Starting Fashion Retail Data Generation Pipeline")
        logger.info(f"Configuration: {self.config}")
        logger.info("="*60)
        
        try:
            # Setup
            self.setup_catalog()
            self.drop_existing_tables()
            
            # Create tables and generate data
            self.create_dimensions()
            self.create_facts()
            self.create_bridge_aggregates()
            
            # Optimize and enable features
            self.optimize_tables()
            self.enable_cdc()
            
            # Validate
            self.validate_data()
            self.generate_sample_queries()
            
            elapsed_time = time.time() - start_time
            logger.info("="*60)
            logger.info(f"Pipeline completed successfully in {elapsed_time:.2f} seconds")
            logger.info(f"Data available in: {self.catalog}.{self.schema}")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            raise


def main():
    """Main entry point"""
    
    # Initialize Spark session
    spark = SparkSession.builder \
        .appName("Fashion Retail Gold Layer Generator") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .getOrCreate()
    
    # Use new config system
    from .config import get_config
    config = get_config()
    
    # Run generator
    generator = FashionRetailDataGenerator(spark, config)
    generator.run()


if __name__ == "__main__":
    main()
