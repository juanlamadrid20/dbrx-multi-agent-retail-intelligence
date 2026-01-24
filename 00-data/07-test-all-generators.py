# Databricks notebook source
# MAGIC %md
# MAGIC # Stage 7: Test All Generators
# MAGIC 
# MAGIC This notebook tests all event generators and populates volumes:
# MAGIC 
# MAGIC 1. Test each generator
# MAGIC 2. Generate sample events for each source
# MAGIC 3. Write to volumes
# MAGIC 4. Verify bronze pipeline can ingest all sources

# COMMAND ----------
# MAGIC %load_ext autoreload
# MAGIC %autoreload 2
# Enables autoreload; learn more at https://docs.databricks.com/en/files/workspace-modules.html#autoreload-for-python-modules
# To disable autoreload; run %autoreload 0

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

CATALOG = "juan_dev"
SCHEMA = "retail"

# Add 00-data directory to path for generators and master_data
import sys
import os
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
data_dir = "/Workspace" + "/".join(notebook_path.split("/")[:-1])
sys.path.insert(0, data_dir)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Dimension Data

# COMMAND ----------

from generators import create_dimension_loader

loader = create_dimension_loader(spark, CATALOG, SCHEMA)
print(loader.summary())

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 1: POS Generator

# COMMAND ----------

from generators import create_pos_generator

pos_gen = create_pos_generator(spark, CATALOG, SCHEMA, batch_size=50)

# Generate sample
pos_events = pos_gen.generate_batch(3)
print("POS Transaction Sample:")
for e in pos_events:
    print(f"  {e['transaction_id']}: {e['store_id']}, items={len(e['items'])}")

# Write batch
pos_file = pos_gen.write_batch_dbutils(dbutils, num_events=100)
print(f"\n✅ Wrote 100 POS events to: {pos_file}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 2: E-commerce Generator

# COMMAND ----------

from generators import create_ecommerce_generator

ecom_gen = create_ecommerce_generator(spark, CATALOG, SCHEMA, batch_size=50)

# Generate sample
ecom_events = ecom_gen.generate_batch(3)
print("E-commerce Order Sample:")
for e in ecom_events:
    print(f"  {e['order_id']}: {e['channel']}, items={len(e['items'])}, customer={e['customer_id']}")

# Write batch
ecom_file = ecom_gen.write_batch_dbutils(dbutils, num_events=100)
print(f"\n✅ Wrote 100 e-commerce events to: {ecom_file}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 3: Inventory Generator

# COMMAND ----------

from generators import create_inventory_generator

inv_gen = create_inventory_generator(spark, CATALOG, SCHEMA, batch_size=50)

# Generate sample
inv_events = inv_gen.generate_batch(5)
print("Inventory Movement Sample:")
for e in inv_events:
    print(f"  {e['movement_id']}: {e['movement_type']}, {e['location_id']}, {e['sku']}, qty={e['quantity']}")

# Write batch
inv_file = inv_gen.write_batch_dbutils(dbutils, num_events=100)
print(f"\n✅ Wrote 100 inventory events to: {inv_file}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 4: Clickstream Generator

# COMMAND ----------

from generators import create_clickstream_generator

click_gen = create_clickstream_generator(spark, CATALOG, SCHEMA, batch_size=50)

# Generate sample
click_events = click_gen.generate_batch(5)
print("Clickstream Event Sample:")
for e in click_events:
    print(f"  {e['event_id']}: {e['event_type']}, {e['channel']}, page={e['page_url'][:30]}...")

# Write batch
click_file = click_gen.write_batch_dbutils(dbutils, num_events=200)
print(f"\n✅ Wrote 200 clickstream events to: {click_file}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Volume Contents

# COMMAND ----------

import json

VOLUME_BASE = f"/Volumes/{CATALOG}/{SCHEMA}/data"

sources = ["pos", "ecommerce", "inventory", "clickstream"]

print("📁 Volume Contents:")
print("=" * 60)

for source in sources:
    path = f"{VOLUME_BASE}/{source}"
    try:
        files = dbutils.fs.ls(path)
        total_size = sum(f.size for f in files)
        print(f"\n{source}/")
        print(f"  Files: {len(files)}")
        print(f"  Total size: {total_size:,} bytes")
        if files:
            newest = max(files, key=lambda f: f.modificationTime)
            print(f"  Newest: {newest.name}")
    except Exception as e:
        print(f"\n{source}/")
        print(f"  ⚠️ Error: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Preview Data from Each Source

# COMMAND ----------

# Read and preview each source as JSON
for source in sources:
    path = f"{VOLUME_BASE}/{source}"
    try:
        files = dbutils.fs.ls(path)
        if files:
            newest = max(files, key=lambda f: f.modificationTime)
            content = dbutils.fs.head(newest.path, 500)
            print(f"\n{'='*60}")
            print(f"📄 {source.upper()} - {newest.name}")
            print(f"{'='*60}")
            print(content[:400] + "..." if len(content) > 400 else content)
    except Exception as e:
        print(f"\n{source}: Error - {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run Bronze Pipeline
# MAGIC 
# MAGIC Now run the DLT pipeline to ingest all sources into Bronze tables.
# MAGIC 
# MAGIC **Tables to verify after pipeline runs:**
# MAGIC - `bronze_pos_transactions`
# MAGIC - `bronze_ecommerce_orders`
# MAGIC - `bronze_inventory_movements`
# MAGIC - `bronze_clickstream_events`

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validate Bronze Tables (After Pipeline Runs)

# COMMAND ----------

bronze_tables = [
    "bronze_pos_transactions",
    "bronze_ecommerce_orders",
    "bronze_inventory_movements",
    "bronze_clickstream_events"
]

print("📋 Bronze Table Status:")
print("=" * 60)

for table in bronze_tables:
    try:
        df = spark.table(f"{CATALOG}.{SCHEMA}.{table}")
        count = df.count()
        print(f"✅ {table}: {count:,} rows")
    except Exception as e:
        print(f"⚠️ {table}: Not found (run pipeline first)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Sample Data from Bronze Tables

# COMMAND ----------

for table in bronze_tables:
    try:
        df = spark.table(f"{CATALOG}.{SCHEMA}.{table}")
        print(f"\n{'='*60}")
        print(f"📊 {table}")
        print(f"{'='*60}")
        display(df.limit(3))
    except Exception as e:
        pass

# COMMAND ----------

# MAGIC %md
# MAGIC ## Stage 7 Complete!

# COMMAND ----------

print("""
╔══════════════════════════════════════════════════════════════════╗
║                    STAGE 7 VALIDATION                            ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  Generators Created:                                             ║
║  ├── POSEventGenerator          -> pos/                          ║
║  ├── EcommerceEventGenerator    -> ecommerce/                    ║
║  ├── InventoryEventGenerator    -> inventory/                    ║
║  └── ClickstreamEventGenerator  -> clickstream/                  ║
║                                                                  ║
║  All generators use DimensionLoader for:                         ║
║  ├── Real SKUs from gold_product_dim                             ║
║  ├── Real location IDs from gold_location_dim                    ║
║  └── Real customer IDs from gold_customer_dim                    ║
║                                                                  ║
║  Bronze Tables Added:                                            ║
║  ├── bronze_pos_transactions                                     ║
║  ├── bronze_ecommerce_orders                                     ║
║  ├── bronze_inventory_movements                                  ║
║  └── bronze_clickstream_events                                   ║
║                                                                  ║
║  Next Step: Stage 8 - Complete Silver/Gold + Documentation       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
