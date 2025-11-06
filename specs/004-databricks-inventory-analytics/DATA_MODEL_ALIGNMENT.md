# Inventory Analytics Genie Spec - Data Model Alignment Analysis

**Date**: 2025-01-27  
**Analysis Purpose**: Validate that the Inventory Analytics Genie specification aligns with available inventory data tables and capabilities

---

## Available Inventory Tables

Based on the `juan_dev.retail` schema, the following inventory-related tables are available:

### Core Inventory Tables
1. **`gold_inventory_fact`** - Daily inventory snapshots (Product × Location × Date grain)
   - Quantities: `quantity_on_hand`, `quantity_available`, `quantity_reserved`, `quantity_in_transit`, `quantity_damaged`
   - Status flags: `is_stockout`, `is_overstock`, `is_discontinued`
   - Metrics: `days_of_supply`, `stock_cover_days`, `stockout_duration_days`
   - Reorder info: `reorder_point`, `reorder_quantity`, `last_replenishment_date`, `next_replenishment_date`
   - Values: `inventory_value_cost`, `inventory_value_retail`

2. **`gold_stockout_events`** - Stockout event tracking
   - Duration: `stockout_start_date_key`, `stockout_end_date_key`, `stockout_duration_days`
   - Impact: `lost_sales_attempts`, `lost_sales_quantity`, `lost_sales_revenue`
   - Context: `peak_season_flag`

3. **`gold_inventory_movement_fact`** - Inventory movement transactions
   - Movement types: `SALE`, `RETURN`, `RECEIPT`, `TRANSFER`, `ADJUSTMENT`
   - Quantities: `quantity_change` (positive for additions, negative for deductions)
   - Return delays: `is_return_delayed`, `return_delay_days`
   - References: `reference_transaction_id` (links to sales)

### Supporting Dimension Tables
- `gold_product_dim` - Product master data (category, brand, price tier, etc.)
- `gold_location_dim` - Location master data (location type, region, city, etc.)
- `gold_date_dim` - Date dimension (calendar, fiscal, seasonality flags)
- `gold_time_dim` - Time dimension

### Related Fact Tables (for context)
- `gold_sales_fact` - Contains `is_inventory_constrained`, `inventory_at_purchase`, `quantity_requested` vs `quantity_sold`
- `gold_cart_abandonment_fact` - Contains `low_inventory_trigger`, `inventory_constrained_items`

---

## Spec Coverage Analysis

### ✅ Well Covered in Spec

| Spec Requirement | Data Support | Notes |
|-----------------|--------------|-------|
| Current stock levels (FR-002) | ✅ `gold_inventory_fact` | All quantity fields available |
| Stockout identification (FR-010) | ✅ `gold_inventory_fact.is_stockout` + `gold_stockout_events` | Both current status and historical events |
| Stockout duration/frequency (FR-010) | ✅ `gold_stockout_events` | Duration, start/end dates available |
| Lost sales impact (FR-010) | ✅ `gold_stockout_events` | lost_sales_attempts, quantity, revenue |
| Overstock identification (FR-004) | ✅ `gold_inventory_fact.is_overstock` | Flag available |
| Days of supply (FR-006) | ✅ `gold_inventory_fact.days_of_supply`, `stock_cover_days` | Both metrics available |
| Reorder identification (FR-007) | ✅ `gold_inventory_fact.reorder_point`, `reorder_quantity` | Reorder logic supported |
| Inventory value (FR-005) | ✅ `gold_inventory_fact.inventory_value_cost`, `inventory_value_retail` | Both cost and retail values |
| Inventory movements (FR-008) | ✅ `gold_inventory_movement_fact` | All movement types supported |
| In-transit inventory (FR-011) | ✅ `gold_inventory_fact.quantity_in_transit` | Current in-transit amounts |
| Replenishment schedule (FR-008) | ✅ `gold_inventory_fact.last_replenishment_date`, `next_replenishment_date` | Schedule tracking available |
| Historical trends (FR-023) | ✅ `gold_inventory_fact` (time-series) | Date dimension enables time-series analysis |

### 📊 Additional Capabilities Available (Not Explicitly in Spec)

| Capability | Data Support | Recommendation |
|------------|--------------|----------------|
| **Damaged inventory tracking** | `gold_inventory_fact.quantity_damaged` | Add to FR-002 or create FR-025 |
| **Reserved inventory tracking** | `gold_inventory_fact.quantity_reserved` | Already covered in FR-002 but could be more explicit |
| **Discontinued product filtering** | `gold_inventory_fact.is_discontinued` | Add to edge cases or FR-002 |
| **Return delay analysis** | `gold_inventory_movement_fact.return_delay_days`, `is_return_delayed` | Could enhance FR-008 |
| **Peak season stockout impact** | `gold_stockout_events.peak_season_flag` | Could enhance FR-010 |
| **Inventory-constrained sales analysis** | `gold_sales_fact.is_inventory_constrained`, `inventory_at_purchase` | Related but in customer behavior domain |
| **Low inventory cart abandonment** | `gold_cart_abandonment_fact.low_inventory_trigger` | Related but in customer behavior domain |
| **Inventory reconciliation** | `gold_inventory_movement_fact` vs `gold_inventory_fact` | Could add to FR-008 |

### 🔍 Potential Spec Enhancements

Based on the data model, consider adding these capabilities:

1. **Damaged Inventory Analysis**
   - Query: "How much inventory is damaged?"
   - Query: "Which products have the highest damaged inventory rates?"
   - Data: `quantity_damaged` in `gold_inventory_fact`

2. **Return Processing Delays**
   - Query: "How long does it take to restock returned inventory?"
   - Query: "Which products have the longest return processing delays?"
   - Data: `return_delay_days` in `gold_inventory_movement_fact`

3. **Peak Season Stockout Impact**
   - Query: "How do stockouts during peak season compare to regular season?"
   - Query: "What is the revenue impact of peak season stockouts?"
   - Data: `peak_season_flag` in `gold_stockout_events`

4. **Reserved Inventory Analysis**
   - Query: "How much inventory is reserved vs available?"
   - Query: "Which products have high reserved inventory ratios?"
   - Data: `quantity_reserved` in `gold_inventory_fact`

5. **Discontinued Product Inventory**
   - Query: "How much inventory value is tied up in discontinued products?"
   - Query: "Which discontinued products have the highest inventory value?"
   - Data: `is_discontinued` in `gold_inventory_fact`

---

## Sample Query Patterns Supported by Data

### Query Pattern 1: Current Stock Status
```sql
-- "What products are currently out of stock?"
SELECT 
    p.product_name,
    l.location_name,
    i.stockout_duration_days,
    i.quantity_available
FROM gold_inventory_fact i
JOIN gold_product_dim p ON i.product_key = p.product_key
JOIN gold_location_dim l ON i.location_key = l.location_key
WHERE i.is_stockout = TRUE
    AND i.date_key = (SELECT MAX(date_key) FROM gold_inventory_fact)
ORDER BY i.stockout_duration_days DESC
```
✅ **Supported** - Covered in Acceptance Scenario #1

### Query Pattern 2: Stockout Risk Assessment
```sql
-- "Which products are at risk of stockout?"
SELECT 
    p.product_name,
    i.days_of_supply,
    i.quantity_available,
    i.reorder_point,
    CASE 
        WHEN i.days_of_supply <= 3 THEN 'High Risk'
        WHEN i.days_of_supply <= 7 THEN 'Medium Risk'
        ELSE 'Low Risk'
    END as risk_level
FROM gold_inventory_fact i
JOIN gold_product_dim p ON i.product_key = p.product_key
WHERE i.date_key = (SELECT MAX(date_key) FROM gold_inventory_fact)
    AND i.quantity_available > 0
    AND i.quantity_available <= i.reorder_point
ORDER BY i.days_of_supply ASC
```
✅ **Supported** - Covered in Acceptance Scenario #2 and FR-003

### Query Pattern 3: Lost Sales from Stockouts
```sql
-- "What is the revenue impact of stockouts?"
SELECT 
    p.product_name,
    COUNT(se.stockout_id) as stockout_count,
    SUM(se.lost_sales_revenue) as total_lost_revenue,
    SUM(se.lost_sales_quantity) as total_lost_quantity,
    AVG(se.stockout_duration_days) as avg_duration_days
FROM gold_stockout_events se
JOIN gold_product_dim p ON se.product_key = p.product_key
GROUP BY p.product_name
ORDER BY total_lost_revenue DESC
```
✅ **Supported** - Covered in FR-010 (stockout impact analysis)

### Query Pattern 4: Inventory Movements Analysis
```sql
-- "What types of inventory movements occurred last month?"
SELECT 
    movement_type,
    COUNT(*) as movement_count,
    SUM(quantity_change) as total_quantity_change,
    AVG(return_delay_days) as avg_return_delay
FROM gold_inventory_movement_fact
WHERE date_key >= DATE_SUB(CURRENT_DATE, 30)
GROUP BY movement_type
ORDER BY movement_count DESC
```
✅ **Supported** - Covered in FR-008

### Query Pattern 5: Replenishment Schedule Analysis
```sql
-- "Which products need replenishment soon?"
SELECT 
    p.product_name,
    l.location_name,
    i.quantity_available,
    i.reorder_point,
    i.next_replenishment_date,
    DATEDIFF(i.next_replenishment_date, CURRENT_DATE) as days_until_replenishment
FROM gold_inventory_fact i
JOIN gold_product_dim p ON i.product_key = p.product_key
JOIN gold_location_dim l ON i.location_key = l.location_key
WHERE i.date_key = (SELECT MAX(date_key) FROM gold_inventory_fact)
    AND i.quantity_available <= i.reorder_point
    AND i.next_replenishment_date IS NOT NULL
ORDER BY days_until_replenishment ASC
```
✅ **Supported** - Covered in Acceptance Scenario #5 and FR-007

---

## Recommendations

### 1. **Spec Enhancement Opportunities** (Optional)

Consider adding these to enrich the spec:

- **FR-025**: System MUST analyze damaged inventory, including damaged quantity by product, location, or category, and identify products with high damage rates
- **FR-026**: System MUST analyze inventory reservation levels, including reserved vs available inventory ratios and products with high reservation rates
- **FR-027**: System MUST analyze return processing delays, including average return delay times by product or category
- **FR-028**: System MUST analyze peak season stockout impact, comparing stockout frequency and lost sales revenue during peak vs regular seasons

### 2. **Data Model Notes**

The spec correctly assumes automatic schema discovery. Ensure table comments include:
- `gold_inventory_fact`: Table description should explain the daily snapshot grain and key metrics
- `gold_stockout_events`: Table description should explain event-based tracking vs snapshot-based
- `gold_inventory_movement_fact`: Table description should explain movement types and reconciliation with inventory_fact

### 3. **Query Pattern Validation**

All acceptance scenarios in the spec are supported by the available data:

| Scenario | Tables Used | Status |
|----------|-------------|--------|
| #1: Current stockouts | `gold_inventory_fact` | ✅ Supported |
| #2: Stockout risk | `gold_inventory_fact` (days_of_supply, reorder_point) | ✅ Supported |
| #3: Overstock | `gold_inventory_fact` (is_overstock) | ✅ Supported |
| #4: Inventory value | `gold_inventory_fact` (inventory_value_cost, inventory_value_retail) | ✅ Supported |
| #5: Reorder needs | `gold_inventory_fact` (reorder_point, quantity_available) | ✅ Supported |
| #6: Days of supply | `gold_inventory_fact` (days_of_supply) | ✅ Supported |
| #7: In-transit inventory | `gold_inventory_fact` (quantity_in_transit) | ✅ Supported |
| #8: Inventory turnover | `gold_inventory_fact` + `gold_sales_fact` (calculable) | ✅ Supported |
| #9: Location stockout rates | `gold_inventory_fact` + `gold_stockout_events` | ✅ Supported |
| #10: Extended stockouts | `gold_stockout_events` (stockout_duration_days) | ✅ Supported |
| #11: Replenishment schedule | `gold_inventory_fact` (last_replenishment_date, next_replenishment_date) | ✅ Supported |

### 4. **Spec Completeness**

**Verdict**: ✅ **The spec is well-aligned with available data**

The specification covers all major inventory analytics capabilities supported by the data model. The optional enhancements listed above would add depth but are not critical for initial implementation.

---

## Conclusion

The Inventory Analytics Genie specification aligns well with the available inventory data tables. All functional requirements are supported by the data model, and all acceptance scenarios can be answered using the available tables.

**Recommendation**: Proceed with the current spec as-is. The optional enhancements (damaged inventory, reservation analysis, return delays, peak season impact) can be added in future iterations if needed.

**Next Steps**:
1. ✅ Spec is ready for `/plan` phase
2. Ensure table comments/descriptions are comprehensive for schema discovery
3. Consider adding the optional enhancements during implementation if user feedback indicates need

