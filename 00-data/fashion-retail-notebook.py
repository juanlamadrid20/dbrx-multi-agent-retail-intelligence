# Databricks notebook source
# MAGIC %md
# MAGIC # Fashion Retail Gold Layer Data Generation
# MAGIC
# MAGIC This notebook orchestrates the execution of the Python modules to generate synthetic fashion retail data.
# MAGIC
# MAGIC ## Prerequisites:
# MAGIC 1. Upload these Python files to the same directory as this notebook:
# MAGIC    - `fashion-retail-main.py`
# MAGIC    - `fashion-retail-dimension-generator.py`
# MAGIC    - `fashion-retail-fact-generator.py`
# MAGIC    - `fashion-retail-aggregates.py`
# MAGIC    - `inventory_manager.py` **(NEW - Feature: 001-i-want-to)**
# MAGIC    - `sales_validator.py` **(NEW - Feature: 001-i-want-to)**
# MAGIC    - `stockout_generator.py` **(NEW - Feature: 001-i-want-to)**
# MAGIC
# MAGIC 2. All files should be in the same folder for easy access

# COMMAND ----------

# MAGIC %md
# MAGIC ## Option 1: Import and Run the Main Orchestrator

# COMMAND ----------

import sys
import os

# For Databricks notebooks, use current working directory or explicit path
# Option 1: Use current working directory (if files are uploaded to the same location)
module_path = os.getcwd()

# Option 2: If you need a specific path, uncomment and modify this line:
# module_path = "/Workspace/Users/your_email@domain.com/path/to/files"

print(f"Looking for modules in: {module_path}")
print(f"Files in directory: {os.listdir(module_path) if os.path.exists(module_path) else 'Directory not found'}")

# Import the main module and generators
import importlib.util
import sys

# Load modules dynamically to handle hyphenated filenames
def load_module_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Load the modules from the same directory
fashion_retail_main = load_module_from_file("fashion_retail_main", os.path.join(module_path, "fashion-retail-main.py"))
fashion_retail_dimension_generator = load_module_from_file("fashion_retail_dimension_generator", os.path.join(module_path, "fashion-retail-dimension-generator.py"))
fashion_retail_fact_generator = load_module_from_file("fashion_retail_fact_generator", os.path.join(module_path, "fashion-retail-fact-generator.py"))
fashion_retail_aggregates = load_module_from_file("fashion_retail_aggregates", os.path.join(module_path, "fashion-retail-aggregates.py"))

# NEW: Load inventory alignment modules - Feature: 001-i-want-to
inventory_manager = load_module_from_file("inventory_manager", os.path.join(module_path, "inventory_manager.py"))
sales_validator = load_module_from_file("sales_validator", os.path.join(module_path, "sales_validator.py"))
stockout_generator = load_module_from_file("stockout_generator", os.path.join(module_path, "stockout_generator.py"))

# Import the classes
FashionRetailDataGenerator = fashion_retail_main.FashionRetailDataGenerator
DimensionGenerator = fashion_retail_dimension_generator.DimensionGenerator
FactGenerator = fashion_retail_fact_generator.FactGenerator
AggregateGenerator = fashion_retail_aggregates.AggregateGenerator
InventoryManager = inventory_manager.InventoryManager
SalesValidator = sales_validator.SalesValidator
StockoutGenerator = stockout_generator.StockoutGenerator

# COMMAND ----------

# Configuration - same as in main.py
config = {
    'catalog': 'juan_dev',
    'schema': 'retail',
    'force_recreate': True,

    # Scale parameters - small for testing (increase once pipeline works)
    'customers': 50_000,        # Start with 50K customers
    'products': 2_000,          # Start with 2K products
    'locations': 25,            # 25 locations
    'historical_days': 90,      # 90 days of history
    'events_per_day': 100,      # 100 events per day

    # Features
    'enable_cdc': True,
    'enable_liquid_clustering': True,

    # Optimization
    'z_order_keys': {
        'gold_sales_fact': ['date_key', 'product_key'],
        'gold_inventory_fact': ['product_key', 'location_key'],
        'gold_customer_event_fact': ['date_key', 'customer_key']
    },

    # NEW: Inventory alignment parameters (Feature: 001-i-want-to)
    'random_seed': 42,  # For reproducible data generation
    'target_stockout_rate': 0.075,  # Target 7.5% stockout rate (midpoint of 5-10%)
    'cart_abandonment_increase': 0.10,  # +10 percentage points for low inventory
    'return_delay_days': (1, 3),  # Returns replenish inventory 1-3 days later
    'low_inventory_threshold': 5,  # Trigger cart abandonment increase when qty < 5
}

print(f"Configuration loaded for: {config['catalog']}.{config['schema']}")
print(f"Full scale: {config['customers']:,} customers, {config['products']:,} products")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Option 2: Direct Module Execution (Recommended for Databricks)
# MAGIC
# MAGIC If importing doesn't work (common in Databricks), use %run magic command instead

# COMMAND ----------

# Alternative: Use %run to execute the Python files directly from the same directory
# This is often more reliable in Databricks - uncomment these lines and comment out the import section above

# %run "./fashion-retail-main"
# %run "./fashion-retail-dimension-generator"
# %run "./fashion-retail-fact-generator"
# %run "./fashion-retail-aggregates"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Execute the Full Pipeline

# COMMAND ----------

# Initialize the generator with current Spark session
generator = FashionRetailDataGenerator(spark, config)

# Run the complete pipeline
try:
    print("Starting Fashion Retail Data Generation Pipeline...")
    print("=" * 60)
    
    # This will execute all steps from main.py:
    # 1. Setup catalog/schema
    # 2. Create dimensions (100K customers, 10K products)
    # 3. Create facts (with proper seasonality and patterns)
    # 4. Create aggregates (affinity scores, size bridge)
    # 5. Enable CDC and optimization
    # 6. Run validation
    
    generator.run()
    
    print("✅ Pipeline completed successfully!")
    
except Exception as e:
    print(f"❌ Pipeline failed: {str(e)}")
    raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## Option 3: Step-by-Step Execution (For Debugging)
# MAGIC
# MAGIC Run each step individually if you want more control:

# COMMAND ----------

# Step 1: Setup Catalog and Schema
generator.setup_catalog()

# COMMAND ----------

# Step 2: Drop existing tables if needed
if config['force_recreate']:
    generator.drop_existing_tables()

# COMMAND ----------

# Step 3: Create Dimensions (using actual DimensionGenerator)
dim_gen = DimensionGenerator(spark, config)

# Create each dimension with full logic from dimension_generators.py
dim_gen.create_customer_dimension()  # 100K customers with segments, channels, etc.
dim_gen.create_product_dimension()   # 10K products with categories, brands, seasons
dim_gen.create_location_dimension()  # 13 locations (10 stores, 2 warehouses, 1 DC)
dim_gen.create_date_dimension()      # 730 days of history + 365 future
dim_gen.create_channel_dimension()   # 8 channels (web, mobile, store, etc.)
dim_gen.create_time_dimension()      # 96 time periods (15-min intervals)

print("✅ All dimensions created with full data")

# COMMAND ----------

# Step 4: Create Facts (using actual FactGenerator with inventory alignment)
# NOTE: The orchestrator in fashion-retail-main.py handles initialization automatically
# For step-by-step execution, you would need to:
# 1. Initialize InventoryManager and SalesValidator
# 2. Pass them to FactGenerator constructor
#
# For simplicity, use the full pipeline via generator.run() instead of step-by-step

print("⚠️  For inventory alignment features, use generator.run() instead of step-by-step execution")
print("   The step-by-step approach shown here does not initialize InventoryManager/SalesValidator")

# If you still want to run step-by-step, uncomment below (will use legacy mode):
# fact_gen = FactGenerator(spark, config)
# fact_gen.create_sales_fact()
# fact_gen.create_inventory_fact()
# fact_gen.create_customer_event_fact()
# fact_gen.create_cart_abandonment_fact()
# fact_gen.create_demand_forecast_fact()

print("✅ Skip to Step 6 or use generator.run() for full pipeline")

# COMMAND ----------

# Step 5: Create Aggregates (using actual AggregateGenerator)
agg_gen = AggregateGenerator(spark, config)

# Create bridge and aggregate tables
agg_gen.create_customer_product_affinity()  # Personalization scores from actual data
agg_gen.create_size_fit_bridge()           # Size/fit feedback patterns
agg_gen.create_inventory_movement_fact()    # Movement transactions

print("✅ All aggregates created from actual fact data")

# COMMAND ----------

# Step 6: Apply Optimizations
generator.optimize_tables()
generator.enable_cdc()

print("✅ Optimizations applied")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validate the Generated Data

# COMMAND ----------

# Run validation to confirm data volumes match expectations
validation_results = {}

# Check actual row counts
tables_to_validate = [
    ('gold_customer_dim', 'customer_key', 100_000),
    ('gold_product_dim', 'product_key', 10_000),
    ('gold_sales_fact', 'transaction_id', 1_500_000),
    ('gold_inventory_fact', 'product_key, location_key, date_key', 390_000),  # 30 days × 1000 products × 13 locations
    ('gold_customer_product_affinity_agg', 'customer_key, product_key', 500_000)  # Varies based on interactions
]

for table, key_cols, expected in tables_to_validate:
    actual_count = spark.sql(f"""
        SELECT COUNT(*) as cnt 
        FROM {config['catalog']}.{config['schema']}.{table}
    """).collect()[0]['cnt']
    
    validation_results[table] = {
        'expected': expected,
        'actual': actual_count,
        'match': '✅' if abs(actual_count - expected) / expected < 0.2 else '⚠️'  # 20% tolerance
    }

# Display results
import pandas as pd
df_validation = pd.DataFrame(validation_results).T
display(df_validation)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test Key Use Cases with Real Generated Data

# COMMAND ----------

# Test 1: Real-time Personalization - Check affinity scores are properly calculated
test_personalization = spark.sql(f"""
    SELECT 
        'Personalization' as use_case,
        COUNT(DISTINCT customer_key) as customers_with_affinity,
        AVG(affinity_score) as avg_affinity,
        MAX(affinity_score) as max_affinity,
        AVG(predicted_cltv_impact) as avg_cltv_impact
    FROM {config['catalog']}.{config['schema']}.gold_customer_product_affinity_agg
    WHERE affinity_score > 0
""")

display(test_personalization)

# COMMAND ----------

# Test 2: Inventory Optimization - Check for imbalances
test_inventory = spark.sql(f"""
    WITH inventory_health AS (
        SELECT 
            SUM(CASE WHEN is_stockout THEN 1 ELSE 0 END) as stockout_count,
            SUM(CASE WHEN is_overstock THEN 1 ELSE 0 END) as overstock_count,
            AVG(days_of_supply) as avg_days_supply,
            COUNT(DISTINCT product_key) as products_tracked,
            COUNT(DISTINCT location_key) as locations_tracked
        FROM {config['catalog']}.{config['schema']}.gold_inventory_fact
        WHERE date_key = (SELECT MAX(date_key) FROM {config['catalog']}.{config['schema']}.gold_inventory_fact)
    )
    SELECT 
        'Inventory' as use_case,
        stockout_count,
        overstock_count,
        ROUND(avg_days_supply, 1) as avg_days_supply,
        products_tracked,
        locations_tracked
    FROM inventory_health
""")

display(test_inventory)

# COMMAND ----------

# Test 3: Demand Forecast - Check forecast accuracy
test_forecast = spark.sql(f"""
    SELECT 
        'Demand Forecast' as use_case,
        COUNT(*) as forecasts_with_actuals,
        ROUND(AVG(forecast_accuracy), 1) as avg_accuracy_pct,
        ROUND(AVG(mape), 1) as avg_mape,
        COUNT(DISTINCT product_key) as products_forecasted
    FROM {config['catalog']}.{config['schema']}.gold_demand_forecast_fact
    WHERE actual_quantity IS NOT NULL
""")

display(test_forecast)

# COMMAND ----------

# Test 4: Size/Fit - Check return patterns
test_size_fit = spark.sql(f"""
    SELECT 
        'Size/Fit' as use_case,
        COUNT(*) as feedback_records,
        ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 1) as return_rate_pct,
        ROUND(AVG(fit_score), 1) as avg_fit_score,
        SUM(CASE WHEN fit_description = 'perfect' THEN 1 ELSE 0 END) as perfect_fit_count
    FROM {config['catalog']}.{config['schema']}.gold_size_fit_bridge
""")

display(test_size_fit)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 5: Inventory Alignment Validation (NEW - Feature: 001-i-want-to)

# COMMAND ----------

# Test 5a: Stockout Rate - Should be 5-10%
test_stockout_rate = spark.sql(f"""
    SELECT
        'Stockout Rate' as metric,
        COUNT(*) as total_positions,
        SUM(CASE WHEN is_stockout = TRUE THEN 1 ELSE 0 END) as stockout_positions,
        ROUND(SUM(CASE WHEN is_stockout = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as stockout_rate_pct
    FROM {config['catalog']}.{config['schema']}.gold_inventory_fact
    WHERE date_key = (SELECT MAX(date_key) FROM {config['catalog']}.{config['schema']}.gold_inventory_fact)
""")

display(test_stockout_rate)

# COMMAND ----------

# Test 5b: Inventory Constrained Sales - Check how many sales were constrained
test_constrained_sales = spark.sql(f"""
    SELECT
        'Inventory Constrained Sales' as metric,
        COUNT(*) as total_sales,
        SUM(CASE WHEN is_inventory_constrained = TRUE THEN 1 ELSE 0 END) as constrained_sales,
        ROUND(SUM(CASE WHEN is_inventory_constrained = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as constrained_pct,
        SUM(quantity_requested) as total_requested,
        SUM(quantity_sold) as total_sold,
        SUM(quantity_requested - quantity_sold) as lost_quantity
    FROM {config['catalog']}.{config['schema']}.gold_sales_fact
    WHERE quantity_requested IS NOT NULL
""")

display(test_constrained_sales)

# COMMAND ----------

# Test 5c: Stockout Events - New table validation
test_stockout_events = spark.sql(f"""
    SELECT
        'Stockout Events' as metric,
        COUNT(*) as total_events,
        SUM(lost_sales_attempts) as total_lost_attempts,
        SUM(lost_sales_quantity) as total_lost_quantity,
        ROUND(SUM(lost_sales_revenue), 2) as total_lost_revenue,
        SUM(CASE WHEN peak_season_flag = TRUE THEN 1 ELSE 0 END) as peak_season_stockouts,
        ROUND(AVG(stockout_duration_days), 1) as avg_duration_days
    FROM {config['catalog']}.{config['schema']}.gold_stockout_events
""")

display(test_stockout_events)

# COMMAND ----------

# Test 5d: Cart Abandonment - Low Inventory Impact
test_low_inventory_abandonment = spark.sql(f"""
    SELECT
        'Low Inventory Cart Abandonment' as metric,
        COUNT(*) as total_abandonments,
        SUM(CASE WHEN low_inventory_trigger = TRUE THEN 1 ELSE 0 END) as low_inventory_abandonments,
        ROUND(SUM(CASE WHEN low_inventory_trigger = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as low_inv_pct,
        AVG(inventory_constrained_items) as avg_constrained_items
    FROM {config['catalog']}.{config['schema']}.gold_cart_abandonment_fact
    WHERE low_inventory_trigger IS NOT NULL
""")

display(test_low_inventory_abandonment)

# COMMAND ----------

# Test 5e: No Negative Inventory - Critical validation
test_no_negative_inventory = spark.sql(f"""
    SELECT
        'Negative Inventory Violations' as metric,
        COUNT(*) as violation_count,
        CASE
            WHEN COUNT(*) = 0 THEN '✅ PASS'
            ELSE '❌ FAIL'
        END as test_result
    FROM {config['catalog']}.{config['schema']}.gold_inventory_fact
    WHERE quantity_available < 0
""")

display(test_no_negative_inventory)

# COMMAND ----------

# Test 5f: Return Replenishment Delays - Should be 1-3 days
test_return_delays = spark.sql(f"""
    WITH return_delays AS (
        SELECT
            sf.transaction_id,
            sf.date_key as return_date_key,
            sf.return_restocked_date_key,
            d1.calendar_date as return_date,
            d2.calendar_date as restock_date,
            DATEDIFF(d2.calendar_date, d1.calendar_date) as delay_days
        FROM {config['catalog']}.{config['schema']}.gold_sales_fact sf
        JOIN {config['catalog']}.{config['schema']}.gold_date_dim d1
            ON sf.date_key = d1.date_key
        LEFT JOIN {config['catalog']}.{config['schema']}.gold_date_dim d2
            ON sf.return_restocked_date_key = d2.date_key
        WHERE sf.is_return = TRUE
            AND sf.return_restocked_date_key IS NOT NULL
    )
    SELECT
        'Return Replenishment Delays' as metric,
        COUNT(*) as total_returns,
        SUM(CASE WHEN delay_days BETWEEN 1 AND 3 THEN 1 ELSE 0 END) as valid_delays,
        SUM(CASE WHEN delay_days < 1 OR delay_days > 3 THEN 1 ELSE 0 END) as invalid_delays,
        MIN(delay_days) as min_delay,
        MAX(delay_days) as max_delay,
        ROUND(AVG(delay_days), 1) as avg_delay,
        CASE
            WHEN SUM(CASE WHEN delay_days < 1 OR delay_days > 3 THEN 1 ELSE 0 END) = 0 THEN '✅ PASS'
            ELSE '⚠️ CHECK'
        END as test_result
    FROM return_delays
""")

display(test_return_delays)

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Generation Complete with Actual Modules + Inventory Alignment!
# MAGIC
# MAGIC The data has been generated using the **actual Python modules**, ensuring:
# MAGIC - ✅ Full 50K customers with realistic segments
# MAGIC - ✅ Proper seasonality patterns from `FactGenerator`
# MAGIC - ✅ Realistic customer segments and distributions from `DimensionGenerator`
# MAGIC - ✅ Calculated affinity scores from actual sales/event data in `AggregateGenerator`
# MAGIC - ✅ **NEW: Inventory-aligned customer behavior** (Feature: 001-i-want-to)
# MAGIC   - Sales constrained by available inventory (no phantom sales!)
# MAGIC   - 5-10% stockout rate across product-location combinations
# MAGIC   - Returns replenish inventory 1-3 days after return date
# MAGIC   - Cart abandonment +10pp higher when low inventory detected
# MAGIC   - New `gold_stockout_events` table with lost sales analytics
# MAGIC
# MAGIC ### Key Features of Inventory Alignment:
# MAGIC - **Real-time State Tracking**: 130K+ product-location positions tracked in-memory
# MAGIC - **Random Allocation**: Fair distribution when multiple customers compete for limited inventory
# MAGIC - **Stockout Events**: Captures duration, lost sales attempts, quantity, and revenue
# MAGIC - **Schema Evolution**: New columns added via Delta Lake mergeSchema (backward compatible)
# MAGIC - **Data Integrity**: Zero negative inventory violations, all constraints enforced
# MAGIC
# MAGIC ### New Tables & Columns:
# MAGIC - **gold_sales_fact** (+4 columns): quantity_requested, is_inventory_constrained, inventory_at_purchase, return_restocked_date_key
# MAGIC - **gold_inventory_fact** (+3 columns): stockout_duration_days, last_replenishment_date, next_replenishment_date
# MAGIC - **gold_cart_abandonment_fact** (+2 columns): low_inventory_trigger, inventory_constrained_items
# MAGIC - **gold_stockout_events** (NEW TABLE): Stockout analytics with lost sales estimation
# MAGIC
# MAGIC ### Next Steps:
# MAGIC 1. Run validation queries (Test 5a-5f above) to verify inventory alignment
# MAGIC 2. Query `gold_stockout_events` for lost sales impact analysis
# MAGIC 3. Analyze cart abandonment patterns by low inventory trigger
# MAGIC 4. Build ML models using inventory-constrained features
# MAGIC 5. Set up incremental pipelines using the CDC-enabled tables

# COMMAND ----------

# Display final summary
summary = spark.sql(f"""
    SELECT 
        table_name,
        num_rows,
        size_in_bytes,
        last_modified
    FROM (
        SELECT 
            'gold_customer_dim' as table_name,
            COUNT(*) as num_rows,
            0 as size_in_bytes,
            MAX(etl_timestamp) as last_modified
        FROM {config['catalog']}.{config['schema']}.gold_customer_dim
        UNION ALL
        SELECT 
            'gold_sales_fact' as table_name,
            COUNT(*) as num_rows,
            0 as size_in_bytes,
            MAX(etl_timestamp) as last_modified
        FROM {config['catalog']}.{config['schema']}.gold_sales_fact
        UNION ALL
        SELECT 
            'gold_inventory_fact' as table_name,
            COUNT(*) as num_rows,
            0 as size_in_bytes,
            MAX(etl_timestamp) as last_modified
        FROM {config['catalog']}.{config['schema']}.gold_inventory_fact
    )
    ORDER BY num_rows DESC
""")

display(summary)
