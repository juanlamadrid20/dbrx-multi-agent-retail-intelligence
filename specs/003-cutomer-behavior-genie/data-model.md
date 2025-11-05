# Data Model: Customer Behavior Data for Genie

**Feature**: 003-cutomer-behavior-genie
**Date**: 2025-11-04
**Purpose**: Documentation for Genie space configuration - describes customer behavior tables, relationships, and metrics that Genie needs to understand

## Overview

This document describes the customer behavior data model accessible to the Customer Behavior Genie space. The Genie space queries these tables to answer questions about customer purchasing patterns, segmentation, cart abandonment, product affinity, channel behavior, and engagement metrics.

**Data Model Type**: Star Schema (dimension and fact tables)
**Primary Catalog/Schema**: Unity Catalog managed tables (specific catalog/schema depends on deployment)
**Data Volume**: Medium-scale (1-10 million rows per table, occasional multi-table joins)
**Temporal Coverage**: Historical data plus future dates (for forecasting)

---

## Core Dimension Tables

### gold_customer_dim
**Purpose**: Customer master data with segmentation and lifetime value metrics

**Key Columns**:
- `customer_key` (INT): Primary key, surrogate key
- `customer_id` (STRING): Business key, unique identifier
- `segment` (STRING): Customer segment (VIP, Premium, Loyal, Regular, New)
- `lifetime_value` (DOUBLE): Customer lifetime value (CLTV)
- `acquisition_date` (DATE): When customer was acquired
- `acquisition_channel` (STRING): Channel where customer was acquired
- `preferred_channel` (STRING): Customer's preferred shopping channel
- `preferred_category` (STRING): Customer's preferred product category
- `loyalty_tier` (STRING): Loyalty program tier
- `geo_region` (STRING): Geographic region
- `is_current` (BOOLEAN): Current record flag (SCD Type 2)

**Key Metrics**:
- Lifetime Value (CLTV): Sum of all historical purchases
- Average Order Value: Can be calculated from sales_fact
- Purchase Frequency: Can be calculated from sales_fact

**Relationships**:
- Links to `gold_sales_fact` via `customer_key`
- Links to `gold_cart_abandonment_fact` via `customer_key`
- Links to `gold_customer_product_affinity_agg` via `customer_key`

---

### gold_product_dim
**Purpose**: Product master data with categorization and pricing

**Key Columns**:
- `product_key` (INT): Primary key
- `product_id` (STRING): Business key
- `product_name` (STRING): Product name
- `brand` (STRING): Brand name
- `category_level_1` (STRING): Top-level category (e.g., "Apparel")
- `category_level_2` (STRING): Second-level category (e.g., "Women's")
- `category_level_3` (STRING): Third-level category (e.g., "Tops")
- `base_price` (DOUBLE): Base retail price
- `season_code` (STRING): Season (Spring, Summer, Fall, Winter)
- `is_active` (BOOLEAN): Active product flag

**Relationships**:
- Links to `gold_sales_fact` via `product_key`
- Links to `gold_cart_abandonment_fact` via `product_key` (in cart items)
- Links to `gold_customer_product_affinity_agg` via `product_key`

---

### gold_date_dim
**Purpose**: Date dimension with calendar and fiscal attributes

**Key Columns**:
- `date_key` (INT): Primary key (YYYYMMDD format)
- `calendar_date` (DATE): Actual date
- `year`, `quarter`, `month`, `day_of_month` (INT): Calendar components
- `day_name` (STRING): Day of week name
- `month_name` (STRING): Month name
- `is_weekend` (BOOLEAN): Weekend flag
- `is_holiday` (BOOLEAN): Holiday flag
- `season` (STRING): Season (Spring, Summer, Fall, Winter)
- `is_peak_season` (BOOLEAN): Peak shopping season flag
- `is_sale_period` (BOOLEAN): Sale period flag

**Important Note**: This table includes dates from historical days ago through **+365 days in the future** to support forecasting. Queries should filter by `calendar_date` to ensure correct temporal ranges.

**Relationships**:
- Links to all fact tables via `date_key`

---

### gold_channel_dim
**Purpose**: Sales channel definitions

**Key Columns**:
- `channel_key` (INT): Primary key
- `channel_name` (STRING): Channel name (e.g., "Online", "In-Store", "Mobile App")
- `channel_type` (STRING): Channel type

**Relationships**:
- Links to `gold_sales_fact` via `channel_key`
- Links to `gold_cart_abandonment_fact` via `channel_key`

---

## Core Fact Tables

### gold_sales_fact
**Purpose**: Customer purchase transactions - the primary source for customer behavior analysis

**Key Columns**:
- `transaction_id` (STRING): Unique transaction identifier
- `line_item_id` (STRING): Unique line item within transaction
- `customer_key` (INT): FK to customer_dim
- `product_key` (INT): FK to product_dim
- `date_key` (INT): FK to date_dim (transaction date)
- `channel_key` (INT): FK to channel_dim
- `location_key` (INT): FK to location_dim
- `quantity_sold` (INT): Quantity purchased
- `unit_price` (DOUBLE): Price per unit
- `discount_amount` (DOUBLE): Discount applied
- `net_sales_amount` (DOUBLE): Total after discount (net sales amount)
- `gross_margin_amount` (DOUBLE): Gross margin
- `is_return` (BOOLEAN): Return transaction flag
- `is_promotional` (BOOLEAN): Promotional sale flag

**Key Metrics Calculated from This Table**:
- **Total Sales Revenue**: `SUM(net_sales_amount)`
- **Average Order Value**: `AVG(net_sales_amount)` per transaction
- **Purchase Frequency**: `COUNT(DISTINCT transaction_id)` per customer per time period
- **Recency**: Days since last purchase (current_date - MAX(date_key))
- **Monetary Value**: `SUM(net_sales_amount)` per customer (RFM M score)

**Common Join Patterns**:
- Join with `gold_customer_dim` for customer segmentation analysis
- Join with `gold_product_dim` for product trend analysis
- Join with `gold_date_dim` for time-based analysis
- Join with `gold_channel_dim` for channel behavior analysis

---

### gold_cart_abandonment_fact
**Purpose**: Cart abandonment events - tracks when customers add items to cart but don't purchase

**Key Columns**:
- `abandonment_id` (INT): Primary key
- `cart_id` (STRING): Unique cart identifier
- `customer_key` (INT): FK to customer_dim
- `date_key` (INT): FK to date_dim
- `channel_key` (INT): FK to channel_dim (digital channels only)
- `cart_value` (DOUBLE): Total value of abandoned cart
- `items_count` (INT): Number of items in cart
- `minutes_in_cart` (INT): Time spent in cart before abandonment
- `abandonment_stage` (STRING): Stage where abandonment occurred ('cart', 'shipping', 'payment')
- `suspected_reason` (STRING): Suspected reason for abandonment
- `low_inventory_trigger` (BOOLEAN): TRUE if any item had low/zero inventory
- `recovery_email_sent` (BOOLEAN): Whether recovery email was sent
- `recovery_converted` (BOOLEAN): Whether recovery was successful

**Key Metrics Calculated from This Table**:
- **Cart Abandonment Rate**: `COUNT(*) WHERE recovery_converted = FALSE / COUNT(*)`
- **Abandonment Rate by Product**: `COUNT(*)` grouped by product
- **Abandonment Rate by Stage**: `COUNT(*)` grouped by `abandonment_stage`
- **Recovery Rate**: `COUNT(*) WHERE recovery_converted = TRUE / COUNT(*) WHERE recovery_email_sent = TRUE`
- **Lost Revenue**: `SUM(cart_value)` for abandoned carts

**Common Join Patterns**:
- Join with `gold_customer_dim` for customer segment abandonment analysis
- Join with `gold_product_dim` for product abandonment analysis
- Join with `gold_date_dim` for time-based abandonment trends

---

### gold_customer_product_affinity_agg
**Purpose**: Pre-aggregated customer-product affinity scores and basket analysis data

**Key Columns**:
- `customer_key` (INT): FK to customer_dim
- `product_key` (INT): FK to product_dim
- `affinity_score` (DOUBLE): Affinity score (0.0-1.0)
- `purchase_count` (INT): Number of times customer purchased this product
- `last_purchase_date_key` (INT): Date of last purchase
- `predicted_cltv_impact` (DOUBLE): Predicted CLTV impact from this affinity

**Key Metrics Calculated from This Table**:
- **Product Affinity**: `affinity_score` directly available
- **Basket Analysis**: Products frequently purchased together (via join patterns)
- **Personalization Recommendations**: Products with high `affinity_score`

**Common Join Patterns**:
- Join with `gold_customer_dim` for segment-based affinity
- Join with `gold_product_dim` for product category affinity
- Self-join for basket analysis (products purchased together)

---

### gold_customer_event_fact
**Purpose**: Customer engagement events (views, clicks, add-to-cart, etc.)

**Key Columns**:
- `event_id` (BIGINT): Primary key
- `customer_key` (INT): FK to customer_dim
- `product_key` (INT): FK to product_dim (optional)
- `date_key` (INT): FK to date_dim
- `channel_key` (INT): FK to channel_dim
- `event_type` (STRING): Event type ('view', 'click', 'add_to_cart', 'wishlist', etc.)
- `session_id` (STRING): Session identifier

**Key Metrics Calculated from This Table**:
- **Engagement Funnel**: 
  - Views: `COUNT(*) WHERE event_type = 'view'`
  - Add to Cart: `COUNT(*) WHERE event_type = 'add_to_cart'`
  - Purchases: Join with sales_fact
- **Conversion Rates**: Calculate conversion at each funnel stage
- **Engagement by Channel**: `COUNT(*)` grouped by channel

**Common Join Patterns**:
- Join with `gold_customer_dim` for customer engagement analysis
- Join with `gold_sales_fact` for funnel conversion analysis
- Join with `gold_channel_dim` for channel engagement analysis

---

## Table Relationships and Join Patterns

### Star Schema Structure
```
gold_customer_dim (center)
    ↓
    ├─→ gold_sales_fact
    ├─→ gold_cart_abandonment_fact
    ├─→ gold_customer_product_affinity_agg
    └─→ gold_customer_event_fact

gold_product_dim (center)
    ↓
    ├─→ gold_sales_fact
    ├─→ gold_cart_abandonment_fact (via cart items)
    └─→ gold_customer_product_affinity_agg

gold_date_dim (center)
    ↓
    ├─→ gold_sales_fact
    ├─→ gold_cart_abandonment_fact
    └─→ gold_customer_event_fact

gold_channel_dim (center)
    ↓
    ├─→ gold_sales_fact
    └─→ gold_cart_abandonment_fact
```

### Common Join Patterns for Customer Behavior Analysis

**Customer Segmentation Analysis**:
```sql
SELECT 
    c.segment,
    c.loyalty_tier,
    COUNT(DISTINCT s.transaction_id) as purchase_count,
    SUM(s.net_sales_amount) as total_revenue,
    AVG(s.net_sales_amount) as avg_order_value
FROM gold_customer_dim c
JOIN gold_sales_fact s ON c.customer_key = s.customer_key
JOIN gold_date_dim d ON s.date_key = d.date_key
WHERE d.calendar_date >= DATE_SUB(CURRENT_DATE, 90)
GROUP BY c.segment, c.loyalty_tier
```

**RFM Analysis**:
```sql
WITH customer_metrics AS (
    SELECT 
        c.customer_key,
        MAX(d.calendar_date) as last_purchase_date,
        COUNT(DISTINCT s.transaction_id) as frequency,
        SUM(s.net_sales_amount) as monetary_value
    FROM gold_customer_dim c
    JOIN gold_sales_fact s ON c.customer_key = s.customer_key
    JOIN gold_date_dim d ON s.date_key = d.date_key
    GROUP BY c.customer_key
)
SELECT 
    customer_key,
    DATEDIFF(CURRENT_DATE, last_purchase_date) as recency,
    frequency,
    monetary_value
FROM customer_metrics
```

**Cart Abandonment Analysis**:
```sql
SELECT 
    p.category_level_2,
    COUNT(*) as abandonment_count,
    SUM(ca.cart_value) as lost_revenue,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as abandonment_rate_pct
FROM gold_cart_abandonment_fact ca
JOIN gold_customer_dim c ON ca.customer_key = c.customer_key
JOIN gold_date_dim d ON ca.date_key = d.date_key
WHERE ca.recovery_converted = FALSE
  AND d.calendar_date >= DATE_SUB(CURRENT_DATE, 30)
GROUP BY p.category_level_2
```

**Basket Analysis**:
```sql
WITH basket_pairs AS (
    SELECT 
        s1.product_key as product_a,
        s2.product_key as product_b,
        COUNT(*) as purchase_together_count
    FROM gold_sales_fact s1
    JOIN gold_sales_fact s2 
        ON s1.transaction_id = s2.transaction_id
        AND s1.product_key < s2.product_key
    GROUP BY s1.product_key, s2.product_key
)
SELECT 
    p1.product_name as product_a_name,
    p2.product_name as product_b_name,
    purchase_together_count
FROM basket_pairs bp
JOIN gold_product_dim p1 ON bp.product_a = p1.product_key
JOIN gold_product_dim p2 ON bp.product_b = p2.product_key
ORDER BY purchase_together_count DESC
LIMIT 20
```

---

## Key Metrics and Calculations

### Customer Lifetime Value (CLTV)
**Definition**: Total value of all purchases made by a customer over their lifetime

**Calculation**:
- Simple: `SUM(net_sales_amount)` from `gold_sales_fact` grouped by `customer_key`
- Advanced: Can include predicted future value from `gold_customer_product_affinity_agg.predicted_cltv_impact`

**Available**: Pre-calculated in `gold_customer_dim.lifetime_value`, or can be calculated from sales_fact

### Cart Abandonment Rate
**Definition**: Percentage of carts that are abandoned (not converted to purchase)

**Calculation**:
```sql
SELECT 
    COUNT(*) FILTER (WHERE recovery_converted = FALSE) * 100.0 / COUNT(*) as abandonment_rate
FROM gold_cart_abandonment_fact
WHERE date_key >= [start_date] AND date_key <= [end_date]
```

**Available**: Can be calculated from `gold_cart_abandonment_fact`

### RFM Scores
**Definition**: Recency, Frequency, Monetary value scores for customer segmentation

**Recency (R)**: Days since last purchase
- Calculation: `DATEDIFF(CURRENT_DATE, MAX(date_key))` from `gold_sales_fact`

**Frequency (F)**: Number of purchases in time period
- Calculation: `COUNT(DISTINCT transaction_id)` from `gold_sales_fact`

**Monetary (M)**: Total revenue from customer
- Calculation: `SUM(net_sales_amount)` from `gold_sales_fact`

**Available**: Can be calculated from `gold_sales_fact` and `gold_date_dim`

### Average Order Value (AOV)
**Definition**: Average value of a purchase transaction

**Calculation**:
```sql
SELECT AVG(net_sales_amount) as avg_order_value
FROM gold_sales_fact
WHERE date_key >= [start_date] AND date_key <= [end_date]
```

**Available**: Can be calculated from `gold_sales_fact`

### Conversion Rate (Funnel Analysis)
**Definition**: Percentage of users converting from one stage to the next

**Stages**: View → Add to Cart → Purchase

**Calculation**:
- Views: `COUNT(*) WHERE event_type = 'view'` from `gold_customer_event_fact`
- Add to Cart: `COUNT(*) WHERE event_type = 'add_to_cart'` from `gold_customer_event_fact`
- Purchases: `COUNT(DISTINCT transaction_id)` from `gold_sales_fact`
- Conversion Rate: `(Purchases / Views) * 100`

**Available**: Can be calculated from `gold_customer_event_fact` and `gold_sales_fact`

---

## Data Quality Notes

### Temporal Constraints
- **Date Range**: `gold_date_dim` includes historical dates and future dates (+365 days)
- **Query Filtering**: Always filter by `calendar_date` when querying time periods
- **SCD Type 2**: `gold_customer_dim` uses SCD Type 2 - always filter by `is_current = TRUE` for current customer data

### Data Completeness
- **Cart Abandonment**: Only available for digital channels (check `channel_key`)
- **Customer Events**: May not have complete event tracking for all customers
- **Product Affinity**: Pre-aggregated data, may not include all customer-product combinations

### Known Constraints
- **Medium-Scale Data**: Tables contain 1-10 million rows
- **Join Performance**: Multi-table joins should include appropriate filters (date ranges, segments)
- **Time Periods**: Use `calendar_date` from `gold_date_dim` for accurate time filtering

---

## Best Practices for Genie Queries

1. **Always Filter by Date Range**: Use `gold_date_dim.calendar_date` with appropriate date ranges
2. **Use Current Customer Data**: Filter `gold_customer_dim` by `is_current = TRUE`
3. **Optimize Joins**: Start with fact tables, join to dimensions as needed
4. **Limit Result Sets**: For large analyses, use `LIMIT` or appropriate aggregations
5. **Use Pre-Aggregated Data**: Leverage `gold_customer_product_affinity_agg` when available
6. **Channel-Specific Analysis**: Check `channel_key` for channel-specific queries (cart abandonment is digital-only)

---

## References

- **Full Schema Documentation**: `00-data/README.md`
- **Inventory Alignment Details**: `specs/001-i-want-to/data-model.md`
- **Genie Space Configuration**: `10-genie-rooms/genie-configs/customer-behavior/`
