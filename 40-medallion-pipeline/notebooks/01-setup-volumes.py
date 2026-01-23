# Databricks notebook source
# MAGIC %md
# MAGIC # Stage 1: Setup Unity Catalog Volumes
# MAGIC 
# MAGIC This notebook creates the Volume structure for the Medallion Pipeline.
# MAGIC 
# MAGIC **Volumes Created:**
# MAGIC - `/Volumes/juan_dev/retail/data/pos/` - POS transactions
# MAGIC - `/Volumes/juan_dev/retail/data/ecommerce/` - E-commerce orders
# MAGIC - `/Volumes/juan_dev/retail/data/inventory/` - Inventory movements
# MAGIC - `/Volumes/juan_dev/retail/data/clickstream/` - Web/app events
# MAGIC - `/Volumes/juan_dev/retail/data/customers/` - Customer records
# MAGIC - `/Volumes/juan_dev/retail/data/products/` - Product catalog
# MAGIC - `/Volumes/juan_dev/retail/checkpoints/` - Auto Loader checkpoints

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Configuration
CATALOG = "juan_dev"
SCHEMA = "retail"

# Volume names
DATA_VOLUME = "data"
CHECKPOINT_VOLUME = "checkpoints"

# Source subdirectories (will be created inside data volume)
SOURCE_DIRS = [
    "pos",
    "ecommerce", 
    "inventory",
    "clickstream",
    "customers",
    "products"
]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Volumes

# COMMAND ----------

# Create data volume if it doesn't exist
spark.sql(f"""
    CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.{DATA_VOLUME}
    COMMENT 'Raw event data for medallion pipeline ingestion'
""")
print(f"✅ Created volume: {CATALOG}.{SCHEMA}.{DATA_VOLUME}")

# COMMAND ----------

# Create checkpoints volume if it doesn't exist
spark.sql(f"""
    CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.{CHECKPOINT_VOLUME}
    COMMENT 'Auto Loader schema and checkpoint storage'
""")
print(f"✅ Created volume: {CATALOG}.{SCHEMA}.{CHECKPOINT_VOLUME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Source Subdirectories

# COMMAND ----------

import os

# Base path for data volume
data_volume_path = f"/Volumes/{CATALOG}/{SCHEMA}/{DATA_VOLUME}"

# Create subdirectories for each source
for source_dir in SOURCE_DIRS:
    dir_path = f"{data_volume_path}/{source_dir}"
    
    # Use dbutils to create directory
    try:
        dbutils.fs.mkdirs(dir_path)
        print(f"✅ Created directory: {dir_path}")
    except Exception as e:
        print(f"⚠️ Directory may already exist: {dir_path} - {str(e)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Volume Structure

# COMMAND ----------

# List the data volume contents
print("📁 Data Volume Structure:")
print("=" * 50)

try:
    contents = dbutils.fs.ls(data_volume_path)
    for item in contents:
        print(f"  {item.name}")
except Exception as e:
    print(f"❌ Error listing volume: {e}")

# COMMAND ----------

# List checkpoint volume
checkpoint_volume_path = f"/Volumes/{CATALOG}/{SCHEMA}/{CHECKPOINT_VOLUME}"
print(f"\n📁 Checkpoint Volume: {checkpoint_volume_path}")
print("=" * 50)

try:
    contents = dbutils.fs.ls(checkpoint_volume_path)
    if contents:
        for item in contents:
            print(f"  {item.name}")
    else:
        print("  (empty - will be populated by Auto Loader)")
except Exception as e:
    print(f"  (empty or not accessible yet)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print("""
╔══════════════════════════════════════════════════════════════════╗
║                    STAGE 1 COMPLETE                              ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  Volumes Created:                                                ║
║  ├── /Volumes/juan_dev/retail/data/                              ║
║  │   ├── pos/           <- POS transactions                      ║
║  │   ├── ecommerce/     <- Online orders                         ║
║  │   ├── inventory/     <- Inventory movements                   ║
║  │   ├── clickstream/   <- Web/app events                        ║
║  │   ├── customers/     <- Customer records                      ║
║  │   └── products/      <- Product catalog                       ║
║  └── /Volumes/juan_dev/retail/checkpoints/                       ║
║                                                                  ║
║  Next Step: Stage 2 - Create POS Event Generator                 ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validation Queries
# MAGIC 
# MAGIC Run these to verify the setup:

# COMMAND ----------

# Verify volumes exist in Unity Catalog
display(spark.sql(f"""
    SHOW VOLUMES IN {CATALOG}.{SCHEMA}
"""))

# COMMAND ----------

# Get volume details
display(spark.sql(f"""
    DESCRIBE VOLUME {CATALOG}.{SCHEMA}.{DATA_VOLUME}
"""))
