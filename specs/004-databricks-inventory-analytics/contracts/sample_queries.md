# Sample Queries: Inventory Analytics Genie

Sample queries organized by analytical category to help Genie learn query patterns and translate natural language to SQL. These queries cover all functional requirements (FR-001 through FR-024) and acceptance scenarios.

---

## Current Stock Status & Levels

**Complexity**: Simple  
**Covers**: FR-002

What products are currently out of stock?
```sql
SELECT 
    p.product_name,
    l.location_name,
    i.stockout_duration_days,
    i.quantity_available,
    i.last_replenishment_date
FROM gold_inventory_fact i
JOIN gold_product_dim p ON i.product_key = p.product_key
JOIN gold_location_dim l ON i.location_key = l.location_key
WHERE i.is_stockout = TRUE
    AND i.date_key = (SELECT MAX(date_key) FROM gold_inventory_fact)
ORDER BY i.stockout_duration_days DESC NULLS LAST;
```

What is the current inventory level for product X at location Y?
```sql
SELECT 
    p.product_name,
    l.location_name,
    i.quantity_on_hand,
    i.quantity_available,
    i.quantity_reserved,
    i.quantity_in_transit,
    i.quantity_damaged,
    i.is_stockout
FROM gold_inventory_fact i
JOIN gold_product_dim p ON i.product_key = p.product_key
JOIN gold_location_dim l ON i.location_key = l.location_key
WHERE p.product_name = '{product_name}'
    AND l.location_name = '{location_name}'
    AND i.date_key = (SELECT MAX(date_key) FROM gold_inventory_fact);
```

Show me inventory levels by product category.
```sql
SELECT 
    p.category_level_1,
    COUNT(DISTINCT i.product_key) as product_count,
    SUM(i.quantity_on_hand) as total_quantity_on_hand,
    SUM(i.quantity_available) as total_quantity_available,
    SUM(i.inventory_value_cost) as total_inventory_value_cost,
    SUM(i.inventory_value_retail) as total_inventory_value_retail
FROM gold_inventory_fact i
JOIN gold_product_dim p ON i.product_key = p.product_key
WHERE i.date_key = (SELECT MAX(date_key) FROM gold_inventory_fact)
GROUP BY p.category_level_1
ORDER BY total_inventory_value_cost DESC;
```

---

## Stockout Risk & Analysis

**Complexity**: Medium  
**Covers**: FR-003, FR-010

Which products are at risk of stockout?
```sql
SELECT 
    p.product_name,
    l.location_name,
    i.quantity_available,
    i.days_of_supply,
    i.reorder_point,
    i.next_replenishment_date,
    CASE 
        WHEN i.days_of_supply <= 3 OR i.quantity_available <= i.reorder_point THEN 'High Risk'
        WHEN i.days_of_supply <= 7 OR i.quantity_available <= i.reorder_point * 1.5 THEN 'Medium Risk'
        ELSE 'Low Risk'
    END as risk_level
FROM gold_inventory_fact i
JOIN gold_product_dim p ON i.product_key = p.product_key
JOIN gold_location_dim l ON i.location_key = l.location_key
WHERE i.date_key = (SELECT MAX(date_key) FROM gold_inventory_fact)
    AND i.quantity_available > 0
    AND (i.days_of_supply <= 7 OR i.quantity_available <= i.reorder_point * 1.5)
ORDER BY i.days_of_supply ASC;
```

What products have been out of stock for more than 7 days?
```sql
SELECT 
    p.product_name,
    l.location_name,
    i.stockout_duration_days,
    i.last_replenishment_date,
    i.next_replenishment_date,
    DATEDIFF(CURRENT_DATE, i.last_replenishment_date) as days_since_replenishment
FROM gold_inventory_fact i
JOIN gold_product_dim p ON i.product_key = p.product_key
JOIN gold_location_dim l ON i.location_key = l.location_key
WHERE i.is_stockout = TRUE
    AND i.date_key = (SELECT MAX(date_key) FROM gold_inventory_fact)
    AND i.stockout_duration_days > 7
ORDER BY i.stockout_duration_days DESC;
```

What is the stockout risk for top-selling products?
```sql
WITH top_products AS (
    SELECT 
        product_key,
        SUM(quantity_sold) as total_sold
    FROM gold_sales_fact
    WHERE is_return = FALSE
        AND date_key >= DATE_SUB(CURRENT_DATE, 90)
    GROUP BY product_key
    ORDER BY total_sold DESC
    LIMIT 20
)
SELECT 
    p.product_name,
    l.location_name,
    i.quantity_available,
    i.days_of_supply,
    i.reorder_point,
    tp.total_sold,
    CASE 
        WHEN i.days_of_supply <= 3 THEN 'High Risk'
        WHEN i.days_of_supply <= 7 THEN 'Medium Risk'
        ELSE 'Low Risk'
    END as risk_level
FROM gold_inventory_fact i
JOIN top_products tp ON i.product_key = tp.product_key
JOIN gold_product_dim p ON i.product_key = p.product_key
JOIN gold_location_dim l ON i.location_key = l.location_key
WHERE i.date_key = (SELECT MAX(date_key) FROM gold_inventory_fact)
ORDER BY i.days_of_supply ASC;
```

---

## Overstock Identification & Analysis

**Complexity**: Medium  
**Covers**: FR-004

What products are overstocked?
```sql
SELECT 
    p.product_name,
    l.location_name,
    i.quantity_on_hand,
    i.days_of_supply,
    i.is_overstock,
    i.inventory_value_cost,
    i.inventory_value_retail
FROM gold_inventory_fact i
JOIN gold_product_dim p ON i.product_key = p.product_key
JOIN gold_location_dim l ON i.location_key = l.location_key
WHERE i.is_overstock = TRUE
    AND i.date_key = (SELECT MAX(date_key) FROM gold_inventory_fact)
ORDER BY i.inventory_value_cost DESC;
```

Which products have excess inventory based on days of supply?
```sql
SELECT 
    p.product_name,
    l.location_name,
    i.quantity_on_hand,
    i.days_of_supply,
    i.inventory_value_cost,
    CASE 
        WHEN i.days_of_supply > 90 THEN 'Severe Overstock'
        WHEN i.days_of_supply > 60 THEN 'Moderate Overstock'
        ELSE 'Normal'
    END as overstock_level
FROM gold_inventory_fact i
JOIN gold_product_dim p ON i.product_key = p.product_key
JOIN gold_location_dim l ON i.location_key = l.location_key
WHERE i.date_key = (SELECT MAX(date_key) FROM gold_inventory_fact)
    AND i.days_of_supply > 60
ORDER BY i.days_of_supply DESC;
```

---

## Inventory Value & Financial Metrics

**Complexity**: Simple  
**Covers**: FR-005

What is the inventory value by location?
```sql
SELECT 
    l.location_name,
    l.region,
    COUNT(DISTINCT i.product_key) as product_count,
    SUM(i.inventory_value_cost) as total_inventory_value_cost,
    SUM(i.inventory_value_retail) as total_inventory_value_retail,
    SUM(i.inventory_value_retail) - SUM(i.inventory_value_cost) as total_margin_value
FROM gold_inventory_fact i
JOIN gold_location_dim l ON i.location_key = l.location_key
WHERE i.date_key = (SELECT MAX(date_key) FROM gold_inventory_fact)
GROUP BY l.location_name, l.region
ORDER BY total_inventory_value_cost DESC;
```

What is the inventory value by product category?
```sql
SELECT 
    p.category_level_1,
    p.category_level_2,
    COUNT(DISTINCT i.product_key) as product_count,
    SUM(i.inventory_value_cost) as total_inventory_value_cost,
    SUM(i.inventory_value_retail) as total_inventory_value_retail,
    AVG(i.inventory_value_cost) as avg_inventory_value_cost_per_product
FROM gold_inventory_fact i
JOIN gold_product_dim p ON i.product_key = p.product_key
WHERE i.date_key = (SELECT MAX(date_key) FROM gold_inventory_fact)
GROUP BY p.category_level_1, p.category_level_2
ORDER BY total_inventory_value_cost DESC;
```

---

## Days of Supply & Reorder Management

**Complexity**: Simple  
**Covers**: FR-006, FR-007

What are the days of supply for top-selling products?
```sql
WITH top_products AS (
    SELECT 
        product_key,
        SUM(quantity_sold) as total_sold
    FROM gold_sales_fact
    WHERE is_return = FALSE
        AND date_key >= DATE_SUB(CURRENT_DATE, 90)
    GROUP BY product_key
    ORDER BY total_sold DESC
    LIMIT 20
)
SELECT 
    p.product_name,
    l.location_name,
    i.quantity_available,
    i.days_of_supply,
    i.stock_cover_days,
    i.reorder_point,
    i.reorder_quantity,
    CASE 
        WHEN i.days_of_supply <= 3 THEN 'Critical'
        WHEN i.days_of_supply <= 7 THEN 'Low'
        WHEN i.days_of_supply <= 14 THEN 'Adequate'
        ELSE 'High'
    END as supply_status
FROM gold_inventory_fact i
JOIN top_products tp ON i.product_key = tp.product_key
JOIN gold_product_dim p ON i.product_key = p.product_key
JOIN gold_location_dim l ON i.location_key = l.location_key
WHERE i.date_key = (SELECT MAX(date_key) FROM gold_inventory_fact)
ORDER BY i.days_of_supply ASC;
```

Which products need reordering?
```sql
SELECT 
    p.product_name,
    l.location_name,
    i.quantity_available,
    i.reorder_point,
    i.reorder_quantity,
    i.next_replenishment_date,
    i.reorder_point - i.quantity_available as quantity_below_reorder_point,
    CASE 
        WHEN i.next_replenishment_date IS NULL THEN 'No schedule - Urgent'
        WHEN DATEDIFF(i.next_replenishment_date, CURRENT_DATE) > 7 THEN 'Scheduled but delayed'
        ELSE 'Scheduled'
    END as reorder_status
FROM gold_inventory_fact i
JOIN gold_product_dim p ON i.product_key = p.product_key
JOIN gold_location_dim l ON i.location_key = l.location_key
WHERE i.date_key = (SELECT MAX(date_key) FROM gold_inventory_fact)
    AND i.quantity_available <= i.reorder_point
ORDER BY i.quantity_available ASC;
```

---

## Inventory Movements & Replenishment

**Complexity**: Medium  
**Covers**: FR-008, FR-011

How much inventory is in transit?
```sql
SELECT 
    p.product_name,
    l.location_name,
    i.quantity_in_transit,
    i.quantity_available,
    i.next_replenishment_date,
    CASE 
        WHEN i.next_replenishment_date IS NOT NULL 
        THEN DATEDIFF(i.next_replenishment_date, CURRENT_DATE)
        ELSE NULL
    END as days_until_arrival
FROM gold_inventory_fact i
JOIN gold_product_dim p ON i.product_key = p.product_key
JOIN gold_location_dim l ON i.location_key = l.location_key
WHERE i.date_key = (SELECT MAX(date_key) FROM gold_inventory_fact)
    AND i.quantity_in_transit > 0
ORDER BY i.quantity_in_transit DESC;
```

What types of inventory movements occurred last month?
```sql
SELECT 
    im.movement_type,
    COUNT(*) as movement_count,
    SUM(im.quantity_change) as total_quantity_change,
    AVG(CASE WHEN im.is_return_delayed THEN im.return_delay_days ELSE NULL END) as avg_return_delay_days
FROM gold_inventory_movement_fact im
JOIN gold_date_dim d ON im.date_key = d.date_key
WHERE d.calendar_date >= DATE_SUB(CURRENT_DATE, 30)
    AND d.calendar_date < CURRENT_DATE
GROUP BY im.movement_type
ORDER BY movement_count DESC;
```

What was the replenishment activity last month?
```sql
SELECT 
    p.product_name,
    l.location_name,
    d.calendar_date,
    im.quantity_change as replenishment_quantity,
    im.movement_type
FROM gold_inventory_movement_fact im
JOIN gold_product_dim p ON im.product_key = p.product_key
JOIN gold_location_dim l ON im.location_key = l.location_key
JOIN gold_date_dim d ON im.date_key = d.date_key
WHERE im.movement_type = 'RECEIPT'
    AND d.calendar_date >= DATE_SUB(CURRENT_DATE, 30)
    AND d.calendar_date < CURRENT_DATE
ORDER BY d.calendar_date DESC, im.quantity_change DESC;
```

---

## Inventory Turnover & Efficiency

**Complexity**: Complex  
**Covers**: FR-009

What is the inventory turnover rate by category?
```sql
WITH inventory_snapshot AS (
    SELECT 
        product_key,
        location_key,
        AVG(inventory_value_cost) as avg_inventory_value_cost
    FROM gold_inventory_fact
    WHERE date_key >= DATE_SUB(CURRENT_DATE, 90)
    GROUP BY product_key, location_key
),
sales_summary AS (
    SELECT 
        product_key,
        location_key,
        SUM(net_sales_amount) as total_sales_revenue
    FROM gold_sales_fact
    WHERE is_return = FALSE
        AND date_key >= DATE_SUB(CURRENT_DATE, 90)
    GROUP BY product_key, location_key
)
SELECT 
    p.category_level_1,
    COUNT(DISTINCT i.product_key) as product_count,
    SUM(i.avg_inventory_value_cost) as total_avg_inventory_value,
    SUM(s.total_sales_revenue) as total_sales_revenue,
    CASE 
        WHEN SUM(i.avg_inventory_value_cost) > 0 
        THEN SUM(s.total_sales_revenue) / SUM(i.avg_inventory_value_cost)
        ELSE 0
    END as inventory_turnover_rate
FROM inventory_snapshot i
JOIN sales_summary s ON i.product_key = s.product_key AND i.location_key = s.location_key
JOIN gold_product_dim p ON i.product_key = p.product_key
GROUP BY p.category_level_1
ORDER BY inventory_turnover_rate DESC;
```

---

## Stockout Events & Lost Sales Impact

**Complexity**: Medium  
**Covers**: FR-010

Which locations have the highest stockout rates?
```sql
SELECT 
    l.location_name,
    l.region,
    COUNT(DISTINCT se.stockout_id) as stockout_event_count,
    SUM(se.lost_sales_revenue) as total_lost_sales_revenue,
    SUM(se.lost_sales_quantity) as total_lost_sales_quantity,
    AVG(se.stockout_duration_days) as avg_stockout_duration_days,
    COUNT(DISTINCT se.product_key) as unique_products_affected
FROM gold_stockout_events se
JOIN gold_location_dim l ON se.location_key = l.location_key
JOIN gold_date_dim d ON se.stockout_start_date_key = d.date_key
WHERE d.calendar_date >= DATE_SUB(CURRENT_DATE, 90)
GROUP BY l.location_name, l.region
ORDER BY total_lost_sales_revenue DESC;
```

What is the revenue impact of stockouts?
```sql
SELECT 
    p.product_name,
    p.category_level_1,
    COUNT(se.stockout_id) as stockout_count,
    SUM(se.lost_sales_revenue) as total_lost_revenue,
    SUM(se.lost_sales_quantity) as total_lost_quantity,
    AVG(se.stockout_duration_days) as avg_duration_days,
    SUM(CASE WHEN se.peak_season_flag THEN se.lost_sales_revenue ELSE 0 END) as peak_season_lost_revenue
FROM gold_stockout_events se
JOIN gold_product_dim p ON se.product_key = p.product_key
JOIN gold_date_dim d ON se.stockout_start_date_key = d.date_key
WHERE d.calendar_date >= DATE_SUB(CURRENT_DATE, 90)
GROUP BY p.product_name, p.category_level_1
ORDER BY total_lost_revenue DESC
LIMIT 20;
```

---

## Location & Regional Comparisons

**Complexity**: Medium  
**Covers**: FR-012

Compare inventory metrics across locations.
```sql
SELECT 
    l.region,
    l.location_name,
    COUNT(DISTINCT i.product_key) as product_count,
    SUM(i.quantity_available) as total_quantity_available,
    SUM(i.inventory_value_cost) as total_inventory_value_cost,
    SUM(CASE WHEN i.is_stockout THEN 1 ELSE 0 END) as stockout_count,
    SUM(CASE WHEN i.is_overstock THEN 1 ELSE 0 END) as overstock_count
FROM gold_inventory_fact i
JOIN gold_location_dim l ON i.location_key = l.location_key
WHERE i.date_key = (SELECT MAX(date_key) FROM gold_inventory_fact)
GROUP BY l.region, l.location_name
ORDER BY l.region, total_inventory_value_cost DESC;
```

---

## Historical Trends & Patterns

**Complexity**: Complex  
**Covers**: FR-023

How have inventory levels changed over time?
```sql
SELECT 
    d.calendar_date,
    d.month_name,
    d.year,
    COUNT(DISTINCT i.product_key) as product_count,
    SUM(i.quantity_available) as total_quantity_available,
    SUM(i.inventory_value_cost) as total_inventory_value_cost,
    SUM(CASE WHEN i.is_stockout THEN 1 ELSE 0 END) as stockout_count,
    SUM(CASE WHEN i.is_overstock THEN 1 ELSE 0 END) as overstock_count
FROM gold_inventory_fact i
JOIN gold_date_dim d ON i.date_key = d.date_key
WHERE d.calendar_date >= DATE_SUB(CURRENT_DATE, 90)
GROUP BY d.calendar_date, d.month_name, d.year
ORDER BY d.calendar_date;
```

What are the trends in stockout events?
```sql
SELECT 
    d.month_name,
    d.year,
    COUNT(DISTINCT se.stockout_id) as stockout_event_count,
    SUM(se.lost_sales_revenue) as total_lost_revenue,
    AVG(se.stockout_duration_days) as avg_duration_days,
    SUM(CASE WHEN se.peak_season_flag THEN 1 ELSE 0 END) as peak_season_stockouts
FROM gold_stockout_events se
JOIN gold_date_dim d ON se.stockout_start_date_key = d.date_key
WHERE d.calendar_date >= DATE_SUB(CURRENT_DATE, 180)
GROUP BY d.month_name, d.year
ORDER BY d.year, d.month_name;
```

---

## Inventory Health Metrics

**Complexity**: Complex  
**Covers**: FR-024

What is the overall inventory health score?
```sql
WITH inventory_metrics AS (
    SELECT 
        COUNT(DISTINCT i.product_key) as total_products,
        SUM(CASE WHEN i.is_stockout THEN 1 ELSE 0 END) as stockout_count,
        SUM(CASE WHEN i.is_overstock THEN 1 ELSE 0 END) as overstock_count,
        SUM(CASE WHEN i.days_of_supply <= 3 THEN 1 ELSE 0 END) as high_risk_count,
        SUM(CASE WHEN i.days_of_supply > 90 THEN 1 ELSE 0 END) as excess_inventory_count,
        AVG(i.days_of_supply) as avg_days_of_supply,
        SUM(i.inventory_value_cost) as total_inventory_value
    FROM gold_inventory_fact i
    WHERE i.date_key = (SELECT MAX(date_key) FROM gold_inventory_fact)
)
SELECT 
    total_products,
    stockout_count,
    overstock_count,
    high_risk_count,
    excess_inventory_count,
    avg_days_of_supply,
    total_inventory_value,
    CASE 
        WHEN stockout_count / total_products > 0.10 THEN 'Critical'
        WHEN stockout_count / total_products > 0.05 THEN 'Poor'
        WHEN high_risk_count / total_products > 0.15 THEN 'At Risk'
        WHEN excess_inventory_count / total_products > 0.10 THEN 'Excess Inventory'
        ELSE 'Healthy'
    END as inventory_health_status
FROM inventory_metrics;
```

---

## Follow-Up Questions

**Complexity**: Medium  
**Covers**: FR-014

[After asking about stockout risk] What about their replenishment schedule?
```sql
-- Context: Previous query identified products at stockout risk
-- Follow-up: Get replenishment schedule for those products
SELECT 
    p.product_name,
    l.location_name,
    i.quantity_available,
    i.days_of_supply,
    i.reorder_point,
    i.last_replenishment_date,
    i.next_replenishment_date,
    CASE 
        WHEN i.next_replenishment_date IS NOT NULL 
        THEN DATEDIFF(i.next_replenishment_date, CURRENT_DATE)
        ELSE NULL
    END as days_until_replenishment,
    i.reorder_quantity
FROM gold_inventory_fact i
JOIN gold_product_dim p ON i.product_key = p.product_key
JOIN gold_location_dim l ON i.location_key = l.location_key
WHERE i.date_key = (SELECT MAX(date_key) FROM gold_inventory_fact)
    AND (i.days_of_supply <= 7 OR i.quantity_available <= i.reorder_point * 1.5)
ORDER BY i.days_of_supply ASC;
```

---

## Error Handling Scenarios

**Complexity**: Simple  
**Covers**: FR-018, FR-022

[Ambiguous Query] "inventory"
**Expected Response**: Ask clarifying questions:
- "What aspect of inventory would you like to know about? For example:
  - Current stock levels
  - Stockout risk
  - Inventory value
  - Reorder needs
  - Inventory movements"

[Future Date Query] "What will inventory levels be next month?"
**Expected Response**: "Forecasting capabilities are not available. This room focuses on historical and current inventory analysis. Data is available from [start_date] to [end_date]. Would you like to analyze historical trends or current inventory status instead?"

[Non-Existent Location] "What is the inventory at location XYZ?"
**Expected Response**: "The location 'XYZ' doesn't exist in the dataset. Available locations are: [list locations]. Would you like to query inventory for one of these locations?"

[Large Dataset Query] "Analyze every inventory record"
**Expected Response**: "This query would process a very large dataset. To improve performance, please add filters such as:
- Time range (e.g., last 30 days)
- Location filter
- Product category filter
Would you like to modify your query with these filters?"

---

## Multi-Domain Detection Test Queries

**Complexity**: Simple  
**Covers**: FR-021

[Multi-Domain Query] "Which customers are affected by stockouts?"
**Expected Response**: "This query combines inventory analytics with customer behavior data. For multi-domain queries, please use the multi-domain agent. This room focuses exclusively on inventory analytics."

[Multi-Domain Query] "Show me customer behavior for products that are out of stock"
**Expected Response**: "This query combines inventory analytics with customer behavior data. For multi-domain queries, please use the multi-domain agent. This room focuses exclusively on inventory analytics."

---

**Note**: These sample queries demonstrate the patterns Genie should learn. Genie will generate SQL based on natural language queries, and these examples guide the translation process.

