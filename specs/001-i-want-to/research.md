# Research: Inventory-Aligned Synthetic Data Generation

**Feature**: Align Customer Behavior Synthetic Data with Real-Time Inventory Data
**Date**: 2025-10-06
**Status**: Complete

## Overview

This document consolidates research findings for implementing inventory-constrained customer behavior generation in the Databricks fashion retail synthetic data pipeline. The research addresses five key technical areas required for the implementation.

---

## 1. PySpark Stateful Processing Patterns

### Research Question
How to efficiently track inventory levels for 10K products × 13 locations × 730 days in PySpark?

### Decision: In-Memory Dictionary with Periodic Checkpointing

**Rationale**:
- **Scale**: 10K products × 13 locations = 130K inventory positions. At daily granularity for 730 days, this is manageable in memory (~50-100MB for state tracking)
- **Performance**: In-memory dictionary operations are O(1) for lookups and updates, critical for processing millions of transactions
- **Simplicity**: Direct state mutation is easier to reason about than distributed state management
- **Databricks Context**: Single-driver execution for data generation doesn't benefit from distributed state

**Approach**:
```python
class InventoryManager:
    def __init__(self):
        # Key: (product_key, location_key, date_key)
        # Value: {qty_available, qty_reserved, qty_on_hand}
        self.inventory_state = {}

    def initialize_inventory(self, date_key, product_keys, location_keys):
        """Set initial inventory levels for a date"""
        for product_key in product_keys:
            for location_key in location_keys:
                key = (product_key, location_key, date_key)
                self.inventory_state[key] = {
                    'qty_available': self._calculate_initial_qty(...),
                    'qty_reserved': 0,
                    'qty_on_hand': self._calculate_initial_qty(...)
                }

    def deduct_inventory(self, product_key, location_key, date_key, quantity):
        """Deduct quantity if available, return actual deducted amount"""
        key = (product_key, location_key, date_key)
        available = self.inventory_state[key]['qty_available']
        deducted = min(available, quantity)
        self.inventory_state[key]['qty_available'] -= deducted
        self.inventory_state[key]['qty_on_hand'] -= deducted
        return deducted
```

**Alternatives Considered**:
- **Broadcast Variables**: Read-only, doesn't support state mutation
- **Delta Lake MERGE**: Too slow for millions of micro-updates (designed for batch operations)
- **Accumulators**: Not designed for complex state tracking, limited to aggregations

**Performance Notes**:
- Checkpoint every 100 dates to persist inventory snapshots to Delta
- Memory footprint: ~130K entries × 100 bytes ≈ 13MB (negligible)
- Lookups/updates: O(1) with Python dict

---

## 2. Delta Lake Schema Evolution

### Research Question
How to add `stockout_flag`, `lost_sales_qty` columns to `gold_sales_fact` without breaking downstream consumers?

### Decision: Schema Evolution with Default Values

**Rationale**:
- Delta Lake supports automatic schema evolution via `mergeSchema` option
- New columns added with NULL or default values preserve backwards compatibility
- Downstream consumers (Genie, BI tools) handle new columns gracefully (ignore unknown fields)

**Migration Strategy**:
```python
# Option 1: Add columns during write (preferred for new data)
df.write \
    .mode("append") \
    .option("mergeSchema", "true") \
    .saveAsTable("gold_sales_fact")

# Option 2: ALTER TABLE for existing data (adds NULL columns)
spark.sql("""
    ALTER TABLE gold_sales_fact
    ADD COLUMNS (
        stockout_flag BOOLEAN COMMENT 'Whether purchase was attempted during stockout',
        lost_sales_qty INT COMMENT 'Quantity customer wanted but unavailable',
        inventory_check_timestamp TIMESTAMP COMMENT 'When inventory was validated'
    )
""")
```

**Backwards Compatibility**:
- Existing queries selecting `*` will see new columns (may need `SELECT col1, col2` for strict schemas)
- Aggregate functions (COUNT, SUM) unaffected
- Genie spaces automatically adapt to new schema

**Alternatives Considered**:
- **New Table**: Creates data duplication, complex migration path
- **Column Mapping**: Adds unnecessary complexity for simple additions
- **Versioned Tables**: Overkill for additive schema changes

**Best Practices**:
- Use `COMMENT` to document new columns
- Set explicit defaults for new columns (NULL is acceptable)
- Update table properties to track schema version:
  ```sql
  ALTER TABLE gold_sales_fact
  SET TBLPROPERTIES ('schema_version' = '2.0', 'last_schema_change' = '2025-10-06')
  ```

---

## 3. Randomization with Constraints

### Research Question
How to randomly distribute limited inventory among competing purchase attempts?

### Decision: Shuffle-Based Random Allocation

**Rationale**:
- Simple, efficient, and truly random
- Preserves fairness across customer segments (no priority bias)
- O(n log n) complexity for sorting, acceptable for daily transaction volumes

**Algorithm**:
```python
def allocate_inventory(purchase_requests, available_inventory):
    """
    Randomly allocate limited inventory among purchase requests.

    Args:
        purchase_requests: List of (customer_key, product_key, location_key, desired_qty)
        available_inventory: int (current available quantity)

    Returns:
        List of (customer_key, allocated_qty, fulfilled: bool)
    """
    import random

    # Shuffle requests for randomness
    shuffled_requests = purchase_requests.copy()
    random.shuffle(shuffled_requests)

    results = []
    remaining_inventory = available_inventory

    for request in shuffled_requests:
        customer_key, product_key, location_key, desired_qty = request
        allocated_qty = min(desired_qty, remaining_inventory)
        fulfilled = (allocated_qty == desired_qty)
        remaining_inventory -= allocated_qty

        results.append((customer_key, allocated_qty, fulfilled))

        if remaining_inventory == 0:
            # Remaining requests get zero allocation
            for unfulfilled_request in shuffled_requests[len(results):]:
                results.append((unfulfilled_request[0], 0, False))
            break

    return results
```

**Alternatives Considered**:
- **Reservoir Sampling**: Overcomplicated for this use case (designed for stream sampling)
- **Weighted Selection**: Would bias towards certain customers (violates random allocation requirement)
- **Priority Queue**: Would introduce segment-based priority (clarification confirmed no priority)

**Performance**:
- Shuffling 500 daily requests: ~0.1ms (negligible)
- Total allocations per day: ~500 products with contention = 2,500 allocations
- Expected runtime: <1 second per day of data generation

---

## 4. Testing Databricks Workflows

### Research Question
How to write tests that run both in pytest (local) and Databricks notebooks?

### Decision: PySpark Test Fixtures with Conditional Spark Session

**Approach**:
```python
# conftest.py - pytest fixtures
import pytest
from pyspark.sql import SparkSession

@pytest.fixture(scope="session")
def spark():
    """Create local Spark session for testing"""
    return SparkSession.builder \
        .appName("test") \
        .master("local[2]") \
        .config("spark.sql.shuffle.partitions", "2") \
        .config("spark.default.parallelism", "2") \
        .getOrCreate()

@pytest.fixture
def sample_customers(spark):
    """Generate sample customer dimension data"""
    from datetime import date
    data = [
        (1, "CUST_001", "vip", "web", date(2024, 1, 1)),
        (2, "CUST_002", "regular", "store", date(2024, 2, 1)),
    ]
    return spark.createDataFrame(data, ["customer_key", "customer_id", "segment", "preferred_channel", "acquisition_date"])

# test_inventory_manager.py
def test_deduct_inventory(spark):
    from inventory_manager import InventoryManager

    manager = InventoryManager()
    manager.initialize_inventory(date_key=20250101, product_keys=[1], location_keys=[1])
    manager.inventory_state[(1, 1, 20250101)] = {'qty_available': 10, 'qty_on_hand': 10}

    # Test successful deduction
    deducted = manager.deduct_inventory(1, 1, 20250101, 5)
    assert deducted == 5
    assert manager.inventory_state[(1, 1, 20250101)]['qty_available'] == 5

    # Test partial deduction (inventory constraint)
    deducted = manager.deduct_inventory(1, 1, 20250101, 10)
    assert deducted == 5  # Only 5 available
    assert manager.inventory_state[(1, 1, 20250101)]['qty_available'] == 0
```

**Databricks Notebook Execution**:
```python
# In Databricks notebook, Spark session already exists
# Tests can import and run directly:
%run ./tests/unit/test_inventory_manager

# Or use pytest in Databricks notebook:
!pip install pytest
!pytest tests/unit/test_inventory_manager.py -v
```

**Best Practices**:
- Use `local[2]` for pytest (faster than cluster mode)
- Set small shuffle partitions for test data (default 200 is overkill)
- Mock Delta table writes in unit tests (use DataFrames, not actual tables)
- Integration tests run on Databricks with real Delta tables

**Alternatives Considered**:
- **Chispa**: DataFrame comparison library (useful but not required for basic tests)
- **Mock Spark**: Too complex, real local Spark is fast enough
- **Separate test codebases**: Violates DRY, hard to maintain

---

## 5. Performance Optimization

### Research Question
Optimal batch size for Delta writes when generating 100K+ transaction records?

### Decision: 50K Record Batches

**Rationale**:
- **Current**: 100K batches work but consume ~500MB memory per batch
- **Optimized**: 50K batches reduce memory to ~250MB, improve write latency
- **Delta Lake**: Prefers smaller, more frequent writes for better file sizing (target: 128MB parquet files)

**Implementation**:
```python
def _write_batch(self, data, table_name, mode='append'):
    """Write data in optimized batches"""
    BATCH_SIZE = 50_000  # Reduced from 100K

    if len(data) >= BATCH_SIZE:
        df = self.spark.createDataFrame(data)
        df.write \
            .mode(mode) \
            .option("mergeSchema", "true") \
            .option("optimizeWrite", "true") \  # Enable auto-optimization
            .option("autoOptimize", "true") \   # Enable auto-compaction
            .saveAsTable(f"{self.catalog}.{self.schema}.{table_name}")
        return []  # Clear data
    return data
```

**Performance Improvements**:
- **Memory**: 50% reduction in peak memory usage (500MB → 250MB per batch)
- **Latency**: Faster write operations (less data per transaction)
- **File Size**: Better parquet file sizing (closer to 128MB optimal)
- **Compaction**: Less frequent OPTIMIZE operations needed

**Delta Lake Optimizations**:
```python
# Enable liquid clustering (Databricks Runtime 13.3+)
spark.sql(f"""
    ALTER TABLE {catalog}.{schema}.gold_sales_fact
    CLUSTER BY (date_key, product_key, location_key)
""")

# Or use Z-Ordering for older runtimes
spark.sql(f"""
    OPTIMIZE {catalog}.{schema}.gold_sales_fact
    ZORDER BY (date_key, product_key)
""")
```

**Alternatives Considered**:
- **100K batches**: Current approach, works but suboptimal memory
- **10K batches**: Too many small writes, overhead increases
- **Streaming writes**: Overkill for batch data generation

**Recommendations**:
- Use 50K batch size for transaction tables (sales_fact, events)
- Use 10K batch size for dimension updates (smaller, more precise control)
- Enable `optimizeWrite` and `autoOptimize` for automatic tuning
- Run OPTIMIZE weekly on large fact tables

---

## Summary of Decisions

| Area | Decision | Impact |
|------|----------|--------|
| State Management | In-memory dictionary | Enables efficient O(1) inventory lookups |
| Schema Evolution | `mergeSchema` with ALTER TABLE | Backwards-compatible column additions |
| Random Allocation | Shuffle-based allocation | Fair, unbiased distribution (per clarification) |
| Testing Strategy | PySpark fixtures + pytest | Local testing + Databricks integration |
| Batch Size | 50K records per write | 50% memory reduction, better file sizing |

---

## Implementation Checklist

- [ ] Create `InventoryManager` class with in-memory state tracking
- [ ] Add schema evolution logic to `FactGenerator._write_batch()`
- [ ] Implement shuffle-based allocation in `SalesValidator`
- [ ] Set up pytest fixtures in `tests/conftest.py`
- [ ] Update batch size constant to 50K in all generators
- [ ] Add Delta Lake optimization commands to post-generation workflow

---

**Research Complete**: All technical unknowns resolved. Ready for Phase 1 (Design & Contracts).
