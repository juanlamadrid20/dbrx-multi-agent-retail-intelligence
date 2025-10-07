# Data Model: Inventory-Aligned Synthetic Data

**Feature**: Align Customer Behavior Synthetic Data with Real-Time Inventory Data
**Date**: 2025-10-06
**Status**: Design Complete

## Overview

This document defines the enhanced data model for inventory-constrained customer behavior generation. The model extends the existing fashion retail star schema to enforce inventory constraints, track stockouts, and correlate customer behavior with inventory availability.

---

## Core Entities

### 1. Inventory Snapshot (UPDATED)

**Purpose**: Represents the state of inventory for a product at a location on a specific date.

**Delta Table**: `gold_inventory_fact`

**Schema Changes**:
| Column | Type | Updated | Description |
|--------|------|---------|-------------|
| product_key | INTEGER | No | FK to product dimension |
| location_key | INTEGER | No | FK to location dimension |
| date_key | INTEGER | No | Date in YYYYMMDD format |
| quantity_on_hand | INTEGER | No | Total physical inventory |
| quantity_available | INTEGER | **UPDATED** | Available for sale (after sales deductions) |
| quantity_reserved | INTEGER | No | Reserved for orders |
| quantity_in_transit | INTEGER | No | In transit to location |
| quantity_damaged | INTEGER | No | Damaged/unsellable |
| **is_stockout** | **BOOLEAN** | **NEW** | True if qty_available = 0 |
| **stockout_duration_days** | **INTEGER** | **NEW** | Consecutive days at zero inventory |
| **last_replenishment_date** | **DATE** | **NEW** | Most recent inventory receipt |
| **next_replenishment_date** | **DATE** | **NEW** | Scheduled next receipt (fixed schedule) |
| inventory_value_cost | DOUBLE | No | Inventory at cost |
| inventory_value_retail | DOUBLE | No | Inventory at retail price |

**Validation Rules**:
- `quantity_available` ≥ 0 (never negative after sales deduction)
- `is_stockout` = TRUE when `quantity_available` = 0
- `quantity_on_hand` = `quantity_available` + `quantity_reserved` + `quantity_damaged`
- Target: 5-10% of (product_key, location_key, date_key) combinations have `is_stockout` = TRUE

**State Transitions**:
```
Initial State (Day 1): qty_available = base_qty
↓
Sale Deduction: qty_available -= sold_qty (via InventoryManager)
↓
Return Addition (Day N+1 to N+3): qty_available += returned_qty
↓
Replenishment (Fixed Schedule): qty_available += replenishment_qty
↓
Stockout Detection: If qty_available = 0, set is_stockout = TRUE
```

---

### 2. Sales Transaction (UPDATED)

**Purpose**: Represents a customer purchase or attempted purchase, validated against available inventory.

**Delta Table**: `gold_sales_fact`

**Schema Changes**:
| Column | Type | Updated | Description |
|--------|------|---------|-------------|
| transaction_id | STRING | No | Unique transaction ID |
| line_item_id | STRING | No | Unique line item ID |
| customer_key | INTEGER | No | FK to customer dimension |
| product_key | INTEGER | No | FK to product dimension |
| date_key | INTEGER | No | Transaction date |
| location_key | INTEGER | No | FK to location dimension |
| channel_key | INTEGER | No | FK to channel dimension |
| quantity_sold | INTEGER | **UPDATED** | Actual quantity sold (may be < requested) |
| **quantity_requested** | **INTEGER** | **NEW** | Quantity customer wanted |
| **is_inventory_constrained** | **BOOLEAN** | **NEW** | TRUE if qty_sold < qty_requested |
| **inventory_at_purchase** | **INTEGER** | **NEW** | Available inventory before purchase |
| unit_price | DOUBLE | No | Price per unit |
| discount_amount | DOUBLE | No | Discount applied |
| net_sales_amount | DOUBLE | No | Total after discount |
| is_return | BOOLEAN | **UPDATED** | TRUE for return transactions |
| **return_restocked_date_key** | **INTEGER** | **NEW** | Date inventory replenished (1-3 days later) |

**Validation Rules**:
- `quantity_sold` ≤ `quantity_requested` (inventory constraint)
- `quantity_sold` ≤ `inventory_at_purchase` (cannot sell more than available)
- `is_inventory_constrained` = TRUE when `quantity_sold` < `quantity_requested`
- If `is_return` = TRUE, then `return_restocked_date_key` = `date_key` + random(1, 3)

**Relationships**:
- → `gold_inventory_fact`: Validates quantity_sold against quantity_available
- → `gold_stockout_events`: Generates stockout event if inventory_at_purchase = 0
- → `gold_cart_abandonment_fact`: Low inventory triggers increased abandonment

---

### 3. Stockout Event (NEW)

**Purpose**: Records when and for how long a product was unavailable at a location.

**Delta Table**: `gold_stockout_events` (NEW)

**Schema**:
| Column | Type | Description |
|--------|------|-------------|
| stockout_id | BIGINT | Auto-increment primary key |
| product_key | INTEGER | FK to product dimension |
| location_key | INTEGER | FK to location dimension |
| stockout_start_date_key | INTEGER | First date with zero inventory |
| stockout_end_date_key | INTEGER | Last date with zero inventory (NULL if ongoing) |
| stockout_duration_days | INTEGER | Number of consecutive stockout days |
| lost_sales_attempts | INTEGER | Number of purchase attempts during stockout |
| lost_sales_quantity | INTEGER | Total quantity requested but unavailable |
| lost_sales_revenue | DOUBLE | Estimated revenue lost |
| peak_season_flag | BOOLEAN | TRUE if stockout occurred during peak season |
| source_system | STRING | 'SYNTHETIC_DATA_GENERATOR' |
| etl_timestamp | TIMESTAMP | Record creation time |

**Validation Rules**:
- `stockout_end_date_key` ≥ `stockout_start_date_key`
- `stockout_duration_days` = `stockout_end_date_key` - `stockout_start_date_key` + 1
- `lost_sales_attempts` ≥ 0
- `lost_sales_quantity` ≥ `lost_sales_attempts` (customers may want multiple units)

**Relationships**:
- → `gold_inventory_fact`: Links to inventory records with `is_stockout` = TRUE
- → `gold_sales_fact`: Counts purchase attempts with `inventory_at_purchase` = 0

**Generation Logic**:
```python
# When inventory_available reaches 0:
if inventory_available == 0 and not is_already_stockout:
    create_stockout_event(
        start_date=current_date,
        product_key=product_key,
        location_key=location_key
    )

# When inventory replenished:
if inventory_available > 0 and is_stockout:
    close_stockout_event(
        end_date=current_date - 1,
        lost_sales=count_failed_purchases()
    )
```

---

### 4. Cart Abandonment Event (UPDATED)

**Purpose**: Records when customers add products to cart but do not complete purchase, with correlation to inventory levels.

**Delta Table**: `gold_cart_abandonment_fact`

**Schema Changes**:
| Column | Type | Updated | Description |
|--------|------|---------|-------------|
| abandonment_id | INTEGER | No | Primary key |
| cart_id | STRING | No | Unique cart identifier |
| customer_key | INTEGER | No | FK to customer dimension |
| date_key | INTEGER | No | Abandonment date |
| channel_key | INTEGER | No | FK to channel dimension (digital only) |
| cart_value | DOUBLE | No | Total cart value |
| items_count | INTEGER | No | Number of items in cart |
| **low_inventory_trigger** | **BOOLEAN** | **NEW** | TRUE if any item had low/zero inventory |
| **inventory_constrained_items** | **INTEGER** | **NEW** | Count of items with qty_available < 5 |
| abandonment_stage | STRING | No | 'cart', 'shipping', 'payment' |
| suspected_reason | STRING | **UPDATED** | Includes 'out_of_stock' reason |

**Validation Rules**:
- `low_inventory_trigger` = TRUE when any cart item has `inventory_available` < 5
- Baseline abandonment rate: ~30% (varies by segment)
- **Inventory-constrained abandonment rate**: baseline + 10 percentage points
- `inventory_constrained_items` ≤ `items_count`

**Relationships**:
- → `gold_inventory_fact`: Checks inventory levels for cart items
- → `gold_customer_event_fact`: Links to add_to_cart events

**Abandonment Rate Logic**:
```python
# Baseline rates by segment
baseline_abandonment = {
    'vip': 0.20,
    'premium': 0.25,
    'loyal': 0.30,
    'regular': 0.35,
    'new': 0.40
}

# Inventory constraint adjustment
if inventory_constrained:
    abandonment_rate = baseline_abandonment[segment] + 0.10  # +10pp
else:
    abandonment_rate = baseline_abandonment[segment]

# Generate abandonment
is_abandoned = random.random() < abandonment_rate
```

---

### 5. Inventory Movement (UPDATED)

**Purpose**: Records of inventory changes including receipts, transfers, sales depletion, and returns.

**Delta Table**: `gold_inventory_movement_fact`

**Schema Changes**:
| Column | Type | Updated | Description |
|--------|------|---------|-------------|
| movement_id | BIGINT | No | Auto-increment primary key |
| product_key | INTEGER | No | FK to product dimension |
| location_key | INTEGER | No | FK to location dimension |
| date_key | INTEGER | No | Movement date |
| movement_type | STRING | **UPDATED** | 'SALE', 'RETURN', 'RECEIPT', 'TRANSFER', 'ADJUSTMENT' |
| quantity_change | INTEGER | No | Positive for additions, negative for deductions |
| **is_return_delayed** | **BOOLEAN** | **NEW** | TRUE for returns with 1-3 day delay |
| **return_delay_days** | **INTEGER** | **NEW** | Days between return and restock (1-3) |
| reference_transaction_id | STRING | No | Links to sales transaction if movement_type = 'SALE' |
| source_system | STRING | No | Source of the movement record |

**Validation Rules**:
- `quantity_change` ≠ 0
- If `movement_type` = 'RETURN', then `is_return_delayed` = TRUE and `return_delay_days` ∈ {1, 2, 3}
- If `movement_type` = 'RECEIPT', then `quantity_change` > 0 (replenishment on fixed schedule)
- Sum of `quantity_change` for (product, location, date) must reconcile with `gold_inventory_fact.quantity_on_hand`

**Relationships**:
- → `gold_sales_fact`: Links sales to inventory deductions
- → `gold_inventory_fact`: Explains day-over-day inventory changes

---

## Supporting Classes (NEW)

### InventoryManager

**Purpose**: Tracks real-time inventory state during data generation.

**Interface**:
```python
class InventoryManager:
    def initialize_inventory(self, date_key, product_keys, location_keys) -> None:
        """Set initial inventory levels for a date"""

    def deduct_inventory(self, product_key, location_key, date_key, quantity) -> int:
        """Deduct quantity from available inventory, return actual deducted amount"""

    def replenish_inventory(self, product_key, location_key, date_key, quantity) -> None:
        """Add quantity to inventory (returns or scheduled replenishment)"""

    def get_available_inventory(self, product_key, location_key, date_key) -> int:
        """Get current available quantity"""

    def is_stockout(self, product_key, location_key, date_key) -> bool:
        """Check if product is out of stock"""

    def get_snapshot(self, date_key) -> List[Dict]:
        """Get all inventory positions for a date (for Delta write)"""
```

### SalesValidator

**Purpose**: Validates purchase attempts against inventory and handles random allocation.

**Interface**:
```python
class SalesValidator:
    def __init__(self, inventory_manager: InventoryManager):
        self.inventory_manager = inventory_manager

    def validate_purchase(self, product_key, location_key, date_key, requested_qty) -> Tuple[int, bool]:
        """
        Validate purchase against inventory.
        Returns: (allocated_qty, is_constrained)
        """

    def allocate_inventory(self, purchase_requests, product_key, location_key, date_key) -> List[Tuple]:
        """
        Randomly allocate limited inventory among competing requests.
        Returns: List of (customer_key, allocated_qty, fulfilled)
        """
```

### StockoutGenerator

**Purpose**: Detects and generates stockout events.

**Interface**:
```python
class StockoutGenerator:
    def __init__(self, inventory_manager: InventoryManager):
        self.inventory_manager = inventory_manager

    def detect_stockouts(self, date_key) -> List[Dict]:
        """Find all products with zero inventory on date"""

    def create_stockout_event(self, product_key, location_key, start_date_key) -> Dict:
        """Create new stockout event"""

    def close_stockout_event(self, stockout_id, end_date_key, lost_sales) -> None:
        """Update stockout event when inventory replenished"""

    def calculate_lost_sales(self, product_key, location_key, start_date, end_date) -> Tuple[int, int, float]:
        """Calculate lost attempts, quantity, revenue during stockout"""
```

---

## Data Flow

```
Day N Initialization:
├─> InventoryManager.initialize_inventory(date_key=N)
├─> Load customer, product, location dimensions
└─> Begin transaction generation

For each customer transaction:
├─> Select product, location, channel
├─> SalesValidator.validate_purchase(product, location, date, qty)
│   ├─> InventoryManager.get_available_inventory()
│   └─> Return (allocated_qty, is_constrained)
├─> If allocated_qty > 0: Create sales record
├─> If allocated_qty < requested_qty: Record lost sales
├─> InventoryManager.deduct_inventory(allocated_qty)
└─> Check for stockout trigger

End of Day N:
├─> StockoutGenerator.detect_stockouts(date_key=N)
├─> InventoryManager.get_snapshot(date_key=N)
├─> Write inventory_fact records to Delta
└─> Advance to Day N+1

Return Processing (Day N+X):
├─> For each return from Day N:
│   └─> If days_since_return ∈ {1,2,3}:
│       └─> InventoryManager.replenish_inventory(return_qty)
└─> Write inventory_movement record
```

---

## Validation Queries

### Check Stockout Rate (Should be 5-10%)
```sql
SELECT
  COUNT(DISTINCT CONCAT(product_key, '_', location_key, '_', date_key)) AS total_positions,
  SUM(CASE WHEN is_stockout THEN 1 ELSE 0 END) AS stockout_positions,
  (SUM(CASE WHEN is_stockout THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS stockout_rate_pct
FROM gold_inventory_fact
-- Expected: stockout_rate_pct BETWEEN 5.0 AND 10.0
```

### Validate No Negative Inventory
```sql
SELECT COUNT(*) AS negative_inventory_count
FROM gold_inventory_fact
WHERE quantity_available < 0
-- Expected: 0
```

### Validate Return Delays (1-3 days)
```sql
SELECT
  DATEDIFF(DAY, CAST(s.date_key AS STRING), CAST(m.date_key AS STRING)) AS delay_days,
  COUNT(*) AS return_count
FROM gold_sales_fact s
JOIN gold_inventory_movement_fact m
  ON s.transaction_id = m.reference_transaction_id
WHERE s.is_return = TRUE
  AND m.movement_type = 'RETURN'
GROUP BY delay_days
-- Expected: delay_days ∈ {1, 2, 3}
```

### Validate Cart Abandonment Increase
```sql
SELECT
  low_inventory_trigger,
  COUNT(*) AS total_carts,
  AVG(CASE WHEN recovery_email_sent THEN 0 ELSE 1 END) AS abandonment_rate
FROM gold_cart_abandonment_fact
GROUP BY low_inventory_trigger
-- Expected: abandonment_rate(low_inventory=TRUE) ≈ abandonment_rate(low_inventory=FALSE) + 0.10
```

---

## Summary

This data model extends the existing fashion retail star schema to enforce inventory-aligned customer behavior:

**New Tables**: 1 (gold_stockout_events)
**Updated Tables**: 4 (gold_inventory_fact, gold_sales_fact, gold_cart_abandonment_fact, gold_inventory_movement_fact)
**New Columns**: 15 across updated tables
**New Classes**: 3 (InventoryManager, SalesValidator, StockoutGenerator)

All changes maintain backwards compatibility via Delta Lake schema evolution.
