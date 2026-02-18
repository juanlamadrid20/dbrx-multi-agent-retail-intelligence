# Customer Behavior Genie

Natural language analytics for customer segmentation, RFM behavior, product affinity, channel behavior, engagement funnels, and cart abandonment.

## Start Here

- Setup steps: [quickstart.md](./quickstart.md)
- Room prompt selection (by mode): [instructions.md](./instructions.md)
- Data model reference: [data_model.md](./data_model.md)
- Ops and troubleshooting: [operations.md](./operations.md)
- Sample prompts: [sample-queries/sample_queries.ipynb](./sample-queries/sample_queries.ipynb)

## Setup Modes

Choose one mode for the Genie room:

### Mode A: Tables-Based Room

Add these tables to Genie:
- `gold_customer_dim`
- `gold_product_dim`
- `gold_date_dim`
- `gold_channel_dim`
- `gold_sales_fact`
- `gold_cart_abandonment_fact`
- `gold_customer_product_affinity_agg`
- `gold_customer_event_fact`

Use prompt file: `instructions.tables.md`

### Mode B: Metric-Views-Only Room

Add only these metric views to Genie:
- `customer_segmentation_mv`
- `customer_rfm_analysis_mv`
- `customer_purchase_summary_mv`
- `product_affinity_mv`
- `channel_behavior_mv`
- `channel_migration_mv`
- `engagement_funnel_mv`
- `cart_abandonment_mv`
- `personalization_impact_mv`
- `segment_trends_daily_mv`

Use prompt file: `instructions.metric-views.md`

## Minimal Validation

After configuration, run at least these checks:
- "What are the key customer segments?"
- "What products are trending?"
- "What is the rate of cart abandonment?"

Expected behavior:
- Direct answer + key metrics + 1-3 actions
- Multi-domain requests are redirected

## Notes

- Prefer Mode B for consistent KPI logic and faster responses.
- Prefer Mode A for more flexible low-level exploration from base tables.
