# Refactoring Analysis: Inventory-Aligned Synthetic Data

**Date**: 2025-10-06
**Current Code Review**: `00-data/fashion-retail-fact-generator.py`

## Current Implementation Issues

### 1. Sales Generation (Lines 114-263)
**Problem**: Sales are generated WITHOUT any inventory validation

```python
# Line 212: Quantity chosen randomly with NO inventory check
quantity = random.choice([1, 2, 3])

# Line 236: Sold quantity written directly
'quantity_sold': quantity,  # ← PROBLEM: No validation against available inventory
```

**Impact**: Customers can purchase products that are out of stock

---

### 2. Inventory Generation (Lines 276-358)
**Problem**: Inventory snapshots are generated INDEPENDENTLY of sales

```python
# Lines 288-296: Random inventory levels, no connection to sales
base_qty = random.randint(500, 2000)  # DC
base_qty = random.randint(200, 800)   # Warehouse
base_qty = random.randint(10, 100)    # Store

qty_on_hand = int(self._apply_seasonality_multiplier(base_qty, date_info) *
                 random.uniform(0.5, 1.5))

# Line 316: is_stockout flag exists but doesn't affect sales
is_stockout = qty_available <= 0  # ← Flag is set but NOT used by sales logic
```

**Impact**:
- Inventory levels don't reflect sales deductions
- Stockout flag is cosmetic (doesn't prevent sales)
- No relationship between `gold_sales_fact` and `gold_inventory_fact`

---

### 3. Cart Abandonment (Lines 442-528)
**Problem**: Abandonment rates are fixed percentages, not correlated with inventory

```python
# Abandonment logic uses fixed rates by segment
# NO connection to inventory levels
```

**Impact**: Cart abandonment doesn't increase when products are low stock

---

## Required Changes

### Phase 1: Add New Components (NEW FILES)

#### 1.1 `inventory_manager.py` (NEW - 200 lines)
```python
class InventoryManager:
    """Track inventory state during data generation"""

    def __init__(self):
        # Key: (product_key, location_key, date_key)
        # Value: {qty_available, qty_on_hand, qty_reserved}
        self.inventory_state = {}

    def initialize_inventory(self, date_key, product_keys, location_keys):
        """Set initial inventory for a date"""
        for product_key in product_keys:
            for location_key in location_keys:
                # Existing logic from lines 286-300
                key = (product_key, location_key, date_key)
                self.inventory_state[key] = {
                    'qty_available': self._calculate_initial_qty(...),
                    'qty_on_hand': ...,
                    'qty_reserved': ...
                }

    def deduct_inventory(self, product_key, location_key, date_key, quantity):
        """Deduct from available inventory, return actual deducted amount"""
        key = (product_key, location_key, date_key)
        available = self.inventory_state[key]['qty_available']
        deducted = min(available, quantity)  # ← KEY CONSTRAINT
        self.inventory_state[key]['qty_available'] -= deducted
        return deducted

    def get_available_inventory(self, product_key, location_key, date_key):
        """Check current available quantity"""
        key = (product_key, location_key, date_key)
        return self.inventory_state[key]['qty_available']
```

#### 1.2 `sales_validator.py` (NEW - 150 lines)
```python
class SalesValidator:
    """Validate purchases against inventory"""

    def __init__(self, inventory_manager: InventoryManager):
        self.inventory_manager = inventory_manager

    def validate_purchase(self, product_key, location_key, date_key, requested_qty):
        """
        Validate purchase against available inventory.
        Returns: (allocated_qty, is_constrained)
        """
        available = self.inventory_manager.get_available_inventory(
            product_key, location_key, date_key
        )
        allocated_qty = min(requested_qty, available)
        is_constrained = (allocated_qty < requested_qty)
        return (allocated_qty, is_constrained)

    def allocate_inventory(self, purchase_requests, product_key, location_key, date_key):
        """Randomly allocate limited inventory among competing requests"""
        import random
        shuffled = purchase_requests.copy()
        random.shuffle(shuffled)  # Fair random allocation

        remaining = self.inventory_manager.get_available_inventory(...)
        allocations = []
        for request in shuffled:
            allocated = min(request['qty'], remaining)
            allocations.append((request['customer'], allocated))
            remaining -= allocated
        return allocations
```

#### 1.3 `stockout_generator.py` (NEW - 100 lines)
```python
class StockoutGenerator:
    """Generate stockout events from inventory state"""

    def detect_stockouts(self, date_key, inventory_manager):
        """Find all products with zero inventory"""
        stockouts = []
        for (prod_key, loc_key, date), state in inventory_manager.inventory_state.items():
            if state['qty_available'] == 0:
                stockouts.append({
                    'product_key': prod_key,
                    'location_key': loc_key,
                    'stockout_start_date_key': date_key
                })
        return stockouts
```

---

### Phase 2: Refactor Existing Code

#### 2.1 `fashion-retail-fact-generator.py` Line 16-30 (UPDATED)
```python
# BEFORE:
class FactGenerator:
    def __init__(self, spark: SparkSession, config: dict):
        self.spark = spark
        self.config = config
        self._load_dimensions()
        random.seed(42)

# AFTER:
from inventory_manager import InventoryManager
from sales_validator import SalesValidator
from stockout_generator import StockoutGenerator

class FactGenerator:
    def __init__(self, spark: SparkSession, config: dict):
        self.spark = spark
        self.config = config
        self._load_dimensions()
        random.seed(config.get('random_seed', 42))

        # NEW: Inventory tracking components
        self.inventory_manager = InventoryManager()
        self.sales_validator = SalesValidator(self.inventory_manager)
        self.stockout_generator = StockoutGenerator()
```

#### 2.2 `create_sales_fact()` Lines 114-263 (MAJOR REFACTOR)
```python
# BEFORE (Line 212):
quantity = random.choice([1, 2, 3])

# AFTER:
requested_qty = random.choice([1, 2, 3])
allocated_qty, is_constrained = self.sales_validator.validate_purchase(
    product['product_key'],
    location['location_key'],
    date_info['date_key'],
    requested_qty
)

# Only create sale if inventory allocated
if allocated_qty > 0:
    inventory_before = self.inventory_manager.get_available_inventory(...)

    # Deduct from inventory
    self.inventory_manager.deduct_inventory(
        product['product_key'],
        location['location_key'],
        date_info['date_key'],
        allocated_qty
    )

    sales_record = {
        # ... existing fields ...
        'quantity_sold': allocated_qty,  # ← Changed from 'quantity'
        'quantity_requested': requested_qty,  # ← NEW
        'is_inventory_constrained': is_constrained,  # ← NEW
        'inventory_at_purchase': inventory_before,  # ← NEW
        # ... rest of fields ...
    }
    sales_data.append(sales_record)
else:
    # Track lost sale in stockout events
    pass  # Handled by stockout_generator
```

#### 2.3 `create_inventory_fact()` Lines 276-358 (REFACTOR)
```python
# BEFORE: Random inventory with no sales connection
qty_on_hand = int(self._apply_seasonality_multiplier(base_qty, date_info) *
                 random.uniform(0.5, 1.5))

# AFTER: Initialize inventory ONCE per product-location, then reflect sales
for date_info in self.date_keys:
    # On first date, initialize inventory
    if date_info == self.date_keys[0]:
        self.inventory_manager.initialize_inventory(
            date_info['date_key'],
            [p['product_key'] for p in self.product_keys],
            [l['location_key'] for l in self.location_keys]
        )

    # After sales processed for this date, write snapshot
    for product in self.product_keys:
        for location in self.location_keys:
            state = self.inventory_manager.get_snapshot(
                product['product_key'],
                location['location_key'],
                date_info['date_key']
            )

            inventory_record = {
                'product_key': product['product_key'],
                'location_key': location['location_key'],
                'date_key': date_info['date_key'],
                'quantity_on_hand': state['qty_on_hand'],
                'quantity_available': state['qty_available'],  # ← Reflects sales
                'quantity_reserved': state['qty_reserved'],
                # ... existing fields ...
                'is_stockout': state['qty_available'] == 0,  # ← Actually meaningful now
                'stockout_duration_days': state.get('stockout_days'),  # ← NEW
                # ... rest of fields ...
            }
```

#### 2.4 `create_cart_abandonment_fact()` Lines 442-528 (UPDATED)
```python
# BEFORE: Fixed abandonment rates
base_rate = 0.30  # Fixed 30%

# AFTER: Adjust based on inventory
base_rate = 0.30
inventory_available = self.inventory_manager.get_available_inventory(...)

# NEW: Increase abandonment by 10pp if inventory low
if inventory_available < 5:
    abandonment_rate = base_rate + 0.10  # +10pp increase
    low_inventory_trigger = True
else:
    abandonment_rate = base_rate
    low_inventory_trigger = False

is_abandoned = random.random() < abandonment_rate

abandonment_record = {
    # ... existing fields ...
    'low_inventory_trigger': low_inventory_trigger,  # ← NEW
    'inventory_constrained_items': ...,  # ← NEW
    # ... rest of fields ...
}
```

#### 2.5 `_write_batch()` (UPDATED)
```python
# BEFORE:
BATCH_SIZE = 100_000

# AFTER:
BATCH_SIZE = 50_000  # Reduced for better memory/performance (from research.md)
```

---

### Phase 3: New Delta Tables

#### 3.1 `gold_stockout_events` (NEW TABLE)
```python
def create_stockout_events(self):
    """NEW: Create stockout events table"""
    stockout_data = []

    # Detect stockouts from inventory_manager state
    for date_info in self.date_keys:
        stockouts = self.stockout_generator.detect_stockouts(
            date_info['date_key'],
            self.inventory_manager
        )
        stockout_data.extend(stockouts)

    # Write to Delta
    df = self.spark.createDataFrame(stockout_data, schema=...)
    df.write.mode("overwrite").saveAsTable(f"{self.catalog}.{self.schema}.gold_stockout_events")
```

---

## Execution Order (CRITICAL)

The current implementation generates tables in this order:
1. Dimensions (unchanged)
2. **Sales Fact** (line 121)
3. **Inventory Fact** (line 122)
4. Customer Event Fact (line 123)
5. Cart Abandonment (line 124)

**NEW ORDER REQUIRED**:
1. Dimensions (unchanged)
2. **Initialize Inventory State** (NEW - once per date)
3. **Sales Fact with Validation** (validate → deduct → write)
4. **Inventory Snapshots** (write state AFTER sales deductions)
5. **Stockout Events** (NEW - detect from inventory state)
6. **Cart Abandonment** (with inventory correlation)
7. Customer Event Fact (unchanged)

---

## Configuration Changes

### `fashion-retail-main.py` Lines 383-405 (UPDATED)
```python
# BEFORE:
config = {
    'catalog': 'juan_dev',
    'schema': 'retail',
    'force_recreate': True,
    'customers': 100_000,
    'products': 10_000,
    # ...
}

# AFTER (ADD):
config = {
    # ... existing config ...

    # NEW: Inventory alignment parameters
    'random_seed': 42,  # For reproducibility
    'target_stockout_rate': 0.075,  # 7.5% (midpoint of 5-10%)
    'cart_abandonment_increase': 0.10,  # +10pp for low inventory
    'return_delay_days': (1, 3),  # Random delay between 1-3 days
    'low_inventory_threshold': 5,  # Trigger cart abandonment increase
}
```

---

## Files Impacted Summary

| File | Lines Changed | Type | Priority |
|------|---------------|------|----------|
| `inventory_manager.py` | 200 | NEW | P0 |
| `sales_validator.py` | 150 | NEW | P0 |
| `stockout_generator.py` | 100 | NEW | P1 |
| `fashion-retail-fact-generator.py` (init) | 16-30 | REFACTOR | P0 |
| `fashion-retail-fact-generator.py` (sales) | 114-263 | REFACTOR | P0 |
| `fashion-retail-fact-generator.py` (inventory) | 276-358 | REFACTOR | P0 |
| `fashion-retail-fact-generator.py` (cart) | 442-528 | UPDATE | P1 |
| `fashion-retail-main.py` (config) | 383-405 | UPDATE | P2 |
| `tests/contract/*` | N/A | NEW | P1 |
| `tests/integration/*` | N/A | NEW | P1 |
| `tests/unit/*` | N/A | NEW | P1 |

**Total Estimated Changes**: ~1,200 lines (450 new, 750 refactored)

---

## Validation After Implementation

Run the quickstart.md validation workflow to verify:
1. ✅ Stockout rate: 5-10% of product-location-day combinations
2. ✅ No negative inventory (quantity_available >= 0 always)
3. ✅ Return delays: 1-3 days (uniform distribution)
4. ✅ Cart abandonment: +10pp increase when inventory < 5
5. ✅ Data integrity: Sales never exceed available inventory
