# Databricks notebook source
# MAGIC %md
# MAGIC # Stage 5: Test Gold Pipeline
# MAGIC 
# MAGIC This notebook validates the Gold pipeline:
# MAGIC 
# MAGIC 1. Verify silver table has data
# MAGIC 2. Preview transformation to gold schema
# MAGIC 3. Run/validate pipeline
# MAGIC 4. Compare schemas with existing gold_sales_fact

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

CATALOG = "juan_dev"
SCHEMA = "retail"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Verify Silver Data Exists

# COMMAND ----------

silver_df = spark.table(f"{CATALOG}.{SCHEMA}.silver_transactions_unified")
silver_count = silver_df.count()

print(f"✅ Silver table has {silver_count} line items")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Preview Transformation (Manual Test)

# COMMAND ----------

from pyspark.sql.functions import col, lit, coalesce, current_timestamp, when, concat

# Read silver (batch mode for testing)
silver = spark.table(f"{CATALOG}.{SCHEMA}.silver_transactions_unified")

# Transform to gold schema
gold_preview = silver.select(
    col("transaction_id").cast("string").alias("transaction_id"),
    col("line_item_id").cast("string").alias("line_item_id"),
    coalesce(col("customer_key"), lit(-1)).cast("int").alias("customer_key"),
    coalesce(col("product_key"), lit(-1)).cast("int").alias("product_key"),
    col("date_key").cast("int").alias("date_key"),
    col("time_key").cast("int").alias("time_key"),
    coalesce(col("location_key"), lit(-1)).cast("int").alias("location_key"),
    coalesce(col("channel_key"), lit(-1)).cast("int").alias("channel_key"),
    col("transaction_id").alias("order_number"),
    concat(col("store_id"), lit("-REG-"), col("register_id").cast("string")).alias("pos_terminal_id"),
    col("associate_id").alias("sales_associate_id"),
    col("qty").cast("int").alias("quantity_sold"),
    col("qty").cast("int").alias("quantity_requested"),
    lit(False).alias("is_inventory_constrained"),
    lit(100).cast("int").alias("inventory_at_purchase"),
    col("price").cast("double").alias("unit_price"),
    col("discount").cast("double").alias("discount_amount"),
    col("tax_amount").cast("double").alias("tax_amount"),
    col("line_total").cast("double").alias("net_sales_amount"),
    col("gross_margin").cast("double").alias("gross_margin_amount"),
    lit(False).alias("is_return"),
    lit(None).cast("int").alias("return_restocked_date_key"),
    lit(False).alias("is_exchange"),
    when(col("discount") > 0, True).otherwise(False).alias("is_promotional"),
    lit(False).alias("is_clearance"),
    lit("in_store").alias("fulfillment_type"),
    col("payment_method").cast("string").alias("payment_method"),
    lit("pos_streaming").alias("source_system"),
    current_timestamp().alias("etl_timestamp")
)

print(f"✅ Transformed {gold_preview.count()} rows")
print("\nSchema:")
gold_preview.printSchema()

display(gold_preview.limit(5))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Compare with Existing gold_sales_fact Schema

# COMMAND ----------

# Get existing gold_sales_fact schema
existing_gold = spark.table(f"{CATALOG}.{SCHEMA}.gold_sales_fact")

print("📋 Existing gold_sales_fact schema:")
print("=" * 60)
for field in existing_gold.schema.fields:
    print(f"  {field.name}: {field.dataType.simpleString()} {'(nullable)' if field.nullable else '(NOT NULL)'}")

# COMMAND ----------

# Compare schemas
print("\n📋 Schema Comparison:")
print("=" * 60)

existing_cols = {f.name: f for f in existing_gold.schema.fields}
streaming_cols = {f.name: f for f in gold_preview.schema.fields}

# Check for missing columns
missing_in_streaming = set(existing_cols.keys()) - set(streaming_cols.keys())
extra_in_streaming = set(streaming_cols.keys()) - set(existing_cols.keys())

if missing_in_streaming:
    print(f"\n⚠️ Columns in existing but missing in streaming:")
    for col_name in missing_in_streaming:
        print(f"   - {col_name}")
else:
    print("\n✅ All existing columns present in streaming")

if extra_in_streaming:
    print(f"\n⚠️ Extra columns in streaming (will be ignored):")
    for col_name in extra_in_streaming:
        print(f"   - {col_name}")

# Check type compatibility
print("\n📋 Type Comparison:")
for col_name in existing_cols:
    if col_name in streaming_cols:
        existing_type = existing_cols[col_name].dataType.simpleString()
        streaming_type = streaming_cols[col_name].dataType.simpleString()
        if existing_type != streaming_type:
            print(f"   ⚠️ {col_name}: existing={existing_type}, streaming={streaming_type}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Run Pipeline
# MAGIC 
# MAGIC Add gold_pipeline.py to your DLT pipeline and run it.
# MAGIC 
# MAGIC **Pipeline Configuration:**
# MAGIC - Add notebook: `03-medallion-pipeline/pipelines/gold_pipeline.py`

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Validate Gold Streaming Table (After Pipeline Runs)

# COMMAND ----------

# Check if streaming gold table exists
try:
    gold_streaming = spark.table(f"{CATALOG}.{SCHEMA}.gold_sales_fact_streaming")
    gold_count = gold_streaming.count()
    
    print(f"✅ Gold streaming table has {gold_count} rows")
    print(f"\nSchema:")
    gold_streaming.printSchema()
    
    # Show sample
    print("\n📊 Sample Data:")
    display(gold_streaming.limit(10))
    
except Exception as e:
    print(f"⚠️ Gold streaming table not found: {e}")
    print("\n   Run the pipeline first with gold_pipeline.py included")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: Validate Data Quality

# COMMAND ----------

try:
    gold_streaming = spark.table(f"{CATALOG}.{SCHEMA}.gold_sales_fact_streaming")
    
    print("📋 Data Quality Validation:")
    print("=" * 60)
    
    from pyspark.sql.functions import count, sum as spark_sum, avg
    
    # Quality stats
    quality_stats = gold_streaming.agg(
        count("*").alias("total_rows"),
        spark_sum(when(col("customer_key") == -1, 1).otherwise(0)).alias("unknown_customer"),
        spark_sum(when(col("product_key") == -1, 1).otherwise(0)).alias("unknown_product"),
        spark_sum(when(col("location_key") == -1, 1).otherwise(0)).alias("unknown_location"),
        spark_sum(when(col("channel_key") == -1, 1).otherwise(0)).alias("unknown_channel"),
        spark_sum("net_sales_amount").alias("total_sales"),
        avg("net_sales_amount").alias("avg_sales")
    ).collect()[0]
    
    total = quality_stats["total_rows"]
    
    print(f"Total rows: {total:,}")
    print(f"\nUnknown dimension keys (-1):")
    print(f"  - customer_key: {quality_stats['unknown_customer']:,} ({100*quality_stats['unknown_customer']/total:.1f}%)")
    print(f"  - product_key: {quality_stats['unknown_product']:,} ({100*quality_stats['unknown_product']/total:.1f}%)")
    print(f"  - location_key: {quality_stats['unknown_location']:,} ({100*quality_stats['unknown_location']/total:.1f}%)")
    print(f"  - channel_key: {quality_stats['unknown_channel']:,} ({100*quality_stats['unknown_channel']/total:.1f}%)")
    print(f"\nSales metrics:")
    print(f"  - Total sales: ${quality_stats['total_sales']:,.2f}")
    print(f"  - Avg per line: ${quality_stats['avg_sales']:,.2f}")
    
except Exception as e:
    print(f"⚠️ Cannot validate: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 7: Compare with Existing Data

# COMMAND ----------

try:
    gold_streaming = spark.table(f"{CATALOG}.{SCHEMA}.gold_sales_fact_streaming")
    gold_existing = spark.table(f"{CATALOG}.{SCHEMA}.gold_sales_fact")
    
    print("📊 Comparison: Streaming vs Existing Gold Sales:")
    print("=" * 60)
    
    streaming_stats = gold_streaming.agg(
        count("*").alias("rows"),
        spark_sum("net_sales_amount").alias("total_sales")
    ).collect()[0]
    
    existing_stats = gold_existing.agg(
        count("*").alias("rows"),
        spark_sum("net_sales_amount").alias("total_sales")
    ).collect()[0]
    
    print(f"\nExisting gold_sales_fact:")
    print(f"  - Rows: {existing_stats['rows']:,}")
    print(f"  - Total sales: ${existing_stats['total_sales']:,.2f}")
    
    print(f"\nStreaming gold_sales_fact_streaming:")
    print(f"  - Rows: {streaming_stats['rows']:,}")
    print(f"  - Total sales: ${streaming_stats['total_sales']:,.2f}")
    
    print(f"\nStreaming adds {100*streaming_stats['rows']/existing_stats['rows']:.1f}% new rows")
    
except Exception as e:
    print(f"⚠️ Cannot compare: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Stage 5 Complete!

# COMMAND ----------

print("""
╔══════════════════════════════════════════════════════════════════╗
║                    STAGE 5 VALIDATION                            ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  Gold Table: gold_sales_fact_streaming                           ║
║                                                                  ║
║  Schema Mapping from silver_transactions_unified:                ║
║  ├── transaction_id → transaction_id                             ║
║  ├── line_item_id → line_item_id                                 ║
║  ├── customer_key → customer_key (or -1)                         ║
║  ├── product_key → product_key (or -1)                           ║
║  ├── date_key, time_key → date_key, time_key                     ║
║  ├── location_key → location_key (or -1)                         ║
║  ├── channel_key → channel_key (or -1)                           ║
║  ├── qty → quantity_sold, quantity_requested                     ║
║  ├── price → unit_price                                          ║
║  ├── discount → discount_amount, is_promotional                  ║
║  ├── tax_amount → tax_amount                                     ║
║  ├── line_total → net_sales_amount                               ║
║  ├── gross_margin → gross_margin_amount                          ║
║  ├── payment_method → payment_method                             ║
║  └── store_id + register_id → pos_terminal_id                    ║
║                                                                  ║
║  Defaults Applied:                                               ║
║  ├── Unknown dimension keys → -1                                 ║
║  ├── fulfillment_type → 'in_store'                               ║
║  ├── source_system → 'pos_streaming'                             ║
║  └── is_return, is_exchange, is_clearance → False                ║
║                                                                  ║
║  Next Step: Stage 6 - Align generators with dimension data       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
