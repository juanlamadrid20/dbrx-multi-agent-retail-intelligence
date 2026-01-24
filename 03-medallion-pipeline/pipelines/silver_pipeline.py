# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Pipeline - Data Cleansing & Validation
# MAGIC 
# MAGIC This pipeline transforms Bronze data into Silver by:
# MAGIC - Exploding nested arrays into rows
# MAGIC - Joining with dimension tables for enrichment
# MAGIC - Applying data quality expectations
# MAGIC - Calculating derived columns
# MAGIC 
# MAGIC **Tables (Stage 4 - POS only):**
# MAGIC - `silver_transactions_unified` - Cleansed and enriched transaction line items
# MAGIC 
# MAGIC **Future tables (Stage 7):**
# MAGIC - `silver_inventory_positions`
# MAGIC - `silver_customer_events`
# MAGIC - `silver_customers_validated`
# MAGIC - `silver_products_validated`

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pipeline Configuration

# COMMAND ----------

from pyspark import pipelines as dp
from pyspark.sql.functions import (
    col, explode, lit, coalesce, current_timestamp,
    date_format, when, concat_ws
)

# Catalog configuration
CATALOG = "juan_dev"
SCHEMA = "retail"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver Tables

# COMMAND ----------

# MAGIC %md
# MAGIC ### Transactions Unified (Stage 4)
# MAGIC 
# MAGIC Transforms POS transactions into enriched line items:
# MAGIC - Explodes items array into individual rows
# MAGIC - Joins with product dimension for product_key and pricing
# MAGIC - Joins with location dimension for location_key and tax rate
# MAGIC - Joins with customer dimension for customer_key
# MAGIC - Calculates line totals, tax, and margin

# COMMAND ----------

@dp.table(
    name="silver_transactions_unified",
    comment="Cleansed and enriched transaction line items from POS. Joined with dimensions.",
    table_properties={
        "quality": "silver",
        "pipelines.reset.allowed": "true"
    }
)
@dp.expect("valid_quantity", "qty > 0")
@dp.expect("valid_price", "price >= 0")
@dp.expect_or_drop("has_sku", "sku IS NOT NULL")
def silver_transactions_unified():
    """
    Transform bronze POS transactions into enriched line items.
    
    Input: bronze_pos_transactions (nested items array)
    Output: Flattened line items with dimension keys and calculations
    
    Joins:
        - gold_product_dim: Get product_key, base_price, unit_cost
        - gold_location_dim: Get location_key, state_tax_rate
        - gold_customer_dim: Get customer_key
    
    Calculations:
        - line_total: qty * (price - discount)
        - tax_amount: line_total * tax_rate
        - gross_margin: line_total - (qty * unit_cost)
    """
    # Read bronze table as stream
    bronze = spark.readStream.table(f"{CATALOG}.{SCHEMA}.bronze_pos_transactions")
    
    # Reference dimension tables (static lookups)
    # Note: These are the existing gold dimension tables from batch processing
    products = spark.table(f"{CATALOG}.{SCHEMA}.gold_product_dim").select(
        col("product_key"),
        col("sku"),
        col("base_price"),
        col("unit_cost"),
        col("category_level_1"),
        col("brand")
    )
    
    locations = spark.table(f"{CATALOG}.{SCHEMA}.gold_location_dim").select(
        col("location_key"),
        col("location_id"),
        col("location_type"),
        coalesce(col("state_tax_rate"), lit(0.07)).alias("state_tax_rate")
    )
    
    customers = spark.table(f"{CATALOG}.{SCHEMA}.gold_customer_dim").filter(
        col("is_current") == True
    ).select(
        col("customer_key"),
        col("customer_id"),
        col("segment"),
        col("preferred_channel")
    )
    
    channels = spark.table(f"{CATALOG}.{SCHEMA}.gold_channel_dim").select(
        col("channel_key"),
        col("channel_code")
    )
    
    # Explode items array into individual line items
    exploded = bronze.select(
        col("transaction_id"),
        col("store_id"),
        col("register_id"),
        col("timestamp"),
        col("customer_id"),
        col("payment_method"),
        col("associate_id"),
        col("_ingestion_timestamp"),
        col("_source_file"),
        explode(col("items")).alias("item")
    ).select(
        "*",
        col("item.sku").alias("sku"),
        col("item.qty").alias("qty"),
        col("item.price").alias("price"),
        col("item.discount").alias("discount")
    ).drop("item")
    
    # Join with dimensions
    # Note: store_id maps to location_id in gold_location_dim
    # Drop duplicate join keys after each join to avoid ambiguous references
    enriched = (
        exploded
        # Join products - left join since generated SKUs may not match
        .join(
            products,
            exploded.sku == products.sku,
            "left"
        )
        .drop(products.sku)  # Drop duplicate sku column from products
        # Join locations - store_id should match location_id
        .join(
            locations,
            exploded.store_id == locations.location_id,
            "left"
        )
        .drop(locations.location_id)  # Drop duplicate location_id column
        # Join customers - customer_id matches
        .join(
            customers,
            exploded.customer_id == customers.customer_id,
            "left"
        )
        .drop(customers.customer_id)  # Drop duplicate customer_id column
        # Join channels - POS is always "STORE_POS" channel
        .join(
            channels,
            channels.channel_code == "STORE_POS",
            "left"
        )
        .drop(channels.channel_code)  # Drop channel_code after join
    )
    
    # Calculate derived columns
    result = enriched.select(
        # Transaction identifiers
        col("transaction_id"),
        concat_ws("-", col("transaction_id"), col("sku")).alias("line_item_id"),
        
        # Dimension keys (from joins)
        col("customer_key"),
        col("product_key"),
        col("location_key"),
        col("channel_key"),
        
        # Date/time keys
        date_format(col("timestamp"), "yyyyMMdd").cast("int").alias("date_key"),
        date_format(col("timestamp"), "HHmm").cast("int").alias("time_key"),
        
        # Original transaction data
        col("store_id"),
        col("register_id"),
        col("timestamp"),
        col("sku"),
        col("qty"),
        col("price"),
        coalesce(col("discount"), lit(0.0)).alias("discount"),
        col("payment_method"),
        col("associate_id"),
        
        # Enriched data from dimensions
        col("category_level_1").alias("product_category"),
        col("brand").alias("product_brand"),
        col("location_type"),
        col("segment").alias("customer_segment"),
        col("state_tax_rate"),
        coalesce(col("unit_cost"), col("price") * 0.4).alias("unit_cost"),  # Default 40% cost if not found
        
        # Calculated fields
        (col("qty") * (col("price") - coalesce(col("discount"), lit(0.0)))).alias("line_total"),
        
        # Metadata
        col("_ingestion_timestamp"),
        col("_source_file"),
        current_timestamp().alias("_processing_timestamp")
    )
    
    # Add tax and margin calculations
    final = result.withColumn(
        "tax_amount",
        col("line_total") * col("state_tax_rate")
    ).withColumn(
        "gross_margin",
        col("line_total") - (col("qty") * col("unit_cost"))
    )
    
    return final

# COMMAND ----------

# MAGIC %md
# MAGIC ### E-commerce Orders Unified (Stage 7)

# COMMAND ----------

@dp.table(
    name="silver_ecommerce_unified",
    comment="Cleansed and enriched e-commerce order line items. Joined with dimensions.",
    table_properties={
        "quality": "silver",
        "pipelines.reset.allowed": "true"
    }
)
@dp.expect("valid_quantity", "qty > 0")
@dp.expect("valid_price", "price >= 0")
@dp.expect_or_drop("has_sku", "sku IS NOT NULL")
def silver_ecommerce_unified():
    """Transform bronze e-commerce orders into enriched line items."""
    from pyspark.sql.functions import explode
    
    bronze = spark.readStream.table(f"{CATALOG}.{SCHEMA}.bronze_ecommerce_orders")
    
    products = spark.table(f"{CATALOG}.{SCHEMA}.gold_product_dim").select(
        col("product_key"), col("sku"), col("base_price"), col("unit_cost"),
        col("category_level_1"), col("brand")
    )
    
    customers = spark.table(f"{CATALOG}.{SCHEMA}.gold_customer_dim").filter(
        col("is_current") == True
    ).select(col("customer_key"), col("customer_id"), col("segment"))
    
    channels = spark.table(f"{CATALOG}.{SCHEMA}.gold_channel_dim").select(
        col("channel_key"), col("channel_code")
    )
    
    # Explode items
    exploded = bronze.select(
        col("order_id"),
        col("channel"),
        col("timestamp"),
        col("customer_id"),
        col("shipping_address"),
        col("shipping_method"),
        col("payment_method"),
        col("promo_code"),
        col("_ingestion_timestamp"),
        col("_source_file"),
        explode(col("items")).alias("item")
    ).select(
        "*",
        col("item.sku").alias("sku"),
        col("item.qty").alias("qty"),
        col("item.price").alias("price"),
        col("item.discount").alias("discount")
    ).drop("item")
    
    # Join dimensions
    enriched = (
        exploded
        .join(products, exploded.sku == products.sku, "left").drop(products.sku)
        .join(customers, exploded.customer_id == customers.customer_id, "left").drop(customers.customer_id)
        .join(channels, exploded.channel == channels.channel_code, "left").drop(channels.channel_code)
    )
    
    return enriched.select(
        col("order_id").alias("transaction_id"),
        concat_ws("-", col("order_id"), col("sku")).alias("line_item_id"),
        col("customer_key"),
        col("product_key"),
        date_format(col("timestamp"), "yyyyMMdd").cast("int").alias("date_key"),
        date_format(col("timestamp"), "HHmm").cast("int").alias("time_key"),
        lit(None).cast("int").alias("location_key"),  # Online - no location
        col("channel_key"),
        col("channel").alias("channel_code"),
        col("sku"),
        col("qty"),
        col("price"),
        coalesce(col("discount"), lit(0.0)).alias("discount"),
        col("shipping_method"),
        col("payment_method"),
        col("promo_code"),
        (col("qty") * (col("price") - coalesce(col("discount"), lit(0.0)))).alias("line_total"),
        col("_ingestion_timestamp"),
        col("_source_file"),
        current_timestamp().alias("_processing_timestamp")
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ### Inventory Movements Validated (Stage 7)

# COMMAND ----------

@dp.table(
    name="silver_inventory_movements",
    comment="Validated inventory movements with dimension keys.",
    table_properties={
        "quality": "silver",
        "pipelines.reset.allowed": "true"
    }
)
@dp.expect("valid_sku", "sku IS NOT NULL")
@dp.expect("valid_location", "location_id IS NOT NULL")
def silver_inventory_movements():
    """Transform bronze inventory movements with dimension lookups."""
    bronze = spark.readStream.table(f"{CATALOG}.{SCHEMA}.bronze_inventory_movements")
    
    products = spark.table(f"{CATALOG}.{SCHEMA}.gold_product_dim").select(
        col("product_key"), col("sku")
    )
    
    locations = spark.table(f"{CATALOG}.{SCHEMA}.gold_location_dim").select(
        col("location_key"), col("location_id")
    )
    
    enriched = (
        bronze
        .join(products, bronze.sku == products.sku, "left").drop(products.sku)
        .join(locations, bronze.location_id == locations.location_id, "left").drop(locations.location_id)
    )
    
    return enriched.select(
        col("movement_id"),
        col("movement_type"),
        col("timestamp"),
        date_format(col("timestamp"), "yyyyMMdd").cast("int").alias("date_key"),
        col("product_key"),
        col("location_key"),
        col("sku"),
        col("location_id"),
        col("quantity"),
        col("reason_code"),
        col("reference_id"),
        col("cost_per_unit"),
        col("_ingestion_timestamp"),
        col("_source_file"),
        current_timestamp().alias("_processing_timestamp")
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ### Clickstream Events Enriched (Stage 7)

# COMMAND ----------

@dp.table(
    name="silver_clickstream_events",
    comment="Enriched clickstream events with session and customer data.",
    table_properties={
        "quality": "silver",
        "pipelines.reset.allowed": "true"
    }
)
@dp.expect("valid_event_type", "event_type IS NOT NULL")
def silver_clickstream_events():
    """Transform bronze clickstream events with dimension lookups."""
    bronze = spark.readStream.table(f"{CATALOG}.{SCHEMA}.bronze_clickstream_events")
    
    products = spark.table(f"{CATALOG}.{SCHEMA}.gold_product_dim").select(
        col("product_key"), col("sku").alias("product_sku_dim")
    )
    
    customers = spark.table(f"{CATALOG}.{SCHEMA}.gold_customer_dim").filter(
        col("is_current") == True
    ).select(col("customer_key"), col("customer_id").alias("customer_id_dim"))
    
    channels = spark.table(f"{CATALOG}.{SCHEMA}.gold_channel_dim").select(
        col("channel_key"), col("channel_code")
    )
    
    enriched = (
        bronze
        .join(products, bronze.product_sku == products.product_sku_dim, "left").drop(products.product_sku_dim)
        .join(customers, bronze.customer_id == customers.customer_id_dim, "left").drop(customers.customer_id_dim)
        .join(channels, bronze.channel == channels.channel_code, "left").drop(channels.channel_code)
    )
    
    return enriched.select(
        col("event_id"),
        col("session_id"),
        col("event_type"),
        col("timestamp"),
        date_format(col("timestamp"), "yyyyMMdd").cast("int").alias("date_key"),
        date_format(col("timestamp"), "HHmm").cast("int").alias("time_key"),
        col("channel_key"),
        col("channel"),
        col("customer_key"),
        col("customer_id"),
        col("product_key"),
        col("product_sku"),
        col("page_url"),
        col("device_type"),
        col("browser"),
        col("referrer"),
        col("cart"),
        col("_ingestion_timestamp"),
        col("_source_file"),
        current_timestamp().alias("_processing_timestamp")
    )
