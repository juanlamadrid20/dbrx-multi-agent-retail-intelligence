# Databricks notebook source
# MAGIC %md
# MAGIC # Stage 2: Test POS Event Generator
# MAGIC 
# MAGIC This notebook tests the POS event generator by:
# MAGIC 1. Generating sample transactions
# MAGIC 2. Writing them to the Volume
# MAGIC 3. Reading back and validating the data

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup: Add generators to path

# COMMAND ----------

import sys
import os

# Add the generators package to path
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
repo_root = "/Workspace" + "/".join(notebook_path.split("/")[:-2])
generators_path = f"{repo_root}/generators"

# For local development, use relative path
sys.path.insert(0, generators_path)
sys.path.insert(0, f"{repo_root}")

print(f"Added to path: {generators_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Import and Configure Generator

# COMMAND ----------

from generators.pos_generator import POSEventGenerator, create_pos_generator

# Configuration
CATALOG = "juan_dev"
SCHEMA = "retail"
VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/data/pos"

# Create generator with seed for reproducibility
generator = POSEventGenerator(
    volume_path=VOLUME_PATH,
    batch_size=10,  # Small batch for testing
    random_seed=42
)

print(f"✅ Generator created")
print(f"   Volume path: {VOLUME_PATH}")
print(f"   Batch size: {generator.batch_size}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Sample Events (Preview)

# COMMAND ----------

# Generate a few events to preview (don't write yet)
sample_events = generator.generate_batch(3)

# Display sample
import json
for i, event in enumerate(sample_events, 1):
    print(f"\n--- Transaction {i} ---")
    print(json.dumps(event, indent=2))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write Events to Volume

# COMMAND ----------

# Write batch to volume using dbutils
file_path = generator.write_batch_dbutils(dbutils, num_events=10)
print(f"✅ Wrote batch to: {file_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify File in Volume

# COMMAND ----------

# List files in pos volume
print("📁 Files in POS volume:")
print("=" * 50)

files = dbutils.fs.ls(VOLUME_PATH)
for f in files:
    print(f"  {f.name} ({f.size} bytes)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read Back and Validate

# COMMAND ----------

# Read the JSON file using Spark
df = spark.read.json(VOLUME_PATH)

print(f"✅ Read {df.count()} transactions from volume")
print(f"\nSchema:")
df.printSchema()

# COMMAND ----------

# Display the data
display(df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validate Data Structure

# COMMAND ----------

# Expand items array to validate line item structure
from pyspark.sql.functions import explode, col

items_df = df.select(
    col("transaction_id"),
    col("store_id"),
    col("customer_id"),
    explode(col("items")).alias("item")
).select(
    "transaction_id",
    "store_id", 
    "customer_id",
    col("item.sku").alias("sku"),
    col("item.qty").alias("qty"),
    col("item.price").alias("price"),
    col("item.discount").alias("discount")
)

print(f"✅ Expanded to {items_df.count()} line items")
display(items_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary Statistics

# COMMAND ----------

# Transaction summary
print("📊 Transaction Summary:")
print("=" * 50)

summary = df.agg({
    "transaction_id": "count"
}).collect()[0]

print(f"  Total transactions: {summary['count(transaction_id)']}")

# Store distribution
print("\n📍 Store Distribution:")
display(df.groupBy("store_id").count().orderBy("count", ascending=False))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Larger Batch (Optional)

# COMMAND ----------

# Uncomment to generate a larger batch for pipeline testing
# file_path = generator.write_batch_dbutils(dbutils, num_events=100)
# print(f"✅ Wrote 100 transactions to: {file_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cleanup (Optional)

# COMMAND ----------

# Uncomment to clean up test files
# for f in dbutils.fs.ls(VOLUME_PATH):
#     dbutils.fs.rm(f.path)
# print("🧹 Cleaned up test files")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Stage 2 Complete!

# COMMAND ----------

print("""
╔══════════════════════════════════════════════════════════════════╗
║                    STAGE 2 COMPLETE                              ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  ✅ base_generator.py - Common generator functionality           ║
║  ✅ pos_generator.py - POS transaction generator                 ║
║  ✅ Events written to /Volumes/juan_dev/retail/data/pos/         ║
║  ✅ Data readable by Spark as JSON                               ║
║                                                                  ║
║  Event Structure:                                                ║
║  ├── transaction_id (string)                                     ║
║  ├── store_id (string)                                           ║
║  ├── register_id (int)                                           ║
║  ├── timestamp (string - ISO format)                             ║
║  ├── customer_id (string, nullable)                              ║
║  ├── items (array)                                               ║
║  │   ├── sku (string)                                            ║
║  │   ├── qty (int)                                               ║
║  │   ├── price (float)                                           ║
║  │   └── discount (float)                                        ║
║  ├── payment_method (string)                                     ║
║  └── associate_id (string)                                       ║
║                                                                  ║
║  Next Step: Stage 3 - Create Bronze Pipeline with Auto Loader    ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
