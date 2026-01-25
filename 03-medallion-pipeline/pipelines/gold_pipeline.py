# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Pipeline - Business-Ready Tables
# MAGIC 
# MAGIC This pipeline creates Gold tables from:
# MAGIC - **Master Data**: Dimension tables derived from 00-data/master_data.py
# MAGIC - **Silver Streaming**: Fact tables from transformed events
# MAGIC 
# MAGIC **Architecture:**
# MAGIC ```
# MAGIC master_data.py ──────────────────────┐
# MAGIC                                      ▼
# MAGIC                              ┌──────────────────┐
# MAGIC                              │ Dimension Tables │
# MAGIC                              │ - gold_product_dim    │
# MAGIC                              │ - gold_location_dim   │
# MAGIC                              │ - gold_channel_dim    │
# MAGIC                              │ - gold_date_dim       │
# MAGIC                              │ - gold_time_dim       │
# MAGIC                              └──────────────────┘
# MAGIC                                      ▲
# MAGIC silver_*_unified ────────────────────┤
# MAGIC                                      ▼
# MAGIC                              ┌──────────────────┐
# MAGIC                              │   Fact Tables    │
# MAGIC                              │ - gold_sales_fact     │
# MAGIC                              │ - gold_inventory_fact │
# MAGIC                              │ - gold_cart_abandonment│
# MAGIC                              └──────────────────┘
# MAGIC ```
# MAGIC 
# MAGIC **No Circular Dependencies:**
# MAGIC - Dimension tables are created from master_data.py (static config)
# MAGIC - Fact tables are created from silver streaming data
# MAGIC - Generators don't need gold tables to exist first

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pipeline Configuration

# COMMAND ----------

from pyspark import pipelines as dp
from pyspark.sql.functions import (
    col, lit, coalesce, current_timestamp, when,
    concat, concat_ws, row_number, to_date
)
from pyspark.sql.types import (
    StructType, StructField, IntegerType, StringType, 
    DoubleType, BooleanType, DateType
)
from pyspark.sql.window import Window
from datetime import datetime, timedelta

# Catalog configuration
CATALOG = "juan_dev"
SCHEMA = "retail"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Master Data Import
# MAGIC 
# MAGIC Uses DLT `root_path` which is automatically added to sys.path during pipeline execution.
# MAGIC The root_path is configured as `${workspace.root_path}/files` in databricks.yml.

# COMMAND ----------

import sys
import os

# DLT automatically adds root_path to sys.path
# root_path is ${workspace.root_path}/files, so we need to add the 00-data subdirectory
# to import master_data.py

for path in sys.path:
    # Look for the files directory (root_path) in sys.path
    if path.endswith('/files') or '/files/' in path:
        data_dir = os.path.join(path, '00-data')
        if os.path.isdir(data_dir) and data_dir not in sys.path:
            sys.path.insert(0, data_dir)
            print(f"Added {data_dir} to sys.path")
            break

from master_data import (
    get_products_for_dimension,
    get_locations_for_dimension,
    get_channels_for_dimension,
    get_customers_for_dimension,
    SALE_PERIODS,
    HOLIDAYS,
    PEAK_SEASON_MONTHS,
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 1: Dimension Tables (from master_data.py)
# MAGIC 
# MAGIC These tables are created from the static master data configuration.
# MAGIC They are materialized once and updated only when master_data.py changes.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Product Dimension

# COMMAND ----------

@dp.table(
    name="gold_product_dim",
    comment="Product master dimension. Source: master_data.py. No external DB dependency.",
    table_properties={
        "quality": "gold",
        "pipelines.reset.allowed": "true"
    }
)
def gold_product_dim():
    """
    Product dimension derived from master_data.py.
    
    Creates products with SKUs, pricing, categories, etc.
    Full schema matching original dimension_generator.py for metric view compatibility.
    """
    # Full schema matching original dimension_generator.py
    schema = StructType([
        StructField("product_key", IntegerType(), False),
        StructField("product_id", StringType(), True),
        StructField("sku", StringType(), True),
        StructField("product_name", StringType(), True),
        StructField("brand", StringType(), True),
        StructField("category_level_1", StringType(), True),
        StructField("category_level_2", StringType(), True),
        StructField("category_level_3", StringType(), True),
        StructField("color_family", StringType(), True),
        StructField("color_name", StringType(), True),
        StructField("size_range", StringType(), True),
        StructField("material_primary", StringType(), True),
        StructField("material_composition", StringType(), True),
        StructField("season_code", StringType(), True),
        StructField("collection_name", StringType(), True),
        StructField("launch_date", DateType(), True),
        StructField("end_of_life_date", DateType(), True),  # Nullable
        StructField("base_price", DoubleType(), True),
        StructField("unit_cost", DoubleType(), True),
        StructField("margin_percent", DoubleType(), True),
        StructField("price_tier", StringType(), True),
        StructField("sustainability_flag", BooleanType(), True),
        StructField("is_active", BooleanType(), True),
        StructField("source_system", StringType(), True),
    ])
    
    products = get_products_for_dimension()
    
    return spark.createDataFrame(products, schema).withColumn(
        "etl_timestamp", current_timestamp()
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ### Location Dimension

# COMMAND ----------

@dp.table(
    name="gold_location_dim",
    comment="Location master dimension (stores, warehouses, DCs). Source: master_data.py.",
    table_properties={
        "quality": "gold",
        "pipelines.reset.allowed": "true"
    }
)
def gold_location_dim():
    """
    Location dimension derived from master_data.py.
    
    Creates stores, warehouses, and distribution centers.
    Full schema matching original dimension_generator.py for metric view compatibility.
    """
    # Full schema matching original dimension_generator.py
    schema = StructType([
        StructField("location_key", IntegerType(), False),
        StructField("location_id", StringType(), True),
        StructField("location_name", StringType(), True),
        StructField("location_type", StringType(), True),
        StructField("store_format", StringType(), True),  # Nullable for warehouses/DCs
        StructField("channel", StringType(), True),
        StructField("district", StringType(), True),
        StructField("city", StringType(), True),
        StructField("state_province", StringType(), True),
        StructField("postal_code", StringType(), True),
        StructField("region", StringType(), True),
        StructField("country", StringType(), True),
        StructField("latitude", DoubleType(), True),
        StructField("longitude", DoubleType(), True),
        StructField("selling_sqft", DoubleType(), True),
        StructField("total_sqft", DoubleType(), True),
        StructField("open_date", DateType(), True),
        StructField("close_date", DateType(), True),  # Nullable
        StructField("is_active", BooleanType(), True),
        StructField("timezone", StringType(), True),
        StructField("state_tax_rate", DoubleType(), True),
        StructField("source_system", StringType(), True),
    ])
    
    locations = get_locations_for_dimension()
    
    return spark.createDataFrame(locations, schema).withColumn(
        "etl_timestamp", current_timestamp()
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ### Channel Dimension

# COMMAND ----------

@dp.table(
    name="gold_channel_dim",
    comment="Sales channel dimension. Source: master_data.py.",
    table_properties={
        "quality": "gold",
        "pipelines.reset.allowed": "true"
    }
)
def gold_channel_dim():
    """
    Channel dimension derived from master_data.py.
    
    Creates sales channels (web, mobile, POS, etc.).
    """
    schema = StructType([
        StructField("channel_key", IntegerType(), False),
        StructField("channel_code", StringType(), True),
        StructField("channel_name", StringType(), True),
        StructField("channel_type", StringType(), True),
        StructField("channel_category", StringType(), True),
        StructField("device_category", StringType(), True),
        StructField("is_digital", BooleanType(), True),
        StructField("is_owned", BooleanType(), True),
        StructField("commission_rate", DoubleType(), True),
        StructField("source_system", StringType(), True),
    ])
    
    channels = get_channels_for_dimension()
    
    return spark.createDataFrame(channels, schema).withColumn(
        "etl_timestamp", current_timestamp()
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ### Customer Dimension

# COMMAND ----------

@dp.table(
    name="gold_customer_dim",
    comment="Customer master dimension with segments and SCD Type 2. Source: master_data.py.",
    table_properties={
        "quality": "gold",
        "pipelines.reset.allowed": "true"
    }
)
def gold_customer_dim():
    """
    Customer dimension derived from master_data.py.
    
    Creates customer records with segment assignments.
    Full schema matching original dimension_generator.py for metric view compatibility.
    """
    # Full schema matching original dimension_generator.py
    schema = StructType([
        StructField("customer_key", IntegerType(), False),
        StructField("customer_id", StringType(), True),
        StructField("email", StringType(), True),
        StructField("first_name", StringType(), True),
        StructField("last_name", StringType(), True),
        StructField("segment", StringType(), True),
        StructField("lifetime_value", DoubleType(), True),
        StructField("acquisition_date", DateType(), True),
        StructField("acquisition_channel", StringType(), True),
        StructField("preferred_channel", StringType(), True),
        StructField("preferred_category", StringType(), True),
        StructField("size_profile_tops", StringType(), True),
        StructField("size_profile_bottoms", StringType(), True),
        StructField("geo_region", StringType(), True),
        StructField("geo_city", StringType(), True),
        StructField("nearest_store_id", IntegerType(), True),
        StructField("loyalty_tier", StringType(), True),
        StructField("email_subscribe_flag", BooleanType(), True),
        StructField("sms_subscribe_flag", BooleanType(), True),
        StructField("effective_date", DateType(), True),
        StructField("expiration_date", DateType(), True),
        StructField("is_current", BooleanType(), True),
        StructField("source_system", StringType(), True),
    ])
    
    customers = get_customers_for_dimension()
    
    return spark.createDataFrame(customers, schema).withColumn(
        "etl_timestamp", current_timestamp()
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ### Date Dimension

# COMMAND ----------

@dp.table(
    name="gold_date_dim",
    comment="Date dimension with retail and fiscal calendar. Source: generated.",
    table_properties={
        "quality": "gold",
        "pipelines.reset.allowed": "true"
    }
)
def gold_date_dim():
    """
    Date dimension generated for 3 years of history + 1 year future.
    Full schema matching original dimension_generator.py for metric view compatibility.
    """
    # Full schema with fiscal columns
    schema = StructType([
        StructField("date_key", IntegerType(), False),
        StructField("calendar_date", DateType(), True),
        StructField("year", IntegerType(), True),
        StructField("quarter", IntegerType(), True),
        StructField("month", IntegerType(), True),
        StructField("month_name", StringType(), True),
        StructField("week_of_year", IntegerType(), True),
        StructField("day_of_month", IntegerType(), True),
        StructField("day_of_week", IntegerType(), True),
        StructField("day_name", StringType(), True),
        StructField("is_weekend", BooleanType(), True),
        StructField("is_holiday", BooleanType(), True),
        StructField("holiday_name", StringType(), True),  # Nullable
        StructField("fiscal_year", IntegerType(), True),
        StructField("fiscal_quarter", IntegerType(), True),
        StructField("fiscal_month", IntegerType(), True),
        StructField("season", StringType(), True),
        StructField("is_peak_season", BooleanType(), True),
        StructField("is_sale_period", BooleanType(), True),
        StructField("sale_event_name", StringType(), True),  # Nullable
    ])
    
    # Generate dates
    start_date = datetime.now() - timedelta(days=1095)  # 3 years back
    end_date = datetime.now() + timedelta(days=365)      # 1 year forward
    
    dates = []
    current = start_date
    while current <= end_date:
        month = current.month
        day = current.day
        
        # Season
        if month in [3, 4, 5]:
            season = 'Spring'
        elif month in [6, 7, 8]:
            season = 'Summer'
        elif month in [9, 10, 11]:
            season = 'Fall'
        else:
            season = 'Winter'
        
        # Holiday check
        is_holiday = False
        holiday_name = None
        for hol_name, hol_day in HOLIDAYS.get(month, []):
            if day == hol_day:
                is_holiday = True
                holiday_name = hol_name
                break
        
        # Fiscal year (starts February)
        fiscal_year = current.year if month >= 2 else current.year - 1
        fiscal_quarter = ((month - 2) % 12) // 3 + 1
        fiscal_month = ((month - 2) % 12) + 1
        
        dates.append({
            'date_key': int(current.strftime('%Y%m%d')),
            'calendar_date': current.date(),
            'year': current.year,
            'quarter': (month - 1) // 3 + 1,
            'month': month,
            'month_name': current.strftime('%B'),
            'week_of_year': current.isocalendar()[1],
            'day_of_month': day,
            'day_of_week': current.weekday() + 1,
            'day_name': current.strftime('%A'),
            'is_weekend': current.weekday() >= 5,
            'is_holiday': is_holiday,
            'holiday_name': holiday_name,
            'fiscal_year': fiscal_year,
            'fiscal_quarter': fiscal_quarter,
            'fiscal_month': fiscal_month,
            'season': season,
            'is_peak_season': month in PEAK_SEASON_MONTHS,
            'is_sale_period': month in SALE_PERIODS,
            'sale_event_name': SALE_PERIODS.get(month),
        })
        current += timedelta(days=1)
    
    return spark.createDataFrame(dates, schema).withColumn("etl_timestamp", current_timestamp())

# COMMAND ----------

# MAGIC %md
# MAGIC ### Time Dimension

# COMMAND ----------

@dp.table(
    name="gold_time_dim",
    comment="Time dimension with 15-minute granularity. Source: generated.",
    table_properties={
        "quality": "gold",
        "pipelines.reset.allowed": "true"
    }
)
def gold_time_dim():
    """
    Time dimension with 15-minute intervals.
    """
    schema = StructType([
        StructField("time_key", IntegerType(), False),
        StructField("hour", IntegerType(), True),
        StructField("minute", IntegerType(), True),
        StructField("hour_minute", StringType(), True),
        StructField("am_pm", StringType(), True),
        StructField("hour_12", IntegerType(), True),
        StructField("period_of_day", StringType(), True),
        StructField("is_business_hours", BooleanType(), True),
        StructField("is_peak_hours", BooleanType(), True),
    ])
    
    times = []
    for hour in range(24):
        for minute in [0, 15, 30, 45]:
            time_key = hour * 100 + minute
            
            if 6 <= hour < 12:
                period = 'Morning'
            elif 12 <= hour < 17:
                period = 'Afternoon'
            elif 17 <= hour < 21:
                period = 'Evening'
            else:
                period = 'Night'
            
            times.append({
                'time_key': time_key,
                'hour': hour,
                'minute': minute,
                'hour_minute': f"{hour:02d}:{minute:02d}",
                'am_pm': 'AM' if hour < 12 else 'PM',
                'hour_12': hour if hour <= 12 else hour - 12,
                'period_of_day': period,
                'is_business_hours': 9 <= hour < 21,
                'is_peak_hours': hour in [12, 13, 17, 18, 19, 20],
            })
    
    return spark.createDataFrame(times, schema).withColumn("etl_timestamp", current_timestamp())

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 2: Fact Tables (from Silver Streaming)
# MAGIC 
# MAGIC These tables read from silver streaming tables and write to gold.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Gold Sales Fact (POS)

# COMMAND ----------

@dp.table(
    name="gold_sales_fact",
    comment="Sales transaction fact table. Sources: POS streaming, E-commerce streaming.",
    table_properties={
        "quality": "gold",
        "pipelines.reset.allowed": "true"
    }
)
@dp.expect("valid_quantity", "quantity_sold > 0")
@dp.expect("valid_price", "unit_price >= 0")
def gold_sales_fact():
    """
    Unified sales fact combining POS transactions.
    """
    pos_silver = spark.readStream.table(f"{CATALOG}.{SCHEMA}.silver_transactions_unified")
    
    return pos_silver.select(
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

# COMMAND ----------

# MAGIC %md
# MAGIC ### Gold Sales Fact - E-commerce

# COMMAND ----------

@dp.table(
    name="gold_sales_fact_ecommerce",
    comment="E-commerce sales transactions. Can be combined with gold_sales_fact.",
    table_properties={
        "quality": "gold",
        "pipelines.reset.allowed": "true"
    }
)
@dp.expect("valid_quantity", "quantity_sold > 0")
def gold_sales_fact_ecommerce():
    """E-commerce sales matching gold_sales_fact schema."""
    ecom_silver = spark.readStream.table(f"{CATALOG}.{SCHEMA}.silver_ecommerce_unified")
    
    return ecom_silver.select(
        col("transaction_id").cast("string").alias("transaction_id"),
        col("line_item_id").cast("string").alias("line_item_id"),
        coalesce(col("customer_key"), lit(-1)).cast("int").alias("customer_key"),
        coalesce(col("product_key"), lit(-1)).cast("int").alias("product_key"),
        col("date_key").cast("int").alias("date_key"),
        col("time_key").cast("int").alias("time_key"),
        lit(-1).cast("int").alias("location_key"),
        coalesce(col("channel_key"), lit(-1)).cast("int").alias("channel_key"),
        col("transaction_id").alias("order_number"),
        lit(None).cast("string").alias("pos_terminal_id"),
        lit(None).cast("string").alias("sales_associate_id"),
        col("qty").cast("int").alias("quantity_sold"),
        col("qty").cast("int").alias("quantity_requested"),
        lit(False).alias("is_inventory_constrained"),
        lit(100).cast("int").alias("inventory_at_purchase"),
        col("price").cast("double").alias("unit_price"),
        col("discount").cast("double").alias("discount_amount"),
        (col("line_total") * 0.07).cast("double").alias("tax_amount"),
        col("line_total").cast("double").alias("net_sales_amount"),
        (col("line_total") * 0.4).cast("double").alias("gross_margin_amount"),
        lit(False).alias("is_return"),
        lit(None).cast("int").alias("return_restocked_date_key"),
        lit(False).alias("is_exchange"),
        when(col("promo_code").isNotNull(), True).otherwise(False).alias("is_promotional"),
        lit(False).alias("is_clearance"),
        col("shipping_method").alias("fulfillment_type"),
        col("payment_method").cast("string").alias("payment_method"),
        lit("ecommerce_streaming").alias("source_system"),
        current_timestamp().alias("etl_timestamp")
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ### Gold Inventory Fact

# COMMAND ----------

@dp.table(
    name="gold_inventory_fact",
    comment="Inventory snapshot fact table. Sources: silver inventory movements aggregated.",
    table_properties={
        "quality": "gold",
        "pipelines.reset.allowed": "true"
    }
)
def gold_inventory_fact():
    """
    Inventory snapshot fact table - aggregates movements into daily snapshots.
    
    Schema matches original fact_generator.py for metric view compatibility.
    """
    from pyspark.sql import functions as F
    
    silver = spark.readStream.table(f"{CATALOG}.{SCHEMA}.silver_inventory_movements")
    products = spark.table(f"{CATALOG}.{SCHEMA}.gold_product_dim")
    
    # Aggregate movements into snapshots by product/location/date
    # For streaming, we compute running totals per product-location combination
    aggregated = silver.groupBy(
        "product_key", "location_key", "date_key"
    ).agg(
        F.sum(F.when(col("movement_type") == "RECEIPT", col("quantity")).otherwise(0)).alias("receipts"),
        F.sum(F.when(col("movement_type") == "SALE", F.abs(col("quantity"))).otherwise(0)).alias("sales"),
        F.sum(F.when(col("movement_type") == "ADJUSTMENT", col("quantity")).otherwise(0)).alias("adjustments"),
        F.avg("cost_per_unit").alias("avg_unit_cost"),
        F.max("timestamp").alias("snapshot_timestamp")
    )
    
    # Join with products to get base_price for value calculations
    with_product = aggregated.join(
        products.select("product_key", "base_price", "unit_cost"),
        on="product_key",
        how="left"
    )
    
    # Create snapshot-like structure
    # Note: In streaming, we approximate snapshot values from movements
    return with_product.select(
        col("product_key").cast("int"),
        col("location_key").cast("int"),
        col("date_key").cast("int"),
        # Quantities - approximated from movements
        (col("receipts") - col("sales") + col("adjustments")).cast("int").alias("quantity_on_hand"),
        ((col("receipts") - col("sales") + col("adjustments")) * 0.9).cast("int").alias("quantity_available"),
        ((col("receipts") - col("sales") + col("adjustments")) * 0.1).cast("int").alias("quantity_reserved"),
        lit(0).cast("int").alias("quantity_in_transit"),
        lit(0).cast("int").alias("quantity_damaged"),
        # Inventory values
        ((col("receipts") - col("sales") + col("adjustments")) * coalesce(col("unit_cost"), lit(50.0))).cast("double").alias("inventory_value_cost"),
        ((col("receipts") - col("sales") + col("adjustments")) * coalesce(col("base_price"), lit(100.0))).cast("double").alias("inventory_value_retail"),
        # Inventory metrics (approximations)
        lit(30).cast("int").alias("days_of_supply"),
        lit(21).cast("int").alias("stock_cover_days"),
        lit(50).cast("int").alias("reorder_point"),
        lit(100).cast("int").alias("reorder_quantity"),
        # Status flags
        when((col("receipts") - col("sales") + col("adjustments")) <= 0, True).otherwise(False).alias("is_stockout"),
        when((col("receipts") - col("sales") + col("adjustments")) > 200, True).otherwise(False).alias("is_overstock"),
        lit(False).alias("is_discontinued"),
        lit(0).cast("int").alias("stockout_duration_days"),
        lit(None).cast("date").alias("last_replenishment_date"),
        lit(None).cast("date").alias("next_replenishment_date"),
        lit("inventory_streaming").alias("source_system"),
        current_timestamp().alias("etl_timestamp")
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ### Gold Cart Abandonment Fact

# COMMAND ----------

@dp.table(
    name="gold_cart_abandonment_fact",
    comment="Cart abandonment tracking fact. Sources: clickstream streaming.",
    table_properties={
        "quality": "gold",
        "pipelines.reset.allowed": "true"
    }
)
def gold_cart_abandonment_fact():
    """
    Cart abandonment fact table tracking abandoned carts and recovery.
    
    Schema matches original fact_generator.py for metric view compatibility.
    Detects abandoned carts (add_to_cart without subsequent complete_checkout).
    """
    from pyspark.sql import functions as F
    from pyspark.sql.window import Window
    
    silver = spark.readStream.table(f"{CATALOG}.{SCHEMA}.silver_clickstream_events")
    
    # Filter to cart-related events
    cart_events = silver.filter(
        col("event_type").isin("add_to_cart", "remove_from_cart", "begin_checkout", "complete_checkout")
    )
    
    # Aggregate to session level for abandonment detection
    session_agg = cart_events.groupBy(
        "session_id", "customer_key", "date_key", "time_key", "channel_key", "customer_id"
    ).agg(
        F.max(F.when(col("event_type") == "complete_checkout", 1).otherwise(0)).alias("completed"),
        F.max(F.when(col("event_type") == "begin_checkout", 1).otherwise(0)).alias("began_checkout"),
        F.max("cart.items").alias("items_count"),
        F.max("cart.value").alias("cart_value"),
        F.first("device_type").alias("device_type"),
        F.min("timestamp").alias("first_event_ts"),
        F.max("timestamp").alias("last_event_ts")
    )
    
    # Create abandonment records
    # abandonment_id: Use hash of session_id for deterministic, globally unique ID
    # This ensures same cart event always gets same ID (streaming idempotency)
    return session_agg.select(
        F.abs(F.hash(col("session_id"))).cast("int").alias("abandonment_id"),
        F.concat(lit("CART_"), col("session_id")).alias("cart_id"),
        coalesce(col("customer_key"), lit(-1)).cast("int").alias("customer_key"),
        col("date_key").cast("int"),
        col("time_key").cast("int"),
        coalesce(col("channel_key"), lit(-1)).cast("int").alias("channel_key"),
        col("cart_value").cast("double"),
        coalesce(col("items_count"), lit(1)).cast("int").alias("items_count"),
        # Minutes in cart (time between first add and last event)
        ((F.unix_timestamp(col("last_event_ts")) - F.unix_timestamp(col("first_event_ts"))) / 60).cast("int").alias("minutes_in_cart"),
        # Recovery fields - simulated for streaming (would come from email system)
        when(col("completed") == 0, F.rand() < 0.8).otherwise(False).alias("recovery_email_sent"),
        when(col("completed") == 0, F.rand() < 0.4).otherwise(False).alias("recovery_email_opened"),
        when(col("completed") == 0, F.rand() < 0.3).otherwise(False).alias("recovery_email_clicked"),
        (col("completed") == 1).alias("is_recovered"),
        when(col("completed") == 1, col("date_key")).otherwise(lit(None)).cast("int").alias("recovery_date_key"),
        when(col("completed") == 1, col("cart_value")).otherwise(lit(0.0)).cast("double").alias("recovery_revenue"),
        # Abandonment stage
        when(col("completed") == 1, lit("completed"))
            .when(col("began_checkout") == 1, lit("payment"))
            .otherwise(lit("cart")).alias("abandonment_stage"),
        # Suspected reason (simulated)
        when(col("completed") == 0,
            F.when(F.rand() < 0.3, lit("high_shipping"))
            .when(F.rand() < 0.5, lit("price_concern"))
            .when(F.rand() < 0.7, lit("comparison_shopping"))
            .otherwise(lit("distraction"))
        ).otherwise(lit(None)).alias("suspected_reason"),
        # Inventory-related abandonment flags
        lit(False).alias("low_inventory_trigger"),
        lit(0).cast("int").alias("inventory_constrained_items"),
        lit("clickstream_streaming").alias("source_system"),
        current_timestamp().alias("etl_timestamp")
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ### Gold Customer Event Fact

# COMMAND ----------

@dp.table(
    name="gold_customer_event_fact",
    comment="Customer engagement events fact table. Sources: clickstream streaming.",
    table_properties={
        "quality": "gold",
        "pipelines.reset.allowed": "true"
    }
)
def gold_customer_event_fact():
    """
    Customer event fact table from clickstream.
    
    Schema matches original fact_generator.py for metric view compatibility.
    """
    from pyspark.sql import functions as F
    
    silver = spark.readStream.table(f"{CATALOG}.{SCHEMA}.silver_clickstream_events")
    
    return silver.select(
        col("event_id").cast("long").alias("event_id"),
        col("session_id"),
        coalesce(col("customer_key"), lit(-1)).cast("int").alias("customer_key"),
        coalesce(col("product_key"), lit(-1)).cast("int").alias("product_key"),
        col("date_key").cast("int"),
        col("time_key").cast("int"),
        coalesce(col("channel_key"), lit(-1)).cast("int").alias("channel_key"),
        lit(None).cast("int").alias("location_key"),
        col("event_type"),
        # Event category
        when(col("event_type").contains("view"), lit("engagement"))
            .when(col("event_type").contains("checkout"), lit("conversion"))
            .otherwise(lit("interaction")).alias("event_category"),
        col("event_type").alias("event_action"),
        # Event label derived from event_type (page_category not in silver)
        when(col("event_type") == "product_view", lit("product"))
            .when(col("event_type") == "search", lit("search"))
            .when(col("event_type").contains("cart"), lit("cart"))
            .when(col("event_type").contains("checkout"), lit("checkout"))
            .otherwise(lit("general")).alias("event_label"),
        coalesce(col("cart.value"), lit(0.0)).cast("double").alias("event_value"),
        lit(30).cast("int").alias("time_on_page_seconds"),
        when(col("event_type") == "page_view", F.rand() < 0.3).otherwise(False).alias("bounce_flag"),
        (col("event_type") == "complete_checkout").alias("conversion_flag"),
        col("page_url"),
        col("referrer").alias("referrer_url"),
        # Extract search term from page_url when event is search
        when(col("event_type") == "search", 
            F.regexp_extract(col("page_url"), r"[?&]q=([^&]+)", 1)
        ).otherwise(lit(None)).alias("search_term"),
        lit("clickstream_streaming").alias("source_system"),
        current_timestamp().alias("etl_timestamp")
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ### Gold Inventory Movement Fact

# COMMAND ----------

@dp.table(
    name="gold_inventory_movement_fact",
    comment="Inventory movement transactions. Sources: silver inventory movements.",
    table_properties={
        "quality": "gold",
        "pipelines.reset.allowed": "true"
    }
)
def gold_inventory_movement_fact():
    """
    Inventory movement fact table (separate from snapshot-based inventory_fact).
    
    Schema matches original aggregates.py for metric view compatibility.
    """
    from pyspark.sql import functions as F
    
    silver = spark.readStream.table(f"{CATALOG}.{SCHEMA}.silver_inventory_movements")
    
    return silver.select(
        col("movement_id"),
        coalesce(col("product_key"), lit(-1)).cast("int").alias("product_key"),
        # For movements, from_location is source, to_location is destination
        when(col("movement_type") == "SALE", col("location_key"))
            .when(col("movement_type") == "TRANSFER", col("location_key"))
            .otherwise(lit(None)).cast("int").alias("from_location_key"),
        when(col("movement_type") == "RECEIPT", col("location_key"))
            .when(col("movement_type") == "RETURN", col("location_key"))
            .otherwise(lit(None)).cast("int").alias("to_location_key"),
        col("date_key").cast("int"),
        lit(1200).cast("int").alias("time_key"),  # Default to noon
        col("movement_type"),
        col("reason_code").alias("movement_reason"),
        F.abs(col("quantity")).cast("int").alias("quantity"),
        coalesce(col("cost_per_unit"), lit(50.0)).cast("double").alias("unit_cost"),
        (F.abs(col("quantity")) * coalesce(col("cost_per_unit"), lit(50.0))).cast("double").alias("total_cost"),
        lit("order").alias("reference_type"),
        col("reference_id"),
        lit("inventory_streaming").alias("source_system"),
        current_timestamp().alias("etl_timestamp")
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ### Gold Stockout Events

# COMMAND ----------

@dp.table(
    name="gold_stockout_events",
    comment="Stockout events derived from inventory snapshots. Sources: gold_inventory_fact.",
    table_properties={
        "quality": "gold",
        "pipelines.reset.allowed": "true"
    }
)
def gold_stockout_events():
    """
    Stockout events table derived from inventory fact.
    
    Identifies stockout periods and calculates lost sales metrics.
    """
    from pyspark.sql import functions as F
    from pyspark.sql.window import Window
    
    # Read from inventory fact (batch read since this is an aggregation)
    inventory = spark.table(f"{CATALOG}.{SCHEMA}.gold_inventory_fact")
    products = spark.table(f"{CATALOG}.{SCHEMA}.gold_product_dim")
    dates = spark.table(f"{CATALOG}.{SCHEMA}.gold_date_dim")
    
    # Identify stockout records
    stockouts = inventory.filter(col("is_stockout") == True)
    
    # Join with products for pricing
    with_products = stockouts.join(
        products.select("product_key", "base_price"),
        on="product_key",
        how="left"
    )
    
    # Join with dates for peak season info
    with_dates = with_products.join(
        dates.select("date_key", "is_peak_season"),
        on="date_key",
        how="left"
    )
    
    # Create stockout events with lost sales estimates
    stockout_events = with_dates.select(
        F.monotonically_increasing_id().alias("stockout_id"),
        col("product_key").cast("int"),
        col("location_key").cast("int"),
        col("date_key").cast("int").alias("stockout_start_date_key"),
        col("date_key").cast("int").alias("stockout_end_date_key"),  # Same day for streaming
        lit(1).cast("int").alias("stockout_duration_days"),
        # Estimated lost sales (2-5 attempts per day during stockout)
        (F.floor(F.rand() * 4) + 2).cast("int").alias("lost_sales_attempts"),
        (F.floor(F.rand() * 6) + 2).cast("int").alias("lost_sales_quantity"),
        # Lost revenue based on product price and estimated quantity
        (coalesce(col("base_price"), lit(100.0)) * (F.floor(F.rand() * 6) + 2)).cast("double").alias("lost_sales_revenue"),
        coalesce(col("is_peak_season"), lit(False)).alias("peak_season_flag"),
        lit("inventory_derived").alias("source_system"),
        current_timestamp().alias("etl_timestamp")
    )
    
    return stockout_events

# COMMAND ----------

# MAGIC %md
# MAGIC ### Gold Customer Product Affinity Aggregate

# COMMAND ----------

@dp.table(
    name="gold_customer_product_affinity_agg",
    comment="Customer-product affinity scores for personalization. Sources: sales + events.",
    table_properties={
        "quality": "gold",
        "pipelines.reset.allowed": "true"
    }
)
def gold_customer_product_affinity_agg():
    """
    Customer-product affinity aggregate for personalization.
    
    Calculates affinity scores from purchase and browsing behavior.
    """
    from pyspark.sql import functions as F
    from pyspark.sql.window import Window
    
    # Read source tables (batch since this is an aggregation)
    sales = spark.table(f"{CATALOG}.{SCHEMA}.gold_sales_fact")
    
    # Check if event fact exists, if not create minimal affinity from sales only
    try:
        events = spark.table(f"{CATALOG}.{SCHEMA}.gold_customer_event_fact")
        has_events = events.count() > 0
    except:
        has_events = False
    
    # Purchase-based affinity from sales
    purchase_affinity = sales.filter(col("is_return") == False).groupBy(
        "customer_key", "product_key"
    ).agg(
        F.count("transaction_id").alias("purchase_count"),
        F.sum("net_sales_amount").alias("total_spent"),
        F.max("date_key").alias("last_purchase_date")
    )
    
    if has_events:
        # Event-based metrics
        event_metrics = events.filter(col("product_key") > 0).groupBy(
            "customer_key", "product_key"
        ).agg(
            F.sum(F.when(col("event_type") == "product_view", 1).otherwise(0)).alias("view_count"),
            F.sum(F.when(col("event_type") == "add_to_cart", 1).otherwise(0)).alias("cart_add_count"),
            F.max("date_key").alias("last_event_date")
        )
        
        # Combine sales and events
        combined = purchase_affinity.join(
            event_metrics,
            on=["customer_key", "product_key"],
            how="full_outer"
        ).select(
            coalesce(purchase_affinity.customer_key, event_metrics.customer_key).alias("customer_key"),
            coalesce(purchase_affinity.product_key, event_metrics.product_key).alias("product_key"),
            coalesce(col("purchase_count"), lit(0)).alias("purchase_count"),
            coalesce(col("total_spent"), lit(0.0)).alias("total_spent"),
            coalesce(col("view_count"), lit(0)).alias("view_count"),
            coalesce(col("cart_add_count"), lit(0)).alias("cart_add_count"),
            F.greatest(
                coalesce(col("last_purchase_date"), lit(0)),
                coalesce(col("last_event_date"), lit(0))
            ).alias("last_interaction_date")
        )
    else:
        # Sales-only affinity
        combined = purchase_affinity.select(
            col("customer_key"),
            col("product_key"),
            col("purchase_count"),
            col("total_spent"),
            lit(0).alias("view_count"),
            lit(0).alias("cart_add_count"),
            col("last_purchase_date").alias("last_interaction_date")
        )
    
    # Calculate affinity scores
    window_spec = Window.partitionBy("customer_key").orderBy(F.desc("affinity_score"))
    
    affinity = combined.select(
        col("customer_key").cast("int"),
        col("product_key").cast("int"),
        # Affinity score: weighted combination of purchase + cart + view
        F.least(
            lit(1.0),
            (col("purchase_count") * 0.5 + col("cart_add_count") * 0.3 + col("view_count") * 0.2) / 10
        ).cast("double").alias("affinity_score"),
        col("purchase_count").cast("int"),
        col("view_count").cast("int"),
        col("cart_add_count").cast("int"),
        # Days since last interaction
        (F.lit(int(datetime.now().strftime('%Y%m%d'))) - col("last_interaction_date")).cast("int").alias("days_since_last_interaction"),
        # Conversion ratios
        when(col("view_count") > 0, col("purchase_count").cast("double") / col("view_count"))
            .otherwise(lit(0.0)).alias("view_to_purchase_ratio"),
        when(col("cart_add_count") > 0, col("purchase_count").cast("double") / col("cart_add_count"))
            .otherwise(lit(0.0)).alias("cart_to_purchase_ratio"),
        # Predicted CLTV impact
        (col("total_spent") * (lit(1.0) + F.least(lit(1.0), col("purchase_count") * 0.1))).cast("double").alias("predicted_cltv_impact"),
        F.current_date().alias("calculation_date"),
        lit("ML_PERSONALIZATION").alias("source_system"),
        current_timestamp().alias("etl_timestamp")
    ).filter(
        (col("purchase_count") > 0) | (col("view_count") > 5) | (col("cart_add_count") > 0)
    )
    
    # Add recommendation rank
    return affinity.withColumn(
        "recommendation_rank",
        F.row_number().over(window_spec)
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## SQL Views (Run After Deployment)
# MAGIC 
# MAGIC ```sql
# MAGIC -- Unified sales view combining POS and E-commerce
# MAGIC CREATE OR REPLACE VIEW juan_dev.retail.gold_sales_fact_all AS
# MAGIC SELECT * FROM juan_dev.retail.gold_sales_fact
# MAGIC UNION ALL
# MAGIC SELECT * FROM juan_dev.retail.gold_sales_fact_ecommerce;
# MAGIC ```
