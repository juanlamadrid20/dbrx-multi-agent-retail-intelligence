# Databricks notebook source
# MAGIC %md
# MAGIC # Stage 6: Test Dimension Alignment
# MAGIC 
# MAGIC This notebook validates that generators use actual dimension values:
# MAGIC 
# MAGIC 1. Test DimensionLoader
# MAGIC 2. Test POS generator with real dimensions
# MAGIC 3. Generate new events and verify joins
# MAGIC 4. Re-run pipeline and check null rates

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

CATALOG = "juan_dev"
SCHEMA = "retail"

# Add 00-data to path for generators and master_data
import sys
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
repo_root = "/Workspace" + "/".join(notebook_path.split("/")[:-2])
sys.path.insert(0, f"{repo_root}/00-data")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Test DimensionLoader

# COMMAND ----------

from generators import create_dimension_loader

# Load dimensions from actual tables
loader = create_dimension_loader(spark, CATALOG, SCHEMA)
print(loader.summary())

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Verify Dimension Values

# COMMAND ----------

# Check SKUs
skus = loader.get_skus(limit=10)
print(f"Sample SKUs: {skus}")
print(f"SKU format matches: {all(s.startswith('SKU_') for s in skus)}")

# Check store IDs
stores = loader.get_store_ids()
print(f"\nStore IDs: {stores}")
print(f"Store format matches: {all(s.startswith('LOC_') for s in stores)}")

# Check customer IDs
customers = loader.get_customer_ids(limit=10)
print(f"\nSample Customer IDs: {customers}")
print(f"Customer format matches: {all(c.startswith('CUST_') for c in customers)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Test POS Generator with Dimensions

# COMMAND ----------

from generators import create_pos_generator

# Create generator with real dimension values
pos_gen = create_pos_generator(
    spark=spark,
    catalog=CATALOG,
    schema=SCHEMA,
    use_dimensions=True,
    batch_size=10
)

# Generate sample events
events = pos_gen.generate_batch(5)

print("Sample POS Events (dimension-aligned):")
print("=" * 60)
for i, event in enumerate(events):
    print(f"\nEvent {i+1}:")
    print(f"  store_id: {event['store_id']}")
    print(f"  customer_id: {event['customer_id']}")
    print(f"  items: {[item['sku'] for item in event['items']]}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Verify Values Match Dimensions

# COMMAND ----------

# Get all unique values from generated events
import json

generated_stores = set()
generated_skus = set()
generated_customers = set()

for event in events:
    generated_stores.add(event['store_id'])
    if event['customer_id']:
        generated_customers.add(event['customer_id'])
    for item in event['items']:
        generated_skus.add(item['sku'])

# Verify against dimension data
dim_stores = set(loader.get_store_ids())
dim_skus = set(loader.get_skus())
dim_customers = set(loader.get_customer_ids())

print("Value Alignment Check:")
print("=" * 60)
print(f"\nStores:")
print(f"  Generated: {generated_stores}")
print(f"  All in dimension: {generated_stores.issubset(dim_stores)}")

print(f"\nSKUs (sample of {len(generated_skus)}):")
print(f"  Generated: {list(generated_skus)[:5]}")
print(f"  All in dimension: {generated_skus.issubset(dim_skus)}")

print(f"\nCustomers:")
print(f"  Generated: {generated_customers}")
print(f"  All in dimension: {generated_customers.issubset(dim_customers)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Write New Events to Volume

# COMMAND ----------

# Clear existing POS files and write new aligned events
import json

VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/data/pos"

# List existing files
existing_files = dbutils.fs.ls(VOLUME_PATH)
print(f"Existing files: {len(existing_files)}")

# Generate new batch with aligned dimensions
pos_gen = create_pos_generator(
    spark=spark,
    catalog=CATALOG,
    schema=SCHEMA,
    use_dimensions=True,
    batch_size=100
)

# Write batch
file_path = pos_gen.write_batch_dbutils(dbutils, num_events=100, file_prefix="pos_aligned")
print(f"✅ Wrote new batch to: {file_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: Verify Written Data

# COMMAND ----------

# Read the new file and verify content
new_files = dbutils.fs.ls(VOLUME_PATH)
print(f"Files in volume: {len(new_files)}")

# Read newest file
newest_file = max(new_files, key=lambda f: f.modificationTime)
print(f"\nNewest file: {newest_file.path}")

# Read content
content = dbutils.fs.head(newest_file.path, 2000)
print("\nSample content (first 2000 chars):")
print(content[:1000])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 7: Re-run Pipeline
# MAGIC 
# MAGIC After generating new aligned events:
# MAGIC 1. Re-run the DLT pipeline (bronze → silver → gold)
# MAGIC 2. The new events should have proper dimension key joins

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 8: Validate Improved Join Rates (After Pipeline Run)

# COMMAND ----------

# Check null rates in silver table after new data flows through
try:
    silver_df = spark.table(f"{CATALOG}.{SCHEMA}.silver_transactions_unified")
    
    from pyspark.sql.functions import count, when, col, sum as spark_sum
    
    # Filter to recent data (dimension-aligned)
    recent_silver = silver_df.filter(col("_source_file").contains("pos_aligned"))
    
    if recent_silver.count() > 0:
        quality_stats = recent_silver.agg(
            count("*").alias("total_rows"),
            spark_sum(when(col("product_key").isNull(), 1).otherwise(0)).alias("null_product_key"),
            spark_sum(when(col("location_key").isNull(), 1).otherwise(0)).alias("null_location_key"),
            spark_sum(when(col("customer_key").isNull(), 1).otherwise(0)).alias("null_customer_key")
        ).collect()[0]
        
        total = quality_stats["total_rows"]
        
        print("📊 Dimension Alignment Results (new data):")
        print("=" * 60)
        print(f"Total rows from aligned generator: {total:,}")
        print(f"\nNull dimension key rates:")
        print(f"  - product_key: {quality_stats['null_product_key']:,} ({100*quality_stats['null_product_key']/total:.1f}%)")
        print(f"  - location_key: {quality_stats['null_location_key']:,} ({100*quality_stats['null_location_key']/total:.1f}%)")
        print(f"  - customer_key: {quality_stats['null_customer_key']:,} ({100*quality_stats['null_customer_key']/total:.1f}%)")
        
        print("\n🎯 Expected Results:")
        print("  - product_key null rate: ~0% (SKUs from dimension)")
        print("  - location_key null rate: 0% (store IDs from dimension)")
        print("  - customer_key null rate: ~30% (guest checkouts only)")
    else:
        print("⚠️ No data from aligned generator found yet.")
        print("   Run the DLT pipeline after generating new events.")
        
except Exception as e:
    print(f"⚠️ Cannot validate: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Stage 6 Complete!

# COMMAND ----------

print("""
╔══════════════════════════════════════════════════════════════════╗
║                    STAGE 6 VALIDATION                            ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  DimensionLoader Created:                                        ║
║  ├── Loads SKUs from gold_product_dim                            ║
║  ├── Loads store IDs from gold_location_dim                      ║
║  ├── Loads customer IDs from gold_customer_dim                   ║
║  └── Provides fallback static data for local testing             ║
║                                                                  ║
║  POS Generator Updated:                                          ║
║  ├── Now uses DimensionLoader for real values                    ║
║  ├── SKUs: SKU_000001 format (matches dimension)                 ║
║  ├── Store IDs: LOC_001 format (matches dimension)               ║
║  ├── Customer IDs: CUST_00000001 format (matches dimension)      ║
║  └── 30% guest checkout rate preserved                           ║
║                                                                  ║
║  Expected Join Results After Pipeline Re-run:                    ║
║  ├── product_key: ~0% null (vs 100% before)                      ║
║  ├── location_key: 0% null (vs 100% before)                      ║
║  ├── customer_key: ~30% null (guest checkouts, same as before)   ║
║  └── channel_key: Needs silver pipeline update for STORE_POS     ║
║                                                                  ║
║  Next Steps:                                                     ║
║  1. Run this notebook to generate aligned events                 ║
║  2. Re-run DLT pipeline                                          ║
║  3. Verify improved null rates                                   ║
║  4. Continue to Stage 7 (remaining generators)                   ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
