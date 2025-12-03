# Customer Behavior Analytics Metric Views

**Created:** 2025-01-29  
**Catalog/Schema:** `juan_dev.retail`  
**Purpose:** Pre-aggregated KPIs for Customer Behavior Analytics Genie Room

---

## Overview

This directory contains Databricks metric views for customer behavior analytics, optimized for the Customer Behavior Genie room. Metric views provide pre-aggregated KPIs that improve query performance and ensure consistent calculations across the Genie room's question types.

### What are Metric Views?

Metric views are Databricks objects that define:
- **Dimensions**: Attributes for grouping and filtering (e.g., Segment, Channel, Product Category)
- **Measures**: Pre-defined aggregations (e.g., Customer Count, Avg CLTV, Transaction Count)
- **Source Data**: The underlying tables and transformations

Metric views are defined using YAML syntax within SQL DDL and follow the [Databricks metric view specification](https://docs.databricks.com/aws/en/metric-views/create/sql).

---

## Metric Views Inventory

The following 10 metric views are available in `juan_dev.retail`:

1. **`customer_segmentation_mv`** - Customer segment summary metrics
2. **`customer_rfm_analysis_mv`** - RFM metrics with loyalty status
3. **`customer_purchase_summary_mv`** - Purchase behavior by segment and channel
4. **`product_affinity_mv`** - Product affinity scores with segment breakdown
5. **`channel_behavior_mv`** - Channel performance metrics by segment
6. **`channel_migration_mv`** - Channel migration patterns
7. **`engagement_funnel_mv`** - Engagement funnel with conversion rates
8. **`cart_abandonment_mv`** - Cart abandonment with recovery tracking
9. **`personalization_impact_mv`** - Personalization effectiveness
10. **`segment_trends_daily_mv`** - Daily segment trends

> **For detailed information** about each metric view including purpose, source tables, use cases, dimensions, measures, and SQL DDL statements, see the [customer_behavior_metric_views.ipynb](./customer_behavior_metric_views.ipynb) notebook.

---

## Usage

### Creating Metric Views in Databricks

Execute each SQL cell in the notebook in Databricks SQL Editor or via API:

```sql
-- Example: Create the customer segmentation metric view
%sql
-- Run the contents of customer_segmentation_mv from the notebook
```

> **Note:** For query examples and usage patterns, see the [customer_behavior_metric_view_queries.ipynb](./customer_behavior_metric_view_queries.ipynb) notebook.

### Viewing Metric View Definition

```sql
-- View the metric view schema and measures
DESCRIBE TABLE EXTENDED juan_dev.retail.customer_segmentation_mv AS JSON;
```

---

## Sample Queries

For comprehensive query examples demonstrating how to use each metric view, see the [customer_behavior_metric_view_queries.ipynb](./customer_behavior_metric_view_queries.ipynb) notebook. The notebook contains:

- Query examples for all 10 metric views
- Common question patterns and their SQL translations
- Best practices for using the `MEASURE()` function
- Examples of aggregating measures across groups

### Quick Example

```sql
-- Get customer counts and average CLTV by segment
SELECT 
  Segment,
  MEASURE(`Customer Count`) as customer_count,
  MEASURE(`Average Lifetime Value`) as avg_cltv
FROM juan_dev.retail.customer_segmentation_mv
GROUP BY Segment
ORDER BY MEASURE(`Average Lifetime Value`) DESC;
```

---

## Performance Benefits

Metric views provide several performance benefits for the Genie room:

1. **Pre-filtered Data**: Views filter to relevant data (`is_current = TRUE`, `is_return = FALSE`)
2. **Pre-joined Dimensions**: Dimension joins (customer, product, date, channel) are pre-computed
3. **Standardized Calculations**: Loyalty status, affinity levels, rates use consistent logic
4. **Optimized for Common Queries**: Each view is optimized for specific question types

### Expected Performance Improvements

- **Segmentation Queries**: 2-3x faster (pre-filtered to current customers)
- **RFM Analysis**: 3-4x faster (pre-calculated RFM scores and loyalty status)
- **Channel Analysis**: 2-3x faster (pre-aggregated by channel and segment)
- **Funnel Analysis**: 4-5x faster (pre-calculated conversion rates)
- **Abandonment Analysis**: 2-3x faster (pre-aggregated with recovery metrics)

---

## Genie Room Integration

### How Genie Uses Metric Views

The Customer Behavior Analytics Genie room can leverage these metric views for:

1. **Natural Language Queries**: Genie translates user questions to SQL queries against metric views
2. **Consistent Metrics**: Pre-defined measures ensure consistent calculations across queries
3. **Performance**: Pre-aggregated data reduces query execution time
4. **Discovery**: Metric view metadata helps Genie understand available dimensions and measures

### Example Genie Queries Using Metric Views

**User Question:** "Which customers are at risk of churning?"
```sql
-- Genie could use customer_rfm_analysis_mv
SELECT 
  Segment,
  `Loyalty Status`,
  MEASURE(`Customer Count`) as customer_count,
  MEASURE(`Average Recency Days`) as avg_recency
FROM juan_dev.retail.customer_rfm_analysis_mv
WHERE `Loyalty Status` = 'At Risk'
GROUP BY Segment, `Loyalty Status`
ORDER BY MEASURE(`Customer Count`) DESC;
```

**User Question:** "What is the cart abandonment rate by segment?"
```sql
-- Genie could use cart_abandonment_mv
SELECT 
  Segment,
  MEASURE(`Total Carts`) as total_carts,
  MEASURE(`Abandonment Rate`) as abandonment_rate,
  MEASURE(`Lost Revenue`) as lost_revenue
FROM juan_dev.retail.cart_abandonment_mv
GROUP BY Segment
ORDER BY MEASURE(`Lost Revenue`) DESC;
```

---

## Metric Views Detail

### 1. customer_segmentation_mv

**Purpose:** Customer segment summary metrics  
**Source:** `gold_customer_dim` (filtered to is_current = TRUE)

**Dimensions:**
- Segment (VIP, Premium, Loyal, Regular, New)
- Loyalty Tier
- Geo Region
- Acquisition Channel

**Measures:**
- Customer Count
- Average Lifetime Value
- Total Lifetime Value
- Min/Max/Median Lifetime Value

**Use Cases:**
- "What are the key customer segments?"
- "What is the average lifetime value by segment?"
- "Show me customer distribution by region"

---

### 2. customer_rfm_analysis_mv

**Purpose:** RFM metrics with loyalty status classification  
**Source:** `gold_sales_fact` + `gold_customer_dim` + `gold_date_dim`

**Dimensions:**
- Segment
- Loyalty Status (Champion, Loyal, At Risk, Regular)

**Measures:**
- Customer Count
- Average Recency Days
- Average Frequency
- Average Monetary Value
- Total Monetary Value
- Champions Count
- At Risk Count

**Use Cases:**
- "Which customers are at risk of churning?"
- "Show me customers with low recency, high frequency"
- "Analyze RFM patterns by segment"

---

### 3. customer_purchase_summary_mv

**Purpose:** Purchase behavior by segment and channel  
**Source:** `gold_sales_fact` + `gold_customer_dim` + `gold_channel_dim` + `gold_date_dim`

**Dimensions:**
- Segment
- Channel Name
- Month Name, Year
- Calendar Date

**Measures:**
- Transaction Count
- Total Revenue
- Average Order Value
- Unique Customers
- Transactions Per Customer

**Use Cases:**
- "What is average order value by segment?"
- "Show me purchase frequency by channel"
- "What is total revenue by segment over time?"

---

### 4. product_affinity_mv

**Purpose:** Product affinity with CLTV impact  
**Source:** `gold_customer_product_affinity_agg` + `gold_product_dim` + `gold_customer_dim`

**Dimensions:**
- Segment
- Product Category Level 1 & 2
- Affinity Level (High >=0.7, Medium >=0.4, Low <0.4)

**Measures:**
- Customer Count
- Product Count
- Average Affinity Score
- Total Purchases
- Average/Total Predicted CLTV Impact
- High Affinity Customer Count

**Use Cases:**
- "Show me products with high affinity scores"
- "How does category affinity differ by segment?"
- "What products have highest affinity for VIP customers?"

---

### 5. channel_behavior_mv

**Purpose:** Channel performance by segment  
**Source:** `gold_sales_fact` + `gold_channel_dim` + `gold_customer_dim`

**Dimensions:**
- Channel Name
- Segment
- Is Digital (Digital / Physical)

**Measures:**
- Unique Customers
- Transaction Count
- Total Revenue
- Average Order Value
- Transactions Per Customer

**Use Cases:**
- "Through which channels do customers prefer to shop?"
- "What is impact of channel on purchase frequency?"
- "Show me channel performance by segment"

---

### 6. channel_migration_mv

**Purpose:** Channel migration patterns  
**Source:** `gold_customer_dim` (filtered to is_current = TRUE)

**Dimensions:**
- Acquisition Channel
- Preferred Channel
- Segment
- Migration Status (Same Channel / Migrated)

**Measures:**
- Customer Count
- Average CLTV
- Total CLTV
- Migration Rate

**Use Cases:**
- "How do customers migrate between channels?"
- "What percentage acquired in-store now prefer online?"
- "Show me channel migration by segment"

---

### 7. engagement_funnel_mv

**Purpose:** Engagement funnel with conversion rates  
**Source:** `gold_customer_event_fact` + `gold_sales_fact` + `gold_customer_dim`

**Dimensions:**
- Segment
- Channel Name
- Month Name, Year

**Measures:**
- Total Sessions
- Views, Add to Cart, Purchases
- Cart Conversion Rate
- Purchase Conversion Rate
- Overall Conversion Rate

**Use Cases:**
- "What are conversion rates at each funnel stage?"
- "Which channels drive most engagement?"
- "Where are customers dropping off?"

---

### 8. cart_abandonment_mv

**Purpose:** Cart abandonment with recovery tracking  
**Source:** `gold_cart_abandonment_fact` + `gold_customer_dim`

**Dimensions:**
- Segment
- Abandonment Stage (cart, shipping, payment)
- Recovery Status (Recovered, Email Sent, No Attempt)

**Measures:**
- Total Carts
- Abandoned Carts
- Recovered Carts
- Abandonment Rate
- Recovery Rate
- Lost Revenue
- Recovered Revenue
- Average Cart Value
- Average Items Per Cart

**Use Cases:**
- "What is the rate of cart abandonment?"
- "Which stages have highest abandonment rates?"
- "How effective are recovery campaigns?"

---

### 9. personalization_impact_mv

**Purpose:** Personalization effectiveness  
**Source:** `gold_customer_product_affinity_agg` + `gold_customer_dim`

**Dimensions:**
- Segment
- Affinity Level (High, Medium, Low)

**Measures:**
- Customers with Affinity
- Average Affinity Score
- Total Purchases from Affinity
- Average Purchases per Customer
- Average/Total Predicted CLTV Impact
- Current Average CLTV
- High Affinity Customer Count

**Use Cases:**
- "Which segments respond best to personalization?"
- "How effective are personalized recommendations?"
- "What is predicted CLTV impact?"

---

### 10. segment_trends_daily_mv

**Purpose:** Daily segment trends  
**Source:** `gold_sales_fact` + `gold_customer_dim` + `gold_date_dim`

**Dimensions:**
- Calendar Date
- Month Name, Year, Quarter
- Season
- Peak Season Indicator
- Segment

**Measures:**
- Transaction Count
- Total Revenue
- Unique Customers
- Average Order Value
- Revenue Per Customer

**Use Cases:**
- "How have sales by segment changed over time?"
- "Show me monthly revenue trends by segment"
- "What are seasonal purchase patterns?"

---

## Maintenance

### Refreshing Metric Views

Metric views automatically reflect the latest data from underlying tables. No manual refresh is needed.

### Updating Metric View Definitions

To update a metric view:

1. Edit the corresponding SQL in the notebook
2. Re-run the `CREATE OR REPLACE VIEW` statement in Databricks
3. Verify the updated definition with `DESCRIBE TABLE EXTENDED`

### Monitoring Performance

Monitor metric view query performance:

```sql
-- Check query history for metric view usage
SELECT 
  statement_text,
  execution_duration_ms,
  produced_rows
FROM system.query.history
WHERE statement_text LIKE '%customer_%mv%'
  AND start_time >= CURRENT_DATE - INTERVAL 7 DAYS
ORDER BY execution_duration_ms DESC
LIMIT 20;
```

---

## Design Principles

These metric views follow key design principles:

1. **Aligned with Sample Queries**: Each view optimizes for specific question patterns from sample_queries.md
2. **Pre-filtering**: Views filter to relevant data (`is_current = TRUE`, `is_return = FALSE`)
3. **Pre-joining**: Dimension joins are pre-computed for performance
4. **Standardized Calculations**: Loyalty status, affinity levels, rates use consistent logic
5. **Comprehensive Comments**: All dimensions and measures include descriptive comments
6. **Performance-focused**: Design prioritizes query speed for Genie room usage

---

## Dependencies

### Required Tables

- `juan_dev.retail.gold_customer_dim`
- `juan_dev.retail.gold_sales_fact`
- `juan_dev.retail.gold_cart_abandonment_fact`
- `juan_dev.retail.gold_customer_product_affinity_agg`
- `juan_dev.retail.gold_customer_event_fact`
- `juan_dev.retail.gold_product_dim`
- `juan_dev.retail.gold_channel_dim`
- `juan_dev.retail.gold_date_dim`

### Required Permissions

To create metric views:
- `USE CATALOG` on `juan_dev` catalog
- `USE SCHEMA` on `retail` schema
- `CREATE TABLE` (metric views use table permissions) on `retail` schema
- `SELECT` on all source tables

To query metric views:
- `SELECT` on metric views
- `USE CATALOG` and `USE SCHEMA` on parent catalog/schema

---

## References

- [Databricks Metric Views Documentation](https://docs.databricks.com/aws/en/metric-views/create/sql)
- [Customer Behavior Genie Instructions](../instructions.md)
- [Customer Behavior Data Model](../data_model.md)
- [Customer Behavior Sample Queries](../sample_queries.md)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-29 | Initial creation of 10 customer behavior metric views |

---

## Support

For questions or issues with metric views:
1. Check the [Databricks Metric Views Documentation](https://docs.databricks.com/aws/en/metric-views/create/sql)
2. Review the source SQL in the notebook for metric view definitions
3. Verify underlying table schemas and data quality
4. Test queries against metric views with sample data

---

**Note:** These metric views are designed specifically for the Customer Behavior Analytics Genie room and may require updates if the underlying data model changes or new question types are added to the Genie room.

