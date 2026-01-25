# Databricks notebook source
# MAGIC %md
# MAGIC # Historical Data Backfill Generator
# MAGIC 
# MAGIC This notebook generates historical synthetic data for the medallion pipeline.
# MAGIC Use this to populate the pipeline with data spanning multiple days/months,
# MAGIC enabling realistic analytics like RFM analysis, trend detection, and seasonality patterns.
# MAGIC 
# MAGIC ## When to Use
# MAGIC - **Initial Setup**: Generate baseline data before starting real-time streaming
# MAGIC - **Demo Reset**: Recreate historical data for demos
# MAGIC - **Testing**: Generate test data with specific date ranges
# MAGIC 
# MAGIC ## What Gets Generated
# MAGIC - POS transactions across all stores
# MAGIC - E-commerce orders across web/mobile channels
# MAGIC - Inventory movements (receipts, transfers, adjustments)
# MAGIC - Clickstream events (page views, cart actions, checkouts)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

import sys
import os

# Add 00-data directory to path for generators and master_data
# Use dbutils to get the notebook's directory path
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
data_dir = "/Workspace" + "/".join(notebook_path.split("/")[:-1])

# Add to Python path for importing master_data and generators
if data_dir not in sys.path:
    sys.path.insert(0, data_dir)

print(f"Data directory: {data_dir}")

from datetime import datetime, timedelta

# COMMAND ----------

# Configuration - Adjust these values as needed
HISTORICAL_DAYS = 90  # Number of days of historical data to generate
RANDOM_SEED = 42      # For reproducibility

# Volume paths - adjust to your catalog/schema
CATALOG = "juan_dev"
SCHEMA = "retail"
VOLUME_BASE = f"/Volumes/{CATALOG}/{SCHEMA}/data"

# Events per day (controls data density)
EVENTS_PER_DAY = {
    "pos": 500,           # POS transactions per day
    "ecommerce": 200,     # E-commerce orders per day
    "inventory": 100,     # Inventory movements per day
    "clickstream": 5000,  # Clickstream events per day (high volume)
}

print(f"Configuration:")
print(f"  Historical days: {HISTORICAL_DAYS}")
print(f"  Date range: {datetime.now() - timedelta(days=HISTORICAL_DAYS)} to {datetime.now()}")
print(f"  Volume base: {VOLUME_BASE}")
print(f"  Events per day: {EVENTS_PER_DAY}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Initialize Generators

# COMMAND ----------

from generators.pos_generator import POSEventGenerator
from generators.ecommerce_generator import EcommerceEventGenerator
from generators.inventory_generator import InventoryEventGenerator
from generators.clickstream_generator import ClickstreamEventGenerator

# Create generators in backfill mode
pos_gen = POSEventGenerator(
    volume_path=f"{VOLUME_BASE}/pos",
    batch_size=EVENTS_PER_DAY["pos"],
    random_seed=RANDOM_SEED,
    historical_days=HISTORICAL_DAYS
)

ecommerce_gen = EcommerceEventGenerator(
    volume_path=f"{VOLUME_BASE}/ecommerce",
    batch_size=EVENTS_PER_DAY["ecommerce"],
    random_seed=RANDOM_SEED + 1,  # Different seed for variety
    historical_days=HISTORICAL_DAYS
)

inventory_gen = InventoryEventGenerator(
    volume_path=f"{VOLUME_BASE}/inventory",
    batch_size=EVENTS_PER_DAY["inventory"],
    random_seed=RANDOM_SEED + 2,
    historical_days=HISTORICAL_DAYS
)

clickstream_gen = ClickstreamEventGenerator(
    volume_path=f"{VOLUME_BASE}/clickstream",
    batch_size=EVENTS_PER_DAY["clickstream"],
    random_seed=RANDOM_SEED + 3,
    historical_days=HISTORICAL_DAYS
)

print("Generators initialized in backfill mode:")
print(f"  POS: {len(pos_gen.date_range)} days, {EVENTS_PER_DAY['pos']} events/day")
print(f"  E-commerce: {len(ecommerce_gen.date_range)} days, {EVENTS_PER_DAY['ecommerce']} events/day")
print(f"  Inventory: {len(inventory_gen.date_range)} days, {EVENTS_PER_DAY['inventory']} events/day")
print(f"  Clickstream: {len(clickstream_gen.date_range)} days, {EVENTS_PER_DAY['clickstream']} events/day")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Progress Callback Helper

# COMMAND ----------

def create_progress_callback(source_name: str):
    """Create a progress callback for a specific source."""
    def callback(date, progress_pct):
        if progress_pct == 1.0 or int(progress_pct * 100) % 10 == 0:
            bar_length = 40
            filled = int(bar_length * progress_pct)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"\r[{source_name}] [{bar}] {progress_pct*100:5.1f}% - {date.strftime('%Y-%m-%d')}", end='', flush=True)
            if progress_pct >= 1.0:
                print()  # New line when complete
    return callback

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Historical Data
# MAGIC 
# MAGIC Run each cell below to generate historical data for each source.
# MAGIC Each source creates one JSON file per day in the corresponding volume.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. POS Transactions

# COMMAND ----------

print(f"Generating {HISTORICAL_DAYS} days of POS transactions...")
print(f"  Estimated records: ~{HISTORICAL_DAYS * EVENTS_PER_DAY['pos']:,}")
print()

pos_files = pos_gen.write_historical_batch(
    dbutils=dbutils,
    events_per_day=EVENTS_PER_DAY["pos"],
    file_per_day=True,
    progress_callback=create_progress_callback("POS")
)

print(f"\n✅ POS backfill complete!")
print(f"   Files created: {len(pos_files)}")
print(f"   Location: {VOLUME_BASE}/pos/")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2. E-commerce Orders

# COMMAND ----------

print(f"Generating {HISTORICAL_DAYS} days of e-commerce orders...")
print(f"  Estimated records: ~{HISTORICAL_DAYS * EVENTS_PER_DAY['ecommerce']:,}")
print()

ecommerce_files = ecommerce_gen.write_historical_batch(
    dbutils=dbutils,
    events_per_day=EVENTS_PER_DAY["ecommerce"],
    file_per_day=True,
    progress_callback=create_progress_callback("E-commerce")
)

print(f"\n✅ E-commerce backfill complete!")
print(f"   Files created: {len(ecommerce_files)}")
print(f"   Location: {VOLUME_BASE}/ecommerce/")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3. Inventory Movements

# COMMAND ----------

print(f"Generating {HISTORICAL_DAYS} days of inventory movements...")
print(f"  Estimated records: ~{HISTORICAL_DAYS * EVENTS_PER_DAY['inventory']:,}")
print()

inventory_files = inventory_gen.write_historical_batch(
    dbutils=dbutils,
    events_per_day=EVENTS_PER_DAY["inventory"],
    file_per_day=True,
    progress_callback=create_progress_callback("Inventory")
)

print(f"\n✅ Inventory backfill complete!")
print(f"   Files created: {len(inventory_files)}")
print(f"   Location: {VOLUME_BASE}/inventory/")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4. Clickstream Events

# COMMAND ----------

print(f"Generating {HISTORICAL_DAYS} days of clickstream events...")
print(f"  Estimated records: ~{HISTORICAL_DAYS * EVENTS_PER_DAY['clickstream']:,}")
print()

clickstream_files = clickstream_gen.write_historical_batch(
    dbutils=dbutils,
    events_per_day=EVENTS_PER_DAY["clickstream"],
    file_per_day=True,
    progress_callback=create_progress_callback("Clickstream")
)

print(f"\n✅ Clickstream backfill complete!")
print(f"   Files created: {len(clickstream_files)}")
print(f"   Location: {VOLUME_BASE}/clickstream/")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

total_pos = HISTORICAL_DAYS * EVENTS_PER_DAY["pos"]
total_ecom = HISTORICAL_DAYS * EVENTS_PER_DAY["ecommerce"]
total_inv = HISTORICAL_DAYS * EVENTS_PER_DAY["inventory"]
total_click = HISTORICAL_DAYS * EVENTS_PER_DAY["clickstream"]
total_all = total_pos + total_ecom + total_inv + total_click

print("=" * 60)
print("HISTORICAL BACKFILL COMPLETE")
print("=" * 60)
print()
print(f"Date Range: {pos_gen.start_date.strftime('%Y-%m-%d')} to {pos_gen.end_date.strftime('%Y-%m-%d')}")
print(f"Total Days: {HISTORICAL_DAYS}")
print()
print("Records Generated (approximate):")
print(f"  POS Transactions:    {total_pos:>10,}")
print(f"  E-commerce Orders:   {total_ecom:>10,}")
print(f"  Inventory Movements: {total_inv:>10,}")
print(f"  Clickstream Events:  {total_click:>10,}")
print(f"  {'─' * 30}")
print(f"  TOTAL:               {total_all:>10,}")
print()
print("Files Created:")
print(f"  POS:         {len(pos_files)} files")
print(f"  E-commerce:  {len(ecommerce_files)} files")
print(f"  Inventory:   {len(inventory_files)} files")
print(f"  Clickstream: {len(clickstream_files)} files")
print()
print("Next Steps:")
print("  1. Run the SDP pipeline to process backfill data into bronze/silver/gold")
print("  2. Verify data in gold tables spans the expected date range")
print("  3. Start real-time generators for ongoing data (use without historical_days)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Backfill Files

# COMMAND ----------

# List generated files for verification
print("POS files (first 5):")
display(dbutils.fs.ls(f"{VOLUME_BASE}/pos")[:5])

print("\nE-commerce files (first 5):")
display(dbutils.fs.ls(f"{VOLUME_BASE}/ecommerce")[:5])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Optional: Quick Data Validation
# MAGIC 
# MAGIC Read a sample file to verify data quality

# COMMAND ----------

# Read sample POS file
import json

sample_file = pos_files[0] if pos_files else None
if sample_file:
    content = dbutils.fs.head(sample_file, 2000)
    lines = content.strip().split('\n')[:3]
    print(f"Sample data from {sample_file}:")
    print()
    for line in lines:
        event = json.loads(line)
        print(f"  Transaction: {event['transaction_id']}")
        print(f"  Timestamp:   {event['timestamp']}")
        print(f"  Store:       {event['store_id']}")
        print(f"  Customer:    {event.get('customer_id', 'Guest')}")
        print(f"  Items:       {len(event['items'])}")
        print()
