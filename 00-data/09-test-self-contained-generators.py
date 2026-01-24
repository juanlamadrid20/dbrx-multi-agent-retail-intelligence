# Databricks notebook source
# MAGIC %md
# MAGIC # Test Self-Contained Generators
# MAGIC 
# MAGIC This notebook tests the new self-contained generator architecture.
# MAGIC 
# MAGIC **Key Changes:**
# MAGIC - Generators use `config/master_data.py` as the single source of truth
# MAGIC - No database connectivity required
# MAGIC - Gold dimension tables derived from master_data (not prerequisites)
# MAGIC - True raw → bronze → silver → gold flow
# MAGIC 
# MAGIC **Testing Steps:**
# MAGIC 1. Test master_data imports (no Spark needed)
# MAGIC 2. Test generator initialization (no DB needed)
# MAGIC 3. Generate sample events
# MAGIC 4. Write to volumes
# MAGIC 5. Verify dimension data for gold pipeline

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup

# COMMAND ----------

CATALOG = "juan_dev"
SCHEMA = "retail"

# Add the pipeline directory to path
import sys
sys.path.insert(0, "/Workspace/Users/juan.lamadrid@databricks.com/ml/agent-bricks/multi-agent-retail-intelligence/files/40-medallion-pipeline")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 1: Master Data Imports (No Spark Required)
# MAGIC 
# MAGIC This test verifies that master_data.py can be imported without any database connection.

# COMMAND ----------

from config.master_data import (
    # Products
    SKUS, PRODUCT_CATALOG, ACTIVE_SKUS,
    CATEGORIES, BRANDS,
    
    # Locations
    STORE_IDS, WAREHOUSE_IDS, ALL_LOCATION_IDS,
    
    # Channels
    CHANNEL_CODES, ECOMMERCE_CHANNELS, POS_CHANNEL,
    
    # Customers
    CUSTOMER_IDS, CUSTOMER_SEGMENT_MAP, CUSTOMER_SEGMENTS,
    
    # Helpers
    get_product_by_sku, get_customer_segment, get_segment_basket_size,
    is_sale_period, get_seasonality_multiplier
)

print("✅ Master data imported successfully (no Spark required)")
print()
print(f"Products: {len(PRODUCT_CATALOG)} items")
print(f"  - SKUs: {len(SKUS)}")
print(f"  - Active: {len(ACTIVE_SKUS)}")
print(f"  - Sample: {SKUS[:3]}")
print()
print(f"Locations: {len(ALL_LOCATION_IDS)} total")
print(f"  - Stores: {len(STORE_IDS)}")
print(f"  - Warehouses: {len(WAREHOUSE_IDS)}")
print(f"  - Sample: {STORE_IDS[:3]}")
print()
print(f"Channels: {len(CHANNEL_CODES)}")
print(f"  - E-commerce: {ECOMMERCE_CHANNELS}")
print(f"  - POS: {POS_CHANNEL}")
print()
print(f"Customers: {len(CUSTOMER_IDS)}")
print(f"  - Segments: {list(CUSTOMER_SEGMENTS.keys())}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 2: Product Lookup

# COMMAND ----------

# Test product lookup
sku = "SKU_000001"
product = get_product_by_sku(sku)

if product:
    print(f"✅ Product found: {sku}")
    print(f"  Name: {product.product_name}")
    print(f"  Brand: {product.brand}")
    print(f"  Category: {product.category_l1} > {product.category_l2} > {product.category_l3}")
    print(f"  Price: ${product.base_price:.2f}")
    print(f"  Cost: ${product.unit_cost:.2f}")
else:
    print(f"❌ Product not found: {sku}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 3: Customer Segment Logic

# COMMAND ----------

# Test customer segment logic
test_customers = CUSTOMER_IDS[:5]
print("Customer Segment Assignments:")
for cid in test_customers:
    segment = get_customer_segment(cid)
    basket_size = get_segment_basket_size(segment)
    print(f"  {cid}: segment={segment}, basket_size={basket_size}")

print()

# Segment distribution
from collections import Counter
segments = [CUSTOMER_SEGMENT_MAP[cid] for cid in CUSTOMER_IDS]
dist = Counter(segments)
print("Segment Distribution:")
for seg, count in sorted(dist.items(), key=lambda x: -x[1]):
    pct = count / len(CUSTOMER_IDS) * 100
    print(f"  {seg}: {count:,} ({pct:.1f}%)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 4: Generator Initialization (No DB Required)
# MAGIC 
# MAGIC Generators now initialize without database connectivity.

# COMMAND ----------

from generators import (
    create_pos_generator,
    create_ecommerce_generator,
    create_inventory_generator,
    create_clickstream_generator
)

# Create generators - NO SPARK OR DB NEEDED
pos_gen = create_pos_generator(catalog=CATALOG, schema=SCHEMA, batch_size=50)
ecom_gen = create_ecommerce_generator(catalog=CATALOG, schema=SCHEMA, batch_size=50)
inv_gen = create_inventory_generator(catalog=CATALOG, schema=SCHEMA, batch_size=50)
click_gen = create_clickstream_generator(catalog=CATALOG, schema=SCHEMA, batch_size=50)

print("✅ All generators created without database dependency")
print()
print(f"POS Generator:")
print(f"  - Stores: {len(pos_gen.stores)}")
print(f"  - SKUs: {len(pos_gen.skus)}")
print(f"  - Customers: {len(pos_gen.customer_ids)}")
print()
print(f"E-commerce Generator:")
print(f"  - Channels: {len(ecom_gen.channels)}")
print(f"  - SKUs: {len(ecom_gen.skus)}")
print()
print(f"Inventory Generator:")
print(f"  - Locations: {len(inv_gen.location_ids)}")
print(f"  - SKUs: {len(inv_gen.skus)}")
print()
print(f"Clickstream Generator:")
print(f"  - Channels: {len(click_gen.channels)}")
print(f"  - SKUs: {len(click_gen.skus)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 5: Generate Sample Events

# COMMAND ----------

# Generate sample POS transaction
pos_event = pos_gen.generate_event()
print("Sample POS Transaction:")
print(f"  ID: {pos_event['transaction_id']}")
print(f"  Store: {pos_event['store_id']}")
print(f"  Customer: {pos_event['customer_id']} ({pos_event['customer_segment']})")
print(f"  Items: {len(pos_event['items'])}")
for item in pos_event['items'][:2]:
    print(f"    - {item['sku']}: ${item['price']:.2f} x {item['qty']}, discount=${item['discount']:.2f}")

# COMMAND ----------

# Generate sample e-commerce order
ecom_event = ecom_gen.generate_event()
print("Sample E-commerce Order:")
print(f"  ID: {ecom_event['order_id']}")
print(f"  Channel: {ecom_event['channel']}")
print(f"  Customer: {ecom_event['customer_id']} ({ecom_event['customer_segment']})")
print(f"  Shipping: {ecom_event['shipping_method']}")
print(f"  Promo: {ecom_event['promo_code']}")
print(f"  Items: {len(ecom_event['items'])}")

# COMMAND ----------

# Generate sample inventory movement
inv_event = inv_gen.generate_event()
print("Sample Inventory Movement:")
print(f"  ID: {inv_event['movement_id']}")
print(f"  Type: {inv_event['movement_type']}")
print(f"  Location: {inv_event['location_id']}")
print(f"  SKU: {inv_event['sku']}")
print(f"  Quantity: {inv_event['quantity']}")
print(f"  Reason: {inv_event['reason_code']}")

# COMMAND ----------

# Generate sample clickstream event
click_event = click_gen.generate_event()
print("Sample Clickstream Event:")
print(f"  ID: {click_event['event_id']}")
print(f"  Type: {click_event['event_type']}")
print(f"  Channel: {click_event['channel']}")
print(f"  Customer: {click_event['customer_id']}")
print(f"  Page: {click_event['page_url']}")
print(f"  Device: {click_event['device_type']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 6: Write Events to Volumes

# COMMAND ----------

VOLUME_BASE = f"/Volumes/{CATALOG}/{SCHEMA}/data"

# Write POS events
pos_file = pos_gen.write_batch_dbutils(dbutils, num_events=100)
print(f"✅ Wrote 100 POS events to: {pos_file}")

# Write e-commerce events
ecom_file = ecom_gen.write_batch_dbutils(dbutils, num_events=100)
print(f"✅ Wrote 100 e-commerce events to: {ecom_file}")

# Write inventory events
inv_file = inv_gen.write_batch_dbutils(dbutils, num_events=100)
print(f"✅ Wrote 100 inventory events to: {inv_file}")

# Write clickstream events
click_file = click_gen.write_batch_dbutils(dbutils, num_events=200)
print(f"✅ Wrote 200 clickstream events to: {click_file}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 7: Verify Volume Contents

# COMMAND ----------

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
    except Exception as e:
        print(f"\n{source}/")
        print(f"  ⚠️ Not found - run 01-setup-volumes.py first")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 8: Dimension Data for Gold Pipeline

# COMMAND ----------

from config.master_data import (
    get_products_for_dimension,
    get_locations_for_dimension,
    get_channels_for_dimension
)

# Get dimension data
products = get_products_for_dimension()
locations = get_locations_for_dimension()
channels = get_channels_for_dimension()

print("Dimension Data (for gold_pipeline.py):")
print()
print(f"Products: {len(products)} records")
print(f"  Sample: {products[0]['sku']} - {products[0]['product_name']}")
print()
print(f"Locations: {len(locations)} records")
print(f"  Sample: {locations[0]['location_id']} - {locations[0]['location_name']}")
print()
print(f"Channels: {len(channels)} records")
for ch in channels:
    print(f"  - {ch['channel_code']}: {ch['channel_name']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print("""
╔══════════════════════════════════════════════════════════════════╗
║              SELF-CONTAINED GENERATOR TEST COMPLETE               ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  ✅ Master data imports work without Spark                       ║
║  ✅ Generators initialize without database dependency            ║
║  ✅ Sample events generated successfully                         ║
║  ✅ Events written to volumes                                    ║
║  ✅ Dimension data available for gold pipeline                   ║
║                                                                  ║
║  Architecture Benefits:                                          ║
║  ├── No circular dependency (gold tables not required first)     ║
║  ├── Generators work standalone (can test locally)               ║
║  ├── Single source of truth (master_data.py)                     ║
║  └── True raw → bronze → silver → gold flow                      ║
║                                                                  ║
║  Next Steps:                                                     ║
║  1. Run the DLT pipeline to create all tables                    ║
║  2. Dimension tables created from master_data.py                 ║
║  3. Fact tables created from streaming silver data               ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
