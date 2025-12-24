# Databricks notebook source
# MAGIC %md
# MAGIC # Fashion Retail Gold Layer Data Generation
# MAGIC
# MAGIC This notebook orchestrates the execution of the Fashion Retail data generation pipeline
# MAGIC using the new Python package structure.
# MAGIC
# MAGIC ## Prerequisites:
# MAGIC 1. The `src/fashion_retail/` package structure should be available
# MAGIC 2. All dependencies are installed via requirements or pip install
# MAGIC
# MAGIC ## Key Improvements:
# MAGIC - ✅ Clean Python package imports (no more complex importlib.util)
# MAGIC - ✅ Proper module organization with src/ structure
# MAGIC - ✅ Configuration management via dataclass
# MAGIC - ✅ Inventory alignment features (Feature: 001-i-want-to)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup: Import the Fashion Retail Package

# COMMAND ----------

import sys
import os

# Add the src directory to Python path for clean imports
sys.path.append('../src')

# Now we can use clean, standard Python imports
from fashion_retail import FashionRetailDataGenerator
from fashion_retail.config import get_config, get_small_config
from fashion_retail.data import DimensionGenerator, FactGenerator, AggregateGenerator
from fashion_retail.inventory import InventoryManager, SalesValidator, StockoutGenerator

print("✅ Fashion Retail package imported successfully!")
print("Available components:")
print("  - FashionRetailDataGenerator (main orchestrator)")
print("  - Configuration management (get_config, get_small_config)")
print("  - Data generators (DimensionGenerator, FactGenerator, AggregateGenerator)")
print("  - Inventory alignment (InventoryManager, SalesValidator, StockoutGenerator)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration Options

# COMMAND ----------

# Option 1: Use default configuration
config = get_config()
print("Default Configuration:")
print(f"  Catalog: {config.catalog}")
print(f"  Schema: {config.schema}")
print(f"  Customers: {config.customers:,}")
print(f"  Products: {config.products:,}")
print(f"  Locations: {config.locations}")

print("\n" + "="*50)

# Option 2: Use small configuration for testing
small_config = get_small_config()
print("Small Configuration (for testing):")
print(f"  Catalog: {small_config.catalog}")
print(f"  Schema: {small_config.schema}")
print(f"  Customers: {small_config.customers:,}")
print(f"  Products: {small_config.products:,}")
print(f"  Locations: {small_config.locations}")

print("\n" + "="*50)

# Option 3: Custom configuration
custom_config = get_config(
    catalog="my_catalog",
    schema="my_schema",
    customers=25_000,
    products=1_000
)
print("Custom Configuration:")
print(f"  Catalog: {custom_config.catalog}")
print(f"  Schema: {custom_config.schema}")
print(f"  Customers: {custom_config.customers:,}")
print(f"  Products: {custom_config.products:,}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Choose Your Configuration
# MAGIC
# MAGIC Select which configuration to use for data generation:

# COMMAND ----------

# Choose your configuration here:
# - Use small_config for quick testing (50K customers, 2K products)
# - Use config for full scale (100K customers, 10K products)
# - Use custom_config for your own parameters

selected_config = small_config  # Change this to your preferred config

print(f"Selected configuration: {selected_config.customers:,} customers, {selected_config.products:,} products")
print(f"Target: {selected_config.full_schema_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Execute the Complete Pipeline
# MAGIC
# MAGIC This runs the full data generation pipeline with inventory alignment features.

# COMMAND ----------

# Initialize the generator with current Spark session
generator = FashionRetailDataGenerator(spark, selected_config)

# Run the complete pipeline
try:
    print("Starting Fashion Retail Data Generation Pipeline...")
    print("=" * 60)
    
    # This will execute all steps:
    # 1. Setup catalog/schema
    # 2. Create dimensions (customers, products, locations, dates, etc.)
    # 3. Create facts with inventory alignment (sales, inventory, events, etc.)
    # 4. Create aggregates (affinity scores, size bridge, etc.)
    # 5. Enable CDC and optimization
    # 6. Run validation
    
    generator.run()
    
    print("✅ Pipeline completed successfully!")
    
except Exception as e:
    print(f"❌ Pipeline failed: {str(e)}")
    raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## Alternative: Step-by-Step Execution
# MAGIC
# MAGIC If you prefer to run each step individually for debugging:

# COMMAND ----------

# Uncomment and run these cells individually if you want step-by-step control:

# # Step 1: Setup Catalog and Schema
# generator.setup_catalog()

# COMMAND ----------

# # Step 2: Drop existing tables if needed
# if selected_config.force_recreate:
#     generator.drop_existing_tables()

# COMMAND ----------

# # Step 3: Create Dimensions
# generator.create_dimensions()
# print("✅ All dimensions created")

# COMMAND ----------

# # Step 4: Create Facts (with inventory alignment)
# generator.create_facts()
# print("✅ All facts created with inventory alignment")

# COMMAND ----------

# # Step 5: Create Aggregates
# generator.create_bridge_aggregates()
# print("✅ All aggregates created")

# COMMAND ----------

# # Step 6: Apply Optimizations
# generator.optimize_tables()
# generator.enable_cdc()
# print("✅ Optimizations applied")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validate the Generated Data

# COMMAND ----------

# Run validation to confirm data volumes match expectations
validation_results = {}

# Check actual row counts
tables_to_validate = [
    ('gold_customer_dim', 'customer_key', selected_config.customers),
    ('gold_product_dim', 'product_key', selected_config.products),
    ('gold_location_dim', 'location_key', selected_config.locations),
    ('gold_sales_fact', 'transaction_id', None),  # Variable based on events
    ('gold_inventory_fact', 'product_key, location_key, date_key', None),  # Variable
    ('gold_customer_product_affinity_agg', 'customer_key, product_key', None)  # Variable
]

for table, key_cols, expected in tables_to_validate:
    try:
        actual_count = spark.sql(f"""
            SELECT COUNT(*) as cnt 
            FROM {selected_config.full_schema_name}.{table}
        """).collect()[0]['cnt']
        
        # Convert expected to string to avoid mixed types in pandas DataFrame
        expected_str = str(expected) if expected is not None else 'Variable'
        
        validation_results[table] = {
            'expected': expected_str,
            'actual': str(actual_count),  # Convert to string to ensure consistent types
            'status': '✅' if expected is None or abs(actual_count - expected) / max(expected, 1) < 0.2 else '⚠️'
        }
    except Exception as e:
        validation_results[table] = {
            'expected': 'Variable',
            'actual': f'Error: {str(e)}',
            'status': '❌'
        }

# Display results using print instead of display to avoid Arrow conversion issues
print("📊 Data Validation Results:")
print("=" * 80)
for table_name, results in validation_results.items():
    print(f"{results['status']} {table_name}")
    print(f"   Expected: {results['expected']}")
    print(f"   Actual:   {results['actual']}")
    print()

# Alternative: Create a simple summary table that's safe to display
summary_data = []
for table_name, results in validation_results.items():
    summary_data.append({
        'table': table_name,
        'expected': results['expected'],
        'actual': results['actual'],
        'status': results['status']
    })

# Create Spark DataFrame instead of pandas to avoid Arrow conversion issues
validation_df = spark.createDataFrame(summary_data)
validation_df.show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test Inventory Alignment Features (NEW - Feature: 001-i-want-to)

# COMMAND ----------

# Test 1: Stockout Rate - Should be around 7.5% (5-10% range)
test_stockout_rate = spark.sql(f"""
    SELECT
        'Stockout Rate' as metric,
        COUNT(*) as total_positions,
        SUM(CASE WHEN is_stockout = TRUE THEN 1 ELSE 0 END) as stockout_positions,
        ROUND(SUM(CASE WHEN is_stockout = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as stockout_rate_pct
    FROM {selected_config.full_schema_name}.gold_inventory_fact
    WHERE date_key = (SELECT MAX(date_key) FROM {selected_config.full_schema_name}.gold_inventory_fact)
""")

print("📊 Stockout Rate Analysis:")
display(test_stockout_rate)

# COMMAND ----------

# Test 2: Inventory Constrained Sales - Check how many sales were constrained
test_constrained_sales = spark.sql(f"""
    SELECT
        'Inventory Constrained Sales' as metric,
        COUNT(*) as total_sales,
        SUM(CASE WHEN is_inventory_constrained = TRUE THEN 1 ELSE 0 END) as constrained_sales,
        ROUND(SUM(CASE WHEN is_inventory_constrained = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as constrained_pct,
        SUM(quantity_requested) as total_requested,
        SUM(quantity_sold) as total_sold,
        SUM(quantity_requested - quantity_sold) as lost_quantity
    FROM {selected_config.full_schema_name}.gold_sales_fact
    WHERE quantity_requested IS NOT NULL
""")

print("📊 Inventory Constrained Sales Analysis:")
display(test_constrained_sales)

# COMMAND ----------

# Test 3: Stockout Events - New table validation
test_stockout_events = spark.sql(f"""
    SELECT
        'Stockout Events' as metric,
        COUNT(*) as total_events,
        SUM(lost_sales_attempts) as total_lost_attempts,
        SUM(lost_sales_quantity) as total_lost_quantity,
        ROUND(SUM(lost_sales_revenue), 2) as total_lost_revenue,
        SUM(CASE WHEN peak_season_flag = TRUE THEN 1 ELSE 0 END) as peak_season_stockouts,
        ROUND(AVG(stockout_duration_days), 1) as avg_duration_days
    FROM {selected_config.full_schema_name}.gold_stockout_events
""")

print("📊 Stockout Events Analysis:")
display(test_stockout_events)

# COMMAND ----------

# Test 4: Cart Abandonment - Low Inventory Impact
test_low_inventory_abandonment = spark.sql(f"""
    SELECT
        'Low Inventory Cart Abandonment' as metric,
        COUNT(*) as total_abandonments,
        SUM(CASE WHEN low_inventory_trigger = TRUE THEN 1 ELSE 0 END) as low_inventory_abandonments,
        ROUND(SUM(CASE WHEN low_inventory_trigger = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as low_inv_pct,
        AVG(inventory_constrained_items) as avg_constrained_items
    FROM {selected_config.full_schema_name}.gold_cart_abandonment_fact
    WHERE low_inventory_trigger IS NOT NULL
""")

print("📊 Cart Abandonment Analysis:")
display(test_low_inventory_abandonment)

# COMMAND ----------

# Test 5: No Negative Inventory - Critical validation
test_no_negative_inventory = spark.sql(f"""
    SELECT
        'Negative Inventory Violations' as metric,
        COUNT(*) as violation_count,
        CASE
            WHEN COUNT(*) = 0 THEN '✅ PASS'
            ELSE '❌ FAIL'
        END as test_result
    FROM {selected_config.full_schema_name}.gold_inventory_fact
    WHERE quantity_available < 0
""")

print("🔍 Data Integrity Check:")
display(test_no_negative_inventory)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Sample Analytics Queries
# MAGIC
# MAGIC Test the key use cases with the generated data:

# COMMAND ----------

# Use Case 1: Real-time Personalization
print("🎯 Use Case 1: Real-time Personalization")

personalization_sample = spark.sql(f"""
    SELECT 
        'Personalization Data' as use_case,
        COUNT(DISTINCT customer_key) as customers_with_affinity,
        AVG(affinity_score) as avg_affinity,
        MAX(affinity_score) as max_affinity,
        AVG(predicted_cltv_impact) as avg_cltv_impact
    FROM {selected_config.full_schema_name}.gold_customer_product_affinity_agg
    WHERE affinity_score > 0
""")

display(personalization_sample)

# COMMAND ----------

# Use Case 2: Inventory Optimization
print("📦 Use Case 2: Inventory Optimization")

inventory_health = spark.sql(f"""
    WITH inventory_summary AS (
        SELECT 
            SUM(CASE WHEN is_stockout THEN 1 ELSE 0 END) as stockout_count,
            SUM(CASE WHEN is_overstock THEN 1 ELSE 0 END) as overstock_count,
            AVG(days_of_supply) as avg_days_supply,
            COUNT(DISTINCT product_key) as products_tracked,
            COUNT(DISTINCT location_key) as locations_tracked
        FROM {selected_config.full_schema_name}.gold_inventory_fact
        WHERE date_key = (SELECT MAX(date_key) FROM {selected_config.full_schema_name}.gold_inventory_fact)
    )
    SELECT 
        'Inventory Health' as use_case,
        stockout_count,
        overstock_count,
        ROUND(avg_days_supply, 1) as avg_days_supply,
        products_tracked,
        locations_tracked
    FROM inventory_summary
""")

display(inventory_health)

# COMMAND ----------

# Use Case 3: Demand Forecasting
print("📈 Use Case 3: Demand Forecasting")

forecast_accuracy = spark.sql(f"""
    SELECT 
        'Demand Forecast' as use_case,
        COUNT(*) as forecasts_with_actuals,
        ROUND(AVG(forecast_accuracy), 1) as avg_accuracy_pct,
        ROUND(AVG(mape), 1) as avg_mape,
        COUNT(DISTINCT product_key) as products_forecasted
    FROM {selected_config.full_schema_name}.gold_demand_forecast_fact
    WHERE actual_quantity IS NOT NULL
""")

display(forecast_accuracy)

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Generation Complete with New Package Structure!
# MAGIC
# MAGIC The data has been generated using the **new Python package structure**, providing:
# MAGIC
# MAGIC ### 🏗️ **Improved Architecture:**
# MAGIC - ✅ Clean Python package imports (no more complex `importlib.util`)
# MAGIC - ✅ Proper `src/fashion_retail/` package organization
# MAGIC - ✅ Configuration management via dataclass
# MAGIC - ✅ Modular design with clear separation of concerns
# MAGIC
# MAGIC ### 📊 **Data Features:**
# MAGIC - ✅ Realistic customer segments and product catalogs
# MAGIC - ✅ Proper seasonality patterns and business logic
# MAGIC - ✅ **Inventory-aligned customer behavior** (Feature: 001-i-want-to)
# MAGIC   - Sales constrained by available inventory (no phantom sales!)
# MAGIC   - 5-10% stockout rate across product-location combinations
# MAGIC   - Returns replenish inventory 1-3 days after return date
# MAGIC   - Cart abandonment +10pp higher when low inventory detected
# MAGIC   - New `gold_stockout_events` table with lost sales analytics
# MAGIC
# MAGIC ### 🔧 **Technical Improvements:**
# MAGIC - **Standard Python Imports**: `from fashion_retail import FashionRetailDataGenerator`
# MAGIC - **Configuration Management**: `get_config()`, `get_small_config()`, custom configs
# MAGIC - **Modular Components**: Separate packages for data generation and inventory management
# MAGIC - **Better IDE Support**: Autocomplete, navigation, and debugging
# MAGIC - **Easier Testing**: Standard Python package structure for unit tests
# MAGIC
# MAGIC ### 📋 **Next Steps:**
# MAGIC 1. Explore the generated data using the validation queries above
# MAGIC 2. Build ML models using the inventory-constrained features
# MAGIC 3. Set up incremental pipelines using the CDC-enabled tables
# MAGIC 4. Extend the package with additional generators or analytics

# COMMAND ----------

# Display final summary
print("📋 Final Data Summary:")

summary = spark.sql(f"""
    SELECT 
        table_name,
        num_rows,
        last_modified
    FROM (
        SELECT 
            'gold_customer_dim' as table_name,
            COUNT(*) as num_rows,
            MAX(etl_timestamp) as last_modified
        FROM {selected_config.full_schema_name}.gold_customer_dim
        UNION ALL
        SELECT 
            'gold_product_dim' as table_name,
            COUNT(*) as num_rows,
            MAX(etl_timestamp) as last_modified
        FROM {selected_config.full_schema_name}.gold_product_dim
        UNION ALL
        SELECT 
            'gold_sales_fact' as table_name,
            COUNT(*) as num_rows,
            MAX(etl_timestamp) as last_modified
        FROM {selected_config.full_schema_name}.gold_sales_fact
        UNION ALL
        SELECT 
            'gold_inventory_fact' as table_name,
            COUNT(*) as num_rows,
            MAX(etl_timestamp) as last_modified
        FROM {selected_config.full_schema_name}.gold_inventory_fact
        UNION ALL
        SELECT 
            'gold_stockout_events' as table_name,
            COUNT(*) as num_rows,
            MAX(etl_timestamp) as last_modified
        FROM {selected_config.full_schema_name}.gold_stockout_events
    )
    ORDER BY num_rows DESC
""")

display(summary)

print(f"\n🎉 Data generation completed successfully!")
print(f"📍 Location: {selected_config.full_schema_name}")
print(f"🏗️ Architecture: Clean Python package structure")
print(f"📊 Features: Inventory alignment + realistic business patterns")