# Databricks notebook source
# MAGIC %md
# MAGIC # Stage 4: Test Silver Pipeline
# MAGIC 
# MAGIC This notebook validates the Silver pipeline:
# MAGIC 
# MAGIC 1. Verify bronze table has data
# MAGIC 2. Preview transformation logic
# MAGIC 3. Run/validate pipeline
# MAGIC 4. Check data quality metrics

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

CATALOG = "juan_dev"
SCHEMA = "retail"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Verify Bronze Data Exists

# COMMAND ----------

bronze_df = spark.table(f"{CATALOG}.{SCHEMA}.bronze_pos_transactions")
bronze_count = bronze_df.count()

print(f"✅ Bronze table has {bronze_count} transactions")
print(f"\nSchema:")
bronze_df.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Preview Transformation (Manual Test)

# COMMAND ----------

from pyspark.sql.functions import col, explode, lit, coalesce, date_format, concat_ws, current_timestamp

# Read bronze (batch mode for testing)
bronze = spark.table(f"{CATALOG}.{SCHEMA}.bronze_pos_transactions")

# Explode items
exploded = bronze.select(
    col("transaction_id"),
    col("store_id"),
    col("timestamp"),
    col("customer_id"),
    explode(col("items")).alias("item")
).select(
    "*",
    col("item.sku").alias("sku"),
    col("item.qty").alias("qty"),
    col("item.price").alias("price"),
    col("item.discount").alias("discount")
).drop("item")

print(f"✅ Exploded to {exploded.count()} line items")
display(exploded.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Check Dimension Tables

# COMMAND ----------

# Check if dimension tables exist and have data
dims = [
    "gold_product_dim",
    "gold_location_dim", 
    "gold_customer_dim",
    "gold_channel_dim"
]

print("📋 Dimension Table Status:")
print("=" * 60)

for dim in dims:
    try:
        count = spark.table(f"{CATALOG}.{SCHEMA}.{dim}").count()
        print(f"✅ {dim}: {count:,} rows")
    except Exception as e:
        print(f"❌ {dim}: Not found - {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Preview Join Results

# COMMAND ----------

# Test location join
locations = spark.table(f"{CATALOG}.{SCHEMA}.gold_location_dim").select(
    "location_key", "location_id", "location_type", "state_tax_rate"
)

print("📍 Location dimension sample:")
display(locations.limit(5))

# Check if store_ids match location_ids
print("\n🔍 Store IDs in bronze data:")
display(exploded.select("store_id").distinct())

print("\n🔍 Location IDs in dimension:")
display(locations.select("location_id").distinct())

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Run Pipeline
# MAGIC 
# MAGIC Add silver_pipeline.py to your DLT pipeline and run it.
# MAGIC 
# MAGIC **Pipeline Configuration:**
# MAGIC - Add notebook: `40-medallion-pipeline/pipelines/silver_pipeline.py`
# MAGIC - Or create new pipeline with both bronze and silver notebooks

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: Validate Silver Table (After Pipeline Runs)

# COMMAND ----------

# Check if silver table exists
try:
    silver_df = spark.table(f"{CATALOG}.{SCHEMA}.silver_transactions_unified")
    silver_count = silver_df.count()
    
    print(f"✅ Silver table has {silver_count} line items")
    print(f"\nSchema:")
    silver_df.printSchema()
    
    # Show sample
    print("\n📊 Sample Data:")
    display(silver_df.limit(10))
    
except Exception as e:
    print(f"⚠️ Silver table not found: {e}")
    print("\n   Run the pipeline first with silver_pipeline.py included")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 7: Validate Data Quality

# COMMAND ----------

try:
    silver_df = spark.table(f"{CATALOG}.{SCHEMA}.silver_transactions_unified")
    
    print("📋 Data Quality Validation:")
    print("=" * 60)
    
    # Check for null keys
    from pyspark.sql.functions import count, when, sum as spark_sum
    
    quality_stats = silver_df.agg(
        count("*").alias("total_rows"),
        spark_sum(when(col("product_key").isNull(), 1).otherwise(0)).alias("null_product_key"),
        spark_sum(when(col("location_key").isNull(), 1).otherwise(0)).alias("null_location_key"),
        spark_sum(when(col("customer_key").isNull(), 1).otherwise(0)).alias("null_customer_key"),
        spark_sum(when(col("qty") <= 0, 1).otherwise(0)).alias("invalid_qty"),
        spark_sum(when(col("price") < 0, 1).otherwise(0)).alias("invalid_price")
    ).collect()[0]
    
    total = quality_stats["total_rows"]
    
    print(f"Total rows: {total:,}")
    print(f"\nNull dimension keys:")
    print(f"  - product_key: {quality_stats['null_product_key']:,} ({100*quality_stats['null_product_key']/total:.1f}%)")
    print(f"  - location_key: {quality_stats['null_location_key']:,} ({100*quality_stats['null_location_key']/total:.1f}%)")
    print(f"  - customer_key: {quality_stats['null_customer_key']:,} ({100*quality_stats['null_customer_key']/total:.1f}%)")
    print(f"\nInvalid values:")
    print(f"  - qty <= 0: {quality_stats['invalid_qty']:,}")
    print(f"  - price < 0: {quality_stats['invalid_price']:,}")
    
    # Note: High null rates for product_key/location_key are expected
    # because POS generator creates random SKUs/store_ids that don't
    # match the dimension tables. This will be fixed in Stage 6.
    
except Exception as e:
    print(f"⚠️ Cannot validate: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 8: Summary Statistics

# COMMAND ----------

try:
    silver_df = spark.table(f"{CATALOG}.{SCHEMA}.silver_transactions_unified")
    
    print("📊 Summary Statistics:")
    print("=" * 60)
    
    # Aggregate stats
    stats = silver_df.agg(
        count("*").alias("line_items"),
        spark_sum("qty").alias("total_qty"),
        spark_sum("line_total").alias("total_revenue"),
        spark_sum("tax_amount").alias("total_tax"),
        spark_sum("gross_margin").alias("total_margin")
    ).collect()[0]
    
    print(f"Line items: {stats['line_items']:,}")
    print(f"Total quantity: {stats['total_qty']:,}")
    print(f"Total revenue: ${stats['total_revenue']:,.2f}")
    print(f"Total tax: ${stats['total_tax']:,.2f}")
    print(f"Total margin: ${stats['total_margin']:,.2f}")
    
except Exception as e:
    print(f"⚠️ Cannot compute stats: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Stage 4 Complete!

# COMMAND ----------

print("""
╔══════════════════════════════════════════════════════════════════╗
║                    STAGE 4 VALIDATION                            ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  Silver Table: silver_transactions_unified                       ║
║                                                                  ║
║  Transformations Applied:                                        ║
║  ├── Explode items array → line items                            ║
║  ├── Join gold_product_dim (product_key)                         ║
║  ├── Join gold_location_dim (location_key, tax_rate)             ║
║  ├── Join gold_customer_dim (customer_key)                       ║
║  ├── Join gold_channel_dim (channel_key)                         ║
║  ├── Calculate line_total, tax_amount, gross_margin              ║
║  └── Add date_key, time_key                                      ║
║                                                                  ║
║  Data Quality Expectations:                                      ║
║  ├── @dp.expect("valid_quantity", "qty > 0")                     ║
║  ├── @dp.expect("valid_price", "price >= 0")                     ║
║  └── @dp.expect_or_drop("has_sku", "sku IS NOT NULL")            ║
║                                                                  ║
║  Note: High null rates for product_key/location_key expected     ║
║  because POS generator uses random SKUs/stores. Will align       ║
║  generators with dimensions in Stage 6.                          ║
║                                                                  ║
║  Next Step: Stage 5 - Create Gold Pipeline (gold_sales_fact)     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
