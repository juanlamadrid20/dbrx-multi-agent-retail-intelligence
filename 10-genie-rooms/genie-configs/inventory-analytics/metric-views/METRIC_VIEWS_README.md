# Inventory Analytics Metric Views

**Created:** 2025-01-27  
**Catalog/Schema:** `juan_dev.retail`  
**Purpose:** Pre-aggregated KPIs for Inventory Analytics Genie Room

---

## Overview

This directory contains Databricks metric views for inventory analytics, optimized for the Inventory Analytics Genie room. Metric views provide pre-aggregated KPIs that improve query performance and ensure consistent calculations across the Genie room's 11 question types.

### What are Metric Views?

Metric views are Databricks objects that define:
- **Dimensions**: Attributes for grouping and filtering (e.g., Location, Product Category, Date)
- **Measures**: Pre-defined aggregations (e.g., Total Quantity, Average Days of Supply, Stockout Count)
- **Source Data**: The underlying tables and transformations

Metric views are defined using YAML syntax within SQL DDL and follow the [Databricks metric view specification](https://docs.databricks.com/aws/en/metric-views/create/sql).

---

## Metric Views Inventory

The following 10 metric views are available in `juan_dev.retail`:

1. **`inventory_current_status_mv`** - Current inventory status metrics (Question Type 1)
2. **`inventory_stockout_risk_mv`** - Stockout risk analysis with standardized risk levels (Question Type 2)
3. **`inventory_overstock_analysis_mv`** - Overstock identification with severity levels (Question Type 3)
4. **`inventory_value_summary_mv`** - Inventory value metrics by location and category (Question Type 4)
5. **`inventory_reorder_management_mv`** - Reorder needs and replenishment status (Question Type 5)
6. **`inventory_movement_summary_mv`** - Inventory movement transactions by type (Question Type 6)
7. **`inventory_stockout_impact_mv`** - Stockout events with lost sales impact (Question Type 7)
8. **`inventory_location_comparison_mv`** - Cross-location inventory metrics comparison (Question Type 8)
9. **`inventory_trends_daily_mv`** - Daily inventory trends over time (Question Type 9)
10. **`inventory_health_score_mv`** - Overall inventory health metrics with health status (Question Type 10)

> **For detailed information** about each metric view including purpose, source tables, use cases, dimensions, measures, and SQL DDL statements, see the [inventory_metric_views.ipynb](./inventory_metric_views.ipynb) notebook.

---

## Usage

### Creating Metric Views in Databricks

Execute each SQL file in Databricks SQL Editor or via API:

```sql
-- Example: Create the current status metric view
%sql
-- Run the contents of inventory_current_status_mv.sql
```

> **Note:** For query examples and usage patterns, see the [inventory_metric_view_queries.ipynb](./inventory_metric_view_queries.ipynb) notebook.

### Viewing Metric View Definition

```sql
-- View the metric view schema and measures
DESCRIBE TABLE EXTENDED juan_dev.retail.inventory_current_status_mv AS JSON;
```

---

## Sample Queries

For comprehensive query examples demonstrating how to use each metric view, see the [inventory_metric_view_queries.ipynb](./inventory_metric_view_queries.ipynb) notebook. The notebook contains:

- Query examples for all 10 metric views
- Common question patterns and their SQL translations
- Best practices for using the `MEASURE()` function
- Examples of aggregating measures across groups

---

## Performance Benefits

Metric views provide several performance benefits for the Genie room:

1. **Pre-filtered Data**: Views like `inventory_current_status_mv` pre-filter to the latest date, eliminating expensive date aggregations
2. **Pre-joined Dimensions**: Dimension joins (product, location) are pre-computed, reducing join overhead
3. **Standardized Calculations**: Risk levels, health scores, and rates are pre-calculated with consistent logic
4. **Optimized for Common Queries**: Each view is optimized for specific question types that the Genie room handles frequently

### Expected Performance Improvements

- **Current Status Queries**: 3-5x faster (pre-filtered to latest date)
- **Risk Analysis Queries**: 2-3x faster (pre-calculated risk levels)
- **Location Comparisons**: 2-4x faster (pre-aggregated by location)
- **Health Score Queries**: 4-6x faster (complex calculations pre-computed)

---

## Genie Room Integration

### How Genie Uses Metric Views

The Inventory Analytics Genie room can leverage these metric views for:

1. **Natural Language Queries**: Genie translates user questions to SQL queries against metric views
2. **Consistent Metrics**: Pre-defined measures ensure consistent calculations across queries
3. **Performance**: Pre-aggregated data reduces query execution time
4. **Discovery**: Metric view metadata helps Genie understand available dimensions and measures

### Example Genie Queries Using Metric Views

**User Question:** "Show me products at high stockout risk"
```sql
-- Genie could use inventory_stockout_risk_mv
SELECT 
  `Location Name`,
  `Product Category`,
  MEASURE(`Products at Risk Count`) as `Products at Risk Count`,
  MEASURE(`Average Days of Supply`) as `Average Days of Supply`
FROM juan_dev.retail.inventory_stockout_risk_mv
WHERE `Risk Level` = 'High Risk'
GROUP BY `Location Name`, `Product Category`;
```

**User Question:** "What is the inventory health by location?"
```sql
-- Genie could use inventory_health_score_mv
SELECT 
  `Location Name`,
  `Health Status`,
  MEASURE(`Health Score`) as `Health Score`,
  MEASURE(`Stockout Rate`) as `Stockout Rate`,
  MEASURE(`Overstock Rate`) as `Overstock Rate`
FROM juan_dev.retail.inventory_health_score_mv
GROUP BY `Location Name`, `Health Status`
ORDER BY MEASURE(`Health Score`) ASC;
```

---

## Maintenance

### Refreshing Metric Views

Metric views automatically reflect the latest data from underlying tables. No manual refresh is needed.

### Updating Metric View Definitions

To update a metric view:

1. Edit the corresponding SQL file
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
WHERE statement_text LIKE '%inventory_%_mv%'
  AND start_time >= CURRENT_DATE - INTERVAL 7 DAYS
ORDER BY execution_duration_ms DESC
LIMIT 20;
```

---

## Design Principles

These metric views follow key design principles:

1. **Aligned with Genie Question Types**: Each view optimizes for specific question patterns
2. **Pre-filtering**: Views filter to relevant data (latest date, active products, etc.)
3. **Pre-joining**: Dimension joins are pre-computed
4. **Standardized Calculations**: Risk levels, health status, rates use consistent logic
5. **Comprehensive Comments**: All dimensions and measures include descriptive comments
6. **Performance-focused**: Design prioritizes query speed for Genie room usage

---

## Dependencies

### Required Tables

- `juan_dev.retail.gold_inventory_fact`
- `juan_dev.retail.gold_stockout_events`
- `juan_dev.retail.gold_inventory_movement_fact`
- `juan_dev.retail.gold_product_dim`
- `juan_dev.retail.gold_location_dim`
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
- [Implementation Summary](./METRIC_VIEWS_IMPLEMENTATION_SUMMARY.md) - Project completion report
- [Inventory Analytics Genie Room Review](../INVENTORY_GENIE_ROOM_REVIEW.md)
- [Inventory Analytics Data Model](../data-model.md)
- [Inventory Analytics Sample Queries](../sample-queries/inventory_analytics_sample_queries.ipynb)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-27 | Initial creation of 10 inventory metric views |

---

## Support

For questions or issues with metric views:
1. Check the [Databricks Metric Views Documentation](https://docs.databricks.com/aws/en/metric-views/create/sql)
2. Review the source SQL files for metric view definitions
3. Verify underlying table schemas and data quality
4. Test queries against metric views with sample data

---

**Note:** These metric views are designed specifically for the Inventory Analytics Genie room and may require updates if the underlying data model changes or new question types are added to the Genie room.

