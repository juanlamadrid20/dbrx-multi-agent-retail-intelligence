# Inventory Analytics Genie

The Inventory Analytics Genie space provides natural language querying of inventory data, enabling analysts to understand inventory levels, stockout risks, overstock situations, replenishment needs, inventory movements, and inventory value across locations.

---

## Quick Start

Follow the [Quickstart Guide](./quickstart.md) to set up and configure your Genie space.

---

## Configuration Artifacts

All configuration artifacts are in this folder:

| File | Description |
|------|-------------|
| [quickstart.md](./quickstart.md) | Step-by-step guide to set up the Genie space |
| [instructions.md](./instructions.md) | Genie space instructions covering business context, key terms, analysis patterns, and response guidelines |
| [data_model.md](./data_model.md) | Data model documentation describing tables, relationships, key metrics, and best practices |
| [sample-queries/sample_queries.ipynb](./sample-queries/sample_queries.ipynb) | Sample queries organized by analytical category |
| [add_table_comments.sql](./add_table_comments.sql) | SQL to add table and column comments for better Genie understanding |
| [metric-views/](./metric-views/) | Metric views for performance optimization |

---

## Prerequisites

Before setting up the Genie space:

1. **Databricks Workspace Access**: Admin or owner permissions to create Genie spaces
2. **Data Tables Deployed**: The following tables must exist in your catalog/schema:
   - `gold_inventory_fact`
   - `gold_stockout_events`
   - `gold_inventory_movement_fact`
   - `gold_product_dim`
   - `gold_location_dim`
   - `gold_date_dim`

---

## Inventory Analytics

An inventory analyst would ask questions that help uncover patterns, trends, and actionable insights about inventory levels, stock health, and supply chain operations.

### Example Questions

- What products are currently out of stock?
- Which products are at risk of stockout?
- What is the inventory value by location?

---

## Analytical Categories

### Current Stock Status & Levels

- What products are currently out of stock?
- What is the current inventory level for product X at location Y?
- Show me inventory levels by product category
- What is the total inventory value by location?

### Stockout Risk & Analysis

- Which products are at risk of stockout?
- What products have been out of stock for more than 7 days?
- What is the stockout risk for top-selling products?
- Which locations have the highest stockout rates?

### Overstock Identification & Analysis

- What products are overstocked?
- Which products have excess inventory based on days of supply?
- Show me products with days of supply > 90

### Inventory Value & Financial Metrics

- What is the inventory value by location?
- What is the inventory value by product category?
- Show me total inventory value at cost vs retail

### Days of Supply & Reorder Management

- What are the days of supply for top-selling products?
- Which products need reordering?
- Show me products below reorder point

### Inventory Movements & Replenishment

- How much inventory is in transit?
- What types of inventory movements occurred last month?
- What was the replenishment activity last month?
- Show me inventory transfers between locations

### Inventory Turnover & Efficiency

- What is the inventory turnover rate by category?
- Which products have the highest turnover?
- Compare inventory investment to sales performance

### Stockout Events & Lost Sales Impact

- Which locations have the highest stockout rates?
- What is the revenue impact of stockouts?
- Show me lost sales by product category
- What is the peak season impact of stockouts?

### Location & Regional Comparisons

- Compare inventory metrics across locations
- Which regions have the best inventory health?
- Show me inventory distribution by region

### Historical Trends & Patterns

- How have inventory levels changed over time?
- What are the trends in stockout events?
- Show me inventory value trends by month

### Inventory Health Metrics

- What is the overall inventory health score?
- Show me inventory health by category
- Which products need attention?

---

## Sample Queries

For comprehensive sample queries covering all analytical categories, see [sample-queries/sample_queries.ipynb](./sample-queries/sample_queries.ipynb).

The sample queries document includes:
- Sample queries organized by category
- Complexity indicators (Simple, Medium, Complex)
- Expected response patterns
- Data sources for each query

For advanced analytical queries (ABC analysis, supply chain efficiency, demand planning, financial KPIs), see [advanced-queries.ipynb](./advanced-queries.ipynb).

---

## Data Model

For detailed information about the inventory analytics data model, see [data_model.md](./data_model.md).

The data model documentation includes:
- Core inventory tables (gold_inventory_fact, gold_stockout_events, gold_inventory_movement_fact)
- Supporting dimension tables (gold_product_dim, gold_location_dim, gold_date_dim)
- Table relationships and join patterns
- Key metrics and calculations
- Data quality notes and best practices

---

## Metric Views

For pre-aggregated metrics that improve Genie performance, see the [metric-views/](./metric-views/) folder.

Metric views provide:
- Pre-calculated KPIs for common question types
- Faster query response times
- Consistent metric calculations

---

## Response Quality

The Genie space is configured to provide:

- **Natural Language Responses**: Conversational, business-friendly language
- **Actionable Recommendations**: 1-3 specific recommendations per response
- **Proactive Suggestions**: Related insights to enhance discovery
- **Error Handling**: Specific error details with actionable guidance
- **Multi-Domain Detection**: Clear redirection for multi-domain queries (e.g., customer behavior questions)

---

## Performance Targets

- **Simple Queries**: < 10 seconds (e.g., single table with filters, simple aggregations)
- **Medium Complexity Queries**: < 30 seconds (e.g., multi-table joins, aggregations)
- **Complex Queries**: < 60 seconds (e.g., complex joins, window functions, time-series analysis)

---

## Folder Structure

```
inventory-analytics/
├── README.genie.inventory.md           # This file - unified guide
├── quickstart.md                       # Step-by-step setup guide
├── instructions.md                     # Genie space instructions
├── data_model.md                       # Data model documentation
├── add_table_comments.sql              # SQL for table/column comments
├── advanced-queries.ipynb              # Advanced analytical queries
├── metric-views/                       # Metric views for performance
│   ├── inventory_metric_views.ipynb
│   └── inventory_metric_view_queries.ipynb
└── sample-queries/                     # Sample queries
    └── sample_queries.ipynb
```

---

These questions help inventory analysts optimize stock levels, prevent stockouts, reduce overstock, improve replenishment timing, and identify operational issues. They support data-driven decision-making for improving inventory operations and supply chain efficiency.
