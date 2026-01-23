# Medallion Streaming Pipeline

A streaming medallion architecture pipeline using Databricks Spark Declarative Pipelines (SDP) to process retail events in real-time.

**Self-Contained Design:** This pipeline uses `config/master_data.py` as the single source of truth for all reference data. No circular dependencies - generators work without gold tables existing first.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    config/master_data.py                            │
│                 (Single Source of Truth)                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│  │ PRODUCTS │ │LOCATIONS │ │ CHANNELS │ │CUSTOMERS │              │
│  │ 500 SKUs │ │ 13 locs  │ │ 8 codes  │ │ 10k IDs  │              │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘              │
└─────────────────────────────────────────────────────────────────────┘
           │                                    │
           ▼                                    ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────────┐
│   GENERATORS    │     │   UC VOLUMES    │     │    GOLD PIPELINE    │
│  (No DB needed) │     │                 │     │   (Dim Tables)      │
│                 │     │                 │     │                     │
│  POS Events     │────▶│  /pos/          │     │  gold_product_dim   │
│  Ecommerce      │────▶│  /ecommerce/    │     │  gold_location_dim  │
│  Inventory      │────▶│  /inventory/    │     │  gold_channel_dim   │
│  Clickstream    │────▶│  /clickstream/  │     │  gold_date_dim      │
└─────────────────┘     └─────────────────┘     └─────────────────────┘
                               │                          │
                               ▼                          │
                      ┌─────────────────┐                │
                      │     BRONZE      │                │
                      │  Auto Loader    │                │
                      └─────────────────┘                │
                               │                         │
                               ▼                         │
                      ┌─────────────────┐                │
                      │     SILVER      │ ◀──────────────┘
                      │ Dimension Joins │    (Joins with dims)
                      └─────────────────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │      GOLD       │
                      │  Fact Tables    │
                      │ gold_sales_fact │
                      └─────────────────┘
```

**Key Benefits:**
- No circular dependencies - start from empty schema
- Generators work standalone (can test locally without Databricks)
- Single source of truth for reference data
- True raw → bronze → silver → gold flow

## Directory Structure

```
40-medallion-pipeline/
├── README.md                    # This file
├── config/
│   ├── __init__.py
│   ├── master_data.py           # SINGLE SOURCE OF TRUTH (no DB)
│   └── pipeline_config.yaml     # Pipeline configuration
├── generators/
│   ├── __init__.py
│   ├── base_generator.py        # Abstract base class
│   ├── pos_generator.py         # POS events (uses master_data)
│   ├── ecommerce_generator.py   # Online orders (uses master_data)
│   ├── inventory_generator.py   # Inventory movements
│   └── clickstream_generator.py # Web/app clickstream
├── pipelines/
│   ├── bronze_pipeline.py       # Raw data ingestion
│   ├── silver_pipeline.py       # Data cleansing & enrichment
│   └── gold_pipeline.py         # Dimensions + Fact tables
└── notebooks/
    ├── 01-setup-volumes.py
    ├── 02-test-pos-generator.py
    ├── 03-test-bronze-pipeline.py
    ├── 04-test-silver-pipeline.py
    ├── 05-test-gold-pipeline.py
    ├── 06-test-dimension-alignment.py
    ├── 07-test-all-generators.py
    ├── 08-validate-business-logic.py
    └── 09-test-self-contained-generators.py  # Tests new architecture
```

## Quick Start

### 1. Setup Volumes

Run the setup notebook to create Unity Catalog volumes:

```python
# In Databricks notebook
%run ./notebooks/01-setup-volumes
```

### 2. Generate Test Data (No Gold Tables Needed!)

```python
from generators import (
    create_pos_generator,
    create_ecommerce_generator
)

# Generators now work WITHOUT database dependency
pos_gen = create_pos_generator(catalog="juan_dev", schema="retail")
pos_gen.write_batch_dbutils(dbutils, num_events=100)

ecom_gen = create_ecommerce_generator(catalog="juan_dev", schema="retail")
ecom_gen.write_batch_dbutils(dbutils, num_events=100)
```

### 3. Deploy Pipeline

Using Databricks Asset Bundles:

```bash
databricks bundle deploy --profile field-eng-west
databricks bundle run medallion_streaming_pipeline --profile field-eng-west
```

The pipeline will create:
1. **Dimension tables** from `master_data.py` (no external dependency)
2. **Fact tables** from streaming bronze/silver data

## Tables

### Bronze (Raw)

| Table | Source | Description |
|-------|--------|-------------|
| `bronze_pos_transactions` | `/Volumes/.../pos/` | Raw POS events |
| `bronze_ecommerce_orders` | `/Volumes/.../ecommerce/` | Raw online orders |
| `bronze_inventory_movements` | `/Volumes/.../inventory/` | Raw inventory events |
| `bronze_clickstream_events` | `/Volumes/.../clickstream/` | Raw web/app events |

### Silver (Cleansed)

| Table | Source | Description |
|-------|--------|-------------|
| `silver_transactions_unified` | bronze_pos | POS line items with dimension keys |
| `silver_ecommerce_unified` | bronze_ecommerce | E-commerce line items with dimension keys |
| `silver_inventory_movements` | bronze_inventory | Validated inventory with dimension keys |
| `silver_clickstream_events` | bronze_clickstream | Enriched events with customer/product keys |

### Gold (Business-Ready)

**Dimension Tables (from master_data.py):**

| Table | Source | Description |
|-------|--------|-------------|
| `gold_product_dim` | master_data.py | 500 products with pricing |
| `gold_location_dim` | master_data.py | 13 stores/warehouses |
| `gold_channel_dim` | master_data.py | 8 sales channels |
| `gold_date_dim` | generated | 3yr history + 1yr future |
| `gold_time_dim` | generated | 15-minute intervals |

**Fact Tables (from streaming):**

| Table | Source | Description |
|-------|--------|-------------|
| `gold_sales_fact` | silver_transactions | POS sales |
| `gold_sales_fact_ecommerce` | silver_ecommerce | E-commerce sales |
| `gold_inventory_fact` | silver_inventory | Inventory movements |
| `gold_cart_abandonment_fact` | silver_clickstream | Cart events |

## Master Data (config/master_data.py)

The single source of truth for all reference data:

```python
from config.master_data import (
    # Products
    SKUS, PRODUCT_CATALOG,      # 500 products
    
    # Locations
    STORE_IDS, ALL_LOCATION_IDS, # 10 stores, 3 warehouses
    
    # Channels
    CHANNEL_CODES, POS_CHANNEL,  # 8 channels
    
    # Customers
    CUSTOMER_IDS, CUSTOMER_SEGMENT_MAP, # 10k customers
    
    # Helpers
    get_product_by_sku,
    get_customer_segment,
    get_segment_basket_size,
)

# All generators use these - NO database queries needed
```

## Generators

All generators are self-contained:

```python
from generators import (
    create_pos_generator,
    create_ecommerce_generator,
    create_inventory_generator,
    create_clickstream_generator
)

# No Spark or database connection required!
pos = create_pos_generator(catalog="juan_dev", schema="retail")

# Generate events using master_data reference values
events = pos.generate_batch(10)

# Write to volumes
pos.write_batch_dbutils(dbutils, num_events=100)
```

## Business Rules

Generators implement business rules from `master_data.py`:

**Customer Segments:**
| Segment | Probability | Basket Size | Discount Sensitivity |
|---------|-------------|-------------|---------------------|
| VIP | 5% | 3-8 items | 20% (less sensitive) |
| Premium | 15% | 2-5 items | 40% |
| Loyal | 25% | 2-4 items | 50% |
| Regular | 35% | 1-3 items | 70% |
| New | 20% | 1-2 items | 90% (very sensitive) |

**Seasonality:**
- November: 1.3x (Black Friday)
- December: 1.5x (Holiday peak)
- January: 0.7x (Post-holiday slump)

## Data Quality

The pipeline applies data quality expectations:

```python
@dp.expect("valid_quantity", "qty > 0")
@dp.expect("valid_price", "price >= 0")
@dp.expect_or_drop("has_sku", "sku IS NOT NULL")
```

## Configuration

Pipeline settings in `databricks.yml`:

```yaml
pipelines:
  medallion_streaming_pipeline:
    name: "retail-intelligence-medallion-pipeline"
    catalog: juan_dev
    target: retail
    continuous: false  # Change to true for 24/7 streaming
    libraries:
      - notebook:
          path: ./40-medallion-pipeline/pipelines/bronze_pipeline.py
      - notebook:
          path: ./40-medallion-pipeline/pipelines/silver_pipeline.py
      - notebook:
          path: ./40-medallion-pipeline/pipelines/gold_pipeline.py
```

## Testing Steps

1. **Test master_data imports** (notebook `09-test-self-contained-generators.py`)
   - Verifies imports work without Spark
   
2. **Setup volumes** (notebook `01-setup-volumes.py`)
   - Creates volume directories
   
3. **Generate test data** (notebook `09-test-self-contained-generators.py`)
   - Writes events to volumes
   
4. **Run DLT pipeline**
   - Creates all dimension and fact tables
   
5. **Validate**
   ```sql
   SELECT COUNT(*) FROM juan_dev.retail.gold_product_dim;
   SELECT COUNT(*) FROM juan_dev.retail.gold_sales_fact;
   ```

## Monitoring

After pipeline deployment, monitor via:
- DLT Pipeline UI: View data quality metrics, lineage
- System tables: Query `system.lakeflow.events`
- Unity Catalog: Check table row counts and freshness
