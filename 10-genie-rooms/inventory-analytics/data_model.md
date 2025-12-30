# Data Model: Inventory Analytics Data for Genie

**Feature**: 004-databricks-inventory-analytics
**Date**: 2025-01-27
**Purpose**: Reference documentation for inventory analytics data model - Genie relies on automatic schema discovery from table comments/descriptions

## Overview

This document provides reference information about the inventory analytics data model. **Important**: The Genie space relies on automatic schema discovery from tables added to the space. Tables must have proper comments and descriptions for Genie to understand the data model, relationships, and key metrics effectively.

**Data Model Type**: Star Schema (dimension and fact tables)
**Primary Catalog/Schema**: `juan_dev.retail` (Unity Catalog managed tables)
**Data Volume**: Medium-scale (1-10 million rows per table, occasional multi-table joins)
**Temporal Coverage**: Historical data (forecasting out of scope)

---

## Core Inventory Tables

The Genie space should have access to these inventory-related tables. Tables must include comprehensive comments and descriptions for automatic schema discovery to work effectively.

### gold_inventory_fact
**Purpose**: Daily inventory snapshot fact table with stockout tracking  
**Grain**: Product × Location × Date

**Key Columns** (table comments should describe these):
- `product_key` (INT): Foreign key to product dimension
- `location_key` (INT): Foreign key to location dimension
- `date_key` (INT): Date in YYYYMMDD format
- `quantity_on_hand` (INT): Total physical inventory
- `quantity_available` (INT): Available for sale (after deductions from sales)
- `quantity_reserved` (INT): Reserved for orders
- `quantity_in_transit` (INT): In transit to location
- `quantity_damaged` (INT): Damaged/unsellable inventory
- `is_stockout` (BOOLEAN): True when quantity_available = 0
- `stockout_duration_days` (INT): Consecutive days at zero inventory (NULL if not stockout)
- `is_overstock` (BOOLEAN): True when inventory exceeds normal levels
- `days_of_supply` (INT): Projected days until stockout based on demand
- `stock_cover_days` (INT): Days of inventory coverage
- `reorder_point` (INT): Reorder threshold quantity
- `reorder_quantity` (INT): Standard reorder quantity
- `last_replenishment_date` (DATE): Most recent inventory receipt date
- `next_replenishment_date` (DATE): Scheduled next receipt (fixed schedule)
- `inventory_value_cost` (DOUBLE): Inventory valued at cost
- `inventory_value_retail` (DOUBLE): Inventory valued at retail price

**Relationships**:
- Links to `gold_product_dim` via `product_key`
- Links to `gold_location_dim` via `location_key`
- Links to `gold_date_dim` via `date_key`
- Links to `gold_stockout_events` via product_key + location_key + date_key

**Key Metrics**:
- Stockout Rate: Percentage of (product, location, date) combinations with `is_stockout = TRUE`
- Days of Supply: Calculated based on current inventory and demand patterns
- Inventory Turnover: Can be calculated from inventory_fact and sales_fact

---

### gold_stockout_events
**Purpose**: Stockout event tracking with lost sales metrics  
**Grain**: One record per stockout event (product × location × stockout period)

**Key Columns** (table comments should describe these):
- `stockout_id` (BIGINT): Auto-increment primary key
- `product_key` (INT): Foreign key to product dimension
- `location_key` (INT): Foreign key to location dimension
- `stockout_start_date_key` (INT): First date with zero inventory
- `stockout_end_date_key` (INT): Last date with zero inventory (NULL if ongoing)
- `stockout_duration_days` (INT): Number of consecutive stockout days
- `lost_sales_attempts` (INT): Number of purchase attempts during stockout
- `lost_sales_quantity` (INT): Total quantity requested but unavailable
- `lost_sales_revenue` (DOUBLE): Estimated revenue lost
- `peak_season_flag` (BOOLEAN): TRUE if stockout occurred during peak season

**Relationships**:
- Links to `gold_inventory_fact` via product_key + location_key + date_key
- Links to `gold_product_dim` via `product_key`
- Links to `gold_location_dim` via `location_key`

**Key Metrics**:
- Lost Sales Impact: Revenue lost due to stockouts
- Stockout Frequency: Number of stockout events per product/location
- Peak Season Impact: Comparison of stockout impact during peak vs regular seasons

---

### gold_inventory_movement_fact
**Purpose**: Inventory movement transactions (receipts, transfers, sales, returns, adjustments)  
**Grain**: One record per inventory movement event

**Key Columns** (table comments should describe these):
- `movement_id` (BIGINT): Auto-increment primary key
- `product_key` (INT): Foreign key to product dimension
- `location_key` (INT): Foreign key to location dimension
- `date_key` (INT): Movement date
- `movement_type` (STRING): 'SALE', 'RETURN', 'RECEIPT', 'TRANSFER', 'ADJUSTMENT'
- `quantity_change` (INT): Positive for additions, negative for deductions
- `is_return_delayed` (BOOLEAN): TRUE for returns with 1-3 day delay
- `return_delay_days` (INT): Days between return and restock (1-3)
- `reference_transaction_id` (STRING): Links to sales transaction if movement_type = 'SALE'

**Relationships**:
- Links to `gold_inventory_fact` via product_key + location_key + date_key
- Links to `gold_sales_fact` via reference_transaction_id (for SALE movements)
- Links to `gold_product_dim` via `product_key`
- Links to `gold_location_dim` via `location_key`

**Key Metrics**:
- Replenishment Rate: Count of RECEIPT movements
- Return Processing Time: Average return_delay_days
- Movement Reconciliation: Movements should reconcile with inventory_fact changes

---

## Supporting Dimension Tables

These dimension tables support inventory analytics queries:

### gold_product_dim
**Purpose**: Product master data  
**Key Columns**: product_key, product_name, category_level_1, category_level_2, brand, base_price, is_active

### gold_location_dim
**Purpose**: Location master data  
**Key Columns**: location_key, location_name, location_type, region, city, is_active

### gold_date_dim
**Purpose**: Date dimension with calendar and fiscal attributes  
**Key Columns**: date_key, calendar_date, year, quarter, month, day_name, month_name, season, is_peak_season

---

## Important Notes for Genie Configuration

### Automatic Schema Discovery Requirements

For automatic schema discovery to work effectively, tables must have:

1. **Table-level comments**: Describe purpose, grain, and key metrics
2. **Column-level comments**: Describe each column's purpose, relationships, and calculations
3. **Relationship indicators**: Foreign key relationships should be clear from column names and comments

### Example Table Comment Format

```sql
COMMENT ON TABLE gold_inventory_fact IS 
'Daily inventory snapshot fact table. Grain: Product × Location × Date. 
Tracks inventory levels, stockout status, days of supply, reorder points, and inventory values. 
Use is_stockout flag to identify current stockouts. Use stockout_duration_days for extended stockout analysis.';

COMMENT ON COLUMN gold_inventory_fact.quantity_available IS 
'Available for sale after deductions from sales. Never negative. 
If quantity_available = 0, then is_stockout = TRUE';

COMMENT ON COLUMN gold_inventory_fact.days_of_supply IS 
'Projected days until stockout based on current inventory levels and demand patterns. 
Lower values indicate higher stockout risk.';
```

### Data Quality Notes

- **No Negative Inventory**: `quantity_available` must always be ≥ 0
- **Stockout Validation**: `is_stockout = TRUE` when `quantity_available = 0`
- **Inventory Reconciliation**: Sum of movements should reconcile with inventory_fact changes
- **Date Range**: Historical data only (forecasting out of scope)

---

## Key Analytical Patterns

These patterns help Genie understand common inventory queries:

1. **Current Status**: Query latest date_key for current inventory state
2. **Stockout Risk**: Combine `days_of_supply`, `quantity_available`, and `reorder_point`
3. **Overstock**: Use `is_overstock` flag or compare `days_of_supply` to thresholds
4. **Lost Sales**: Use `gold_stockout_events.lost_sales_revenue` and `lost_sales_quantity`
5. **Replenishment**: Use `last_replenishment_date`, `next_replenishment_date`, and `reorder_point`
6. **Inventory Movements**: Filter `gold_inventory_movement_fact` by `movement_type`
7. **Turnover**: Calculate from inventory_fact and sales_fact (requires joining)
8. **Time-Series**: Use date_dim for historical trends and patterns

---

**Note**: This document serves as reference only. Genie space configuration relies on automatic schema discovery from table comments/descriptions when tables are added to the space.

