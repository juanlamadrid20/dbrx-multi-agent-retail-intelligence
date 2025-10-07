# Quickstart: Inventory-Aligned Synthetic Data Validation

**Feature**: Align Customer Behavior Synthetic Data with Real-Time Inventory Data
**Purpose**: Validate that synthetic data generation correctly enforces inventory constraints
**Time to Complete**: ~30 minutes

---

## Prerequisites

- Databricks workspace access
- Unity Catalog enabled (catalog: `juan_dev`, schema: `retail`)
- Python 3.11+ with PySpark
- Existing fashion retail star schema tables

---

## Step 1: Run Data Generation with Seed

**Goal**: Generate inventory-aligned synthetic data with reproducible randomness

### 1.1 Execute Data Generation

```python
# In Databricks notebook or Python script
from fashion_retail_main import FashionRetailDataGenerator
from pyspark.sql import SparkSession

# Initialize Spark
spark = SparkSession.builder \
    .appName("Inventory Aligned Data Generation") \
    .getOrCreate()

# Configuration
config = {
    'catalog': 'juan_dev',
    'schema': 'retail',
    'force_recreate': True,  # Drop existing tables

    # Scale parameters
    'customers': 100_000,
    'products': 10_000,
    'locations': 13,
    'historical_days': 730,
    'events_per_day': 500_000,

    # NEW: Inventory alignment seed
    'random_seed': 42,  # For reproducibility
    'target_stockout_rate': 0.075,  # 7.5% (midpoint of 5-10%)
    'cart_abandonment_increase': 0.10,  # +10pp for low inventory

    # Features
    'enable_cdc': True,
    'enable_liquid_clustering': True,
}

# Run generator
generator = FashionRetailDataGenerator(spark, config)
generator.run()
```

### 1.2 Expected Output

```
================================================================================
Starting Fashion Retail Data Generation Pipeline
Configuration: {...}
================================================================================
Setting up catalog: juan_dev.retail
Generating dimension tables...
Created customer dimension with 100,000 records
Created product dimension with 10,000 records
Created location dimension with 13 records
...
Generating fact tables with inventory alignment...
Loaded dimensions: 100,000 customers, 10,000 products, 13 locations
Generating sales fact table with inventory validation...
Created sales fact table with ~15,000,000 transactions
Generating inventory fact table with stockout tracking...
Created inventory fact table with daily snapshots
Generating stockout events...
Created stockout events with ~75,000 events  ← Should be 5-10% of positions
...
Pipeline completed successfully in 450.00 seconds
Data available in: juan_dev.retail
================================================================================
```

---

## Step 2: Validate Stockout Rate (5-10%)

**Goal**: Verify that 5-10% of product-location-day combinations experience stockouts

### 2.1 Query Stockout Rate

```sql
-- Calculate overall stockout rate
SELECT
  COUNT(DISTINCT CONCAT(product_key, '_', location_key, '_', date_key)) AS total_positions,
  SUM(CASE WHEN is_stockout THEN 1 ELSE 0 END) AS stockout_positions,
  ROUND(SUM(CASE WHEN is_stockout THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS stockout_rate_pct
FROM juan_dev.retail.gold_inventory_fact;
```

### 2.2 Expected Results

| Metric | Expected Value | Pass Criteria |
|--------|----------------|---------------|
| total_positions | ~9,490,000 | (10K products × 13 locations × 730 days) |
| stockout_positions | 474,500 - 949,000 | 5-10% of total |
| stockout_rate_pct | 5.0 - 10.0 | ✅ PASS if in range |

### 2.3 Breakdown by Product Category

```sql
-- Stockout rate by product category
SELECT
  p.category_level_1,
  COUNT(DISTINCT CONCAT(i.product_key, '_', i.location_key, '_', i.date_key)) AS positions,
  SUM(CASE WHEN i.is_stockout THEN 1 ELSE 0 END) AS stockouts,
  ROUND(SUM(CASE WHEN i.is_stockout THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS stockout_rate_pct
FROM juan_dev.retail.gold_inventory_fact i
JOIN juan_dev.retail.gold_product_dim p ON i.product_key = p.product_key
GROUP BY p.category_level_1
ORDER BY stockout_rate_pct DESC;
```

**Expected**: All categories should have stockout rates between 5-10%

---

## Step 3: Validate Inventory Consistency (No Negative Quantities)

**Goal**: Ensure sales deductions never cause negative inventory

### 3.1 Check for Negative Inventory

```sql
-- Find any negative inventory positions
SELECT COUNT(*) AS negative_inventory_count
FROM juan_dev.retail.gold_inventory_fact
WHERE quantity_available < 0;
```

**Expected**: `negative_inventory_count` = 0 ✅

### 3.2 Validate Sales vs. Inventory

```sql
-- Verify sales never exceed available inventory
SELECT
  s.date_key,
  s.product_key,
  s.location_key,
  SUM(s.quantity_sold) AS total_sold,
  MAX(s.inventory_at_purchase) AS inventory_before_sales,
  COUNT(*) AS transaction_count
FROM juan_dev.retail.gold_sales_fact s
WHERE s.inventory_at_purchase < s.quantity_sold  -- Impossible scenario
GROUP BY s.date_key, s.product_key, s.location_key
HAVING COUNT(*) > 0;
```

**Expected**: 0 rows returned ✅

### 3.3 Reconcile Inventory Snapshots

```sql
-- Verify quantity_on_hand = quantity_available + quantity_reserved + quantity_damaged
SELECT COUNT(*) AS reconciliation_errors
FROM juan_dev.retail.gold_inventory_fact
WHERE quantity_on_hand <> (quantity_available + quantity_reserved + quantity_damaged);
```

**Expected**: `reconciliation_errors` = 0 ✅

---

## Step 4: Validate Return Delays (1-3 Days)

**Goal**: Confirm returns replenish inventory 1-3 days after return date

### 4.1 Check Return Delay Distribution

```sql
-- Calculate return delay distribution
WITH return_delays AS (
  SELECT
    s.transaction_id,
    s.date_key AS return_date,
    s.return_restocked_date_key AS restock_date,
    (s.return_restocked_date_key - s.date_key) AS delay_days
  FROM juan_dev.retail.gold_sales_fact s
  WHERE s.is_return = TRUE
    AND s.return_restocked_date_key IS NOT NULL
)
SELECT
  delay_days,
  COUNT(*) AS return_count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS percentage
FROM return_delays
GROUP BY delay_days
ORDER BY delay_days;
```

### 4.2 Expected Results

| delay_days | return_count | percentage | Pass? |
|------------|--------------|------------|-------|
| 1 | ~33,333 | ~33.33% | ✅ |
| 2 | ~33,333 | ~33.33% | ✅ |
| 3 | ~33,333 | ~33.33% | ✅ |
| Other | 0 | 0% | ✅ |

**Expected**: All returns have delays of exactly 1, 2, or 3 days (uniform distribution)

### 4.3 Validate Inventory Replenishment

```sql
-- Verify returns actually replenish inventory
SELECT
  s.product_key,
  s.location_key,
  s.date_key AS return_date,
  s.quantity_sold AS return_qty,
  i_before.quantity_available AS inventory_before_restock,
  i_after.quantity_available AS inventory_after_restock,
  (i_after.quantity_available - i_before.quantity_available) AS inventory_increase
FROM juan_dev.retail.gold_sales_fact s
JOIN juan_dev.retail.gold_inventory_fact i_before
  ON s.product_key = i_before.product_key
  AND s.location_key = i_before.location_key
  AND i_before.date_key = s.return_restocked_date_key - 1
JOIN juan_dev.retail.gold_inventory_fact i_after
  ON s.product_key = i_after.product_key
  AND s.location_key = i_after.location_key
  AND i_after.date_key = s.return_restocked_date_key
WHERE s.is_return = TRUE
LIMIT 100;
```

**Expected**: `inventory_increase` should approximately equal `return_qty` (allowing for same-day sales)

---

## Step 5: Validate Cart Abandonment Correlation

**Goal**: Confirm abandonment rates increase by 10pp when inventory is low

### 5.1 Calculate Abandonment Rates by Inventory Status

```sql
-- Compare abandonment rates for low vs. normal inventory
SELECT
  low_inventory_trigger,
  COUNT(*) AS total_carts,
  SUM(CASE WHEN is_recovered = FALSE THEN 1 ELSE 0 END) AS abandoned_carts,
  ROUND(SUM(CASE WHEN is_recovered = FALSE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS abandonment_rate_pct
FROM juan_dev.retail.gold_cart_abandonment_fact
GROUP BY low_inventory_trigger
ORDER BY low_inventory_trigger;
```

### 5.2 Expected Results

| low_inventory_trigger | total_carts | abandoned_carts | abandonment_rate_pct | Pass? |
|-----------------------|-------------|-----------------|----------------------|-------|
| FALSE (normal inventory) | ~400,000 | ~120,000 | ~30.0% | ✅ (baseline) |
| TRUE (low inventory) | ~100,000 | ~40,000 | ~40.0% | ✅ (+10pp) |

**Pass Criteria**: `abandonment_rate_pct(TRUE)` ≈ `abandonment_rate_pct(FALSE)` + 10.0

### 5.3 Breakdown by Customer Segment

```sql
-- Abandonment rate increase by customer segment
SELECT
  c.segment,
  ca.low_inventory_trigger,
  COUNT(*) AS cart_count,
  ROUND(AVG(CASE WHEN ca.is_recovered = FALSE THEN 1.0 ELSE 0.0 END) * 100, 2) AS abandonment_rate_pct
FROM juan_dev.retail.gold_cart_abandonment_fact ca
JOIN juan_dev.retail.gold_customer_dim c ON ca.customer_key = c.customer_key
WHERE c.is_current = TRUE
GROUP BY c.segment, ca.low_inventory_trigger
ORDER BY c.segment, ca.low_inventory_trigger;
```

**Expected**: All segments show ~10pp increase in abandonment when `low_inventory_trigger = TRUE`

---

## Step 6: End-to-End Integration Validation

**Goal**: Verify complete data alignment across all tables

### 6.1 Stockout Event Completeness

```sql
-- Verify stockout events match inventory stockouts
WITH inventory_stockouts AS (
  SELECT
    product_key,
    location_key,
    date_key,
    is_stockout
  FROM juan_dev.retail.gold_inventory_fact
  WHERE is_stockout = TRUE
),
event_stockouts AS (
  SELECT DISTINCT
    se.product_key,
    se.location_key,
    d.date_key
  FROM juan_dev.retail.gold_stockout_events se
  CROSS JOIN LATERAL (
    SELECT date_key
    FROM juan_dev.retail.gold_date_dim
    WHERE date_key BETWEEN se.stockout_start_date_key AND COALESCE(se.stockout_end_date_key, se.stockout_start_date_key)
  ) d
)
SELECT
  (SELECT COUNT(*) FROM inventory_stockouts) AS inventory_stockout_count,
  (SELECT COUNT(*) FROM event_stockouts) AS event_stockout_count,
  (SELECT COUNT(*) FROM inventory_stockouts) - (SELECT COUNT(*) FROM event_stockouts) AS difference
;
```

**Expected**: `difference` should be close to 0 (minor discrepancies acceptable due to timing)

### 6.2 Lost Sales Tracking

```sql
-- Validate lost sales during stockouts
SELECT
  se.stockout_id,
  se.product_key,
  se.location_key,
  se.lost_sales_attempts,
  se.lost_sales_quantity,
  COUNT(s.line_item_id) AS actual_failed_attempts,
  SUM(s.quantity_requested - s.quantity_sold) AS actual_lost_quantity
FROM juan_dev.retail.gold_stockout_events se
LEFT JOIN juan_dev.retail.gold_sales_fact s
  ON se.product_key = s.product_key
  AND se.location_key = s.location_key
  AND s.date_key BETWEEN se.stockout_start_date_key AND COALESCE(se.stockout_end_date_key, se.stockout_start_date_key)
  AND s.inventory_at_purchase = 0
GROUP BY se.stockout_id, se.product_key, se.location_key, se.lost_sales_attempts, se.lost_sales_quantity
LIMIT 100;
```

**Expected**: `lost_sales_attempts` ≈ `actual_failed_attempts` and `lost_sales_quantity` ≈ `actual_lost_quantity`

---

## Summary Checklist

- [ ] **Stockout Rate**: 5-10% of product-location-day combinations (Step 2) ✅
- [ ] **No Negative Inventory**: Zero records with quantity_available < 0 (Step 3) ✅
- [ ] **Return Delays**: All returns restocked 1-3 days later (Step 4) ✅
- [ ] **Cart Abandonment**: +10pp increase for low inventory (Step 5) ✅
- [ ] **Data Integrity**: Stockout events match inventory records (Step 6) ✅

---

## Troubleshooting

### Issue: Stockout rate outside 5-10% range

**Cause**: Inventory initialization or depletion logic incorrect

**Fix**:
1. Check `config['target_stockout_rate']` setting (should be 0.05-0.10)
2. Verify `InventoryManager._calculate_initial_qty()` logic
3. Review `SalesValidator.validate_purchase()` deduction logic

### Issue: Negative inventory quantities

**Cause**: Race condition in inventory deduction or missing validation

**Fix**:
1. Ensure `SalesValidator.validate_purchase()` checks `available_qty` before allocation
2. Verify `InventoryManager.deduct_inventory()` returns `min(requested, available)`
3. Check for concurrent writes to same product-location-date

### Issue: Return delays not in 1-3 day range

**Cause**: Return restock date calculation error

**Fix**:
1. Verify `FactGenerator.create_sales_fact()` sets `return_restocked_date_key = date_key + random(1,3)`
2. Check `random.seed(42)` is set for reproducibility

### Issue: Cart abandonment rate increase ≠ 10pp

**Cause**: Baseline rate incorrect or inventory trigger not firing

**Fix**:
1. Verify baseline abandonment rates by segment
2. Check `low_inventory_trigger` logic (should fire when any cart item has `qty_available < 5`)
3. Ensure `+0.10` adjustment is applied correctly

---

## Next Steps

After successful validation:
1. Run `/tasks` to generate implementation tasks
2. Execute tasks to implement the feature
3. Re-run this quickstart to validate implementation
4. Deploy to production Databricks workspace

---

**Validation Complete**: All data alignment requirements met ✅
