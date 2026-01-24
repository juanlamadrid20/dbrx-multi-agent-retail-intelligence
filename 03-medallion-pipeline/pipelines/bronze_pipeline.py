# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Pipeline - Raw Data Ingestion
# MAGIC 
# MAGIC This pipeline uses Auto Loader to ingest raw event files from Unity Catalog Volumes
# MAGIC into Bronze tables. Bronze tables contain raw, unprocessed data with metadata columns.
# MAGIC 
# MAGIC **Tables (Stage 3 - POS only):**
# MAGIC - `bronze_pos_transactions` - Raw POS transaction events
# MAGIC 
# MAGIC **Future tables (Stage 6):**
# MAGIC - `bronze_ecommerce_orders`
# MAGIC - `bronze_inventory_movements`
# MAGIC - `bronze_clickstream_events`
# MAGIC - `bronze_customer_records`
# MAGIC - `bronze_product_catalog`

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pipeline Configuration

# COMMAND ----------

from pyspark import pipelines as dp
from pyspark.sql.functions import current_timestamp, col

# Volume paths
VOLUME_BASE = "/Volumes/juan_dev/retail/data"
CHECKPOINT_BASE = "/Volumes/juan_dev/retail/checkpoints"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze Tables

# COMMAND ----------

# MAGIC %md
# MAGIC ### POS Transactions (Stage 3)

# COMMAND ----------

@dp.table(
    name="bronze_pos_transactions",
    comment="Raw POS transaction events from store registers. Source: /Volumes/juan_dev/retail/data/pos/",
    table_properties={
        "quality": "bronze",
        "pipelines.reset.allowed": "true"
    }
)
def bronze_pos_transactions():
    """
    Ingest raw POS transaction JSON files from Volume using Auto Loader.
    
    Source schema (from pos_generator.py):
        - transaction_id: string
        - store_id: string
        - register_id: int
        - timestamp: string (ISO format)
        - customer_id: string (nullable)
        - items: array<struct<sku, qty, price, discount>>
        - payment_method: string
        - associate_id: string
    
    Added metadata columns:
        - _ingestion_timestamp: timestamp when record was ingested
        - _source_file: path to source file
    """
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", f"{CHECKPOINT_BASE}/bronze_pos_schema")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .load(f"{VOLUME_BASE}/pos/")
        .withColumn("_ingestion_timestamp", current_timestamp())
        .withColumn("_source_file", col("_metadata.file_path"))
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ### E-commerce Orders (Stage 7)

# COMMAND ----------

@dp.table(
    name="bronze_ecommerce_orders",
    comment="Raw e-commerce order events from web and mobile. Source: /Volumes/juan_dev/retail/data/ecommerce/",
    table_properties={
        "quality": "bronze",
        "pipelines.reset.allowed": "true"
    }
)
def bronze_ecommerce_orders():
    """
    Ingest raw e-commerce order JSON files from Volume using Auto Loader.
    
    Source schema (from ecommerce_generator.py):
        - order_id: string
        - channel: string (WEB_DESKTOP, WEB_MOBILE, APP_IOS, APP_ANDROID)
        - timestamp: string (ISO format)
        - customer_id: string
        - shipping_address: struct<city, state, zip>
        - shipping_method: string
        - items: array<struct<sku, qty, price, discount>>
        - payment_method: string
        - promo_code: string (nullable)
    """
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", f"{CHECKPOINT_BASE}/bronze_ecommerce_schema")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .load(f"{VOLUME_BASE}/ecommerce/")
        .withColumn("_ingestion_timestamp", current_timestamp())
        .withColumn("_source_file", col("_metadata.file_path"))
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ### Inventory Movements (Stage 7)

# COMMAND ----------

@dp.table(
    name="bronze_inventory_movements",
    comment="Raw inventory movement events. Source: /Volumes/juan_dev/retail/data/inventory/",
    table_properties={
        "quality": "bronze",
        "pipelines.reset.allowed": "true"
    }
)
def bronze_inventory_movements():
    """
    Ingest raw inventory movement JSON files from Volume using Auto Loader.
    
    Source schema (from inventory_generator.py):
        - movement_id: string
        - movement_type: string (receipt, transfer_in, transfer_out, sale, return, adjustment)
        - timestamp: string (ISO format)
        - location_id: string
        - sku: string
        - quantity: int (positive or negative)
        - reason_code: string
        - reference_id: string (nullable)
        - cost_per_unit: double (nullable)
    """
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", f"{CHECKPOINT_BASE}/bronze_inventory_schema")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .load(f"{VOLUME_BASE}/inventory/")
        .withColumn("_ingestion_timestamp", current_timestamp())
        .withColumn("_source_file", col("_metadata.file_path"))
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ### Clickstream Events (Stage 7)

# COMMAND ----------

@dp.table(
    name="bronze_clickstream_events",
    comment="Raw clickstream events from web and mobile. Source: /Volumes/juan_dev/retail/data/clickstream/",
    table_properties={
        "quality": "bronze",
        "pipelines.reset.allowed": "true"
    }
)
def bronze_clickstream_events():
    """
    Ingest raw clickstream JSON files from Volume using Auto Loader.
    
    Source schema (from clickstream_generator.py):
        - event_id: string
        - session_id: string
        - event_type: string (page_view, product_view, add_to_cart, etc.)
        - timestamp: string (ISO format)
        - channel: string (WEB_DESKTOP, WEB_MOBILE, APP_IOS, APP_ANDROID)
        - customer_id: string (nullable)
        - page_url: string
        - product_sku: string (nullable)
        - device_type: string
        - browser: string
        - referrer: string (nullable)
        - cart: struct<items, value> (nullable)
    """
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", f"{CHECKPOINT_BASE}/bronze_clickstream_schema")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .load(f"{VOLUME_BASE}/clickstream/")
        .withColumn("_ingestion_timestamp", current_timestamp())
        .withColumn("_source_file", col("_metadata.file_path"))
    )
