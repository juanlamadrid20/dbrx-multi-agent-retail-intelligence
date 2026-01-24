# Customer Behavior Genie

The Customer Behavior Genie space provides natural language querying of customer behavior data, enabling analysts to understand customer purchasing patterns, segmentation, cart abandonment, product affinity, channel behavior, and engagement metrics.

---

## Quick Start

Follow the [Quickstart Guide](./quickstart.md) to set up and configure your Genie space.

---

## Configuration Artifacts

All configuration artifacts are in this folder:

| File | Description |
|------|-------------|
| [quickstart.md](./quickstart.md) | Step-by-step guide to set up the Genie space |
| [instructions.md](./instructions.md) | Genie space instructions (~37 lines) covering business context, key terms, analysis patterns, and response guidelines |
| [data_model.md](./data_model.md) | Data model documentation describing tables, relationships, key metrics, and best practices |
| [sample-queries/sample_queries.ipynb](./sample-queries/sample_queries.ipynb) | Sample queries organized by analytical category |
| [add_table_comments.sql](./add_table_comments.sql) | SQL to add table and column comments for better Genie understanding |
| [metric-views/](./metric-views/) | Metric views for performance optimization |

---

## Prerequisites

Before setting up the Genie space:

1. **Databricks Workspace Access**: Admin or owner permissions to create Genie spaces
2. **Data Tables Deployed**: The following tables must exist in your catalog/schema:
   - `gold_customer_dim`
   - `gold_product_dim`
   - `gold_date_dim`
   - `gold_channel_dim`
   - `gold_sales_fact`
   - `gold_cart_abandonment_fact`
   - `gold_customer_product_affinity_agg`
   - `gold_customer_event_fact`

---

## Customer Behavior Analysis

A customer behavior analyst would ask questions that help uncover patterns, trends, and actionable insights about how customers interact with products, channels, and the brand.

### Example Questions

- What products are trending?
- Through which channels do customers prefer to shop?
- Which segments respond best to personalization?

---

## Analytical Categories

### Customer Segmentation & Value

- What are the key customer segments, and how do their lifetime values differ?
- Which segments have the highest average order value or frequency?
- What is the distribution of customer lifetime value across segments?

### Purchase Patterns & RFM Analysis

- How frequently do customers make purchases, and how recently?
- Which customers are at risk of churning, and which are the most loyal?
- What is the average time between purchases for different segments?

### Product & Category Affinity

- Which product categories are most often purchased together?
- What are the most common product pairings in a single transaction?
- How does category affinity differ by customer segment?

### Channel Behavior & Migration

- Through which channels do customers prefer to shop?
- How do customers migrate between acquisition and preferred channels over time?
- What is the impact of channel on purchase frequency and value?

### Engagement & Funnel Analysis

- What are the conversion rates at each stage of the engagement funnel (view, cart, purchase)?
- Which channels drive the most engagement and conversions?
- Where are customers dropping off in the purchase funnel?

### Abandonment & Recovery

- What is the rate of cart abandonment, and how effective are recovery campaigns?
- Which stages of the funnel have the highest abandonment rates?
- What is the revenue recovery rate from abandoned carts?

### Personalization & Affinity Impact

- How effective are personalized recommendations in driving purchases?
- Which segments respond best to personalization?
- What is the predicted impact of affinity-based targeting on CLTV?

---

## Sample Queries

For comprehensive sample queries covering all analytical categories, see [sample-queries/sample_queries.ipynb](./sample-queries/sample_queries.ipynb).

The sample queries document includes:
- Sample queries organized by category
- Complexity indicators (Simple, Medium, Complex)
- Expected response patterns
- Data sources for each query

For advanced analytical queries (RFM segmentation, basket analysis, cohort retention, personalization effectiveness), see [advanced-queries.ipynb](./advanced-queries.ipynb).

---

## Data Model

For detailed information about the customer behavior data model, see [data_model.md](./data_model.md).

The data model documentation includes:
- Core dimension tables (customer, product, date, channel)
- Core fact tables (sales, cart abandonment, affinity, events)
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
- **Multi-Domain Detection**: Clear redirection for multi-domain queries (e.g., inventory questions)

---

## Performance Targets

- **Simple Queries**: < 10 seconds (e.g., single table with filters, simple aggregations)
- **Medium Complexity Queries**: < 30 seconds (e.g., multi-table joins, aggregations)
- **Complex Queries**: < 60 seconds (e.g., complex joins, window functions, time-series analysis)

---

## Folder Structure

```
customer-behavior/
├── README.genie.customer-behavior.md   # This file - unified guide
├── quickstart.md                       # Step-by-step setup guide
├── instructions.md                     # Genie space instructions
├── data_model.md                       # Data model documentation
├── add_table_comments.sql              # SQL for table/column comments
├── advanced-queries.ipynb              # Advanced analytical queries
├── metric-views/                       # Metric views for performance
│   ├── customer_behavior_metric_views.ipynb
│   └── customer_behavior_metric_view_queries.ipynb
└── sample-queries/                     # Sample queries
    └── sample_queries.ipynb
```

---

These questions help analysts identify opportunities for targeted marketing, retention strategies, product bundling, and channel optimization. They support data-driven decision-making for improving customer experience and business outcomes.
