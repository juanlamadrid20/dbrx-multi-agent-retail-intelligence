# Inventory Analytics Genie

Natural language analytics for inventory levels, stockout risk, overstock, replenishment, movements, and inventory value.

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
- `gold_inventory_fact`
- `gold_stockout_events`
- `gold_inventory_movement_fact`
- `gold_product_dim`
- `gold_location_dim`
- `gold_date_dim`

Use prompt file: `instructions.tables.md`

### Mode B: Metric-Views-Only Room

Add only these metric views to Genie:
- `inventory_current_status_mv`
- `inventory_stockout_risk_mv`
- `inventory_overstock_analysis_mv`
- `inventory_value_summary_mv`
- `inventory_reorder_management_mv`
- `inventory_movement_summary_mv`
- `inventory_stockout_impact_mv`
- `inventory_location_comparison_mv`
- `inventory_trends_daily_mv`
- `inventory_health_score_mv`

Use prompt file: `instructions.metric-views.md`

## Minimal Validation

After configuration, run at least these checks:
- "What products are currently out of stock?"
- "Which products are at risk of stockout?"
- "What is the inventory value by location?"

Expected behavior:
- Direct answer + key metrics + 1-3 actions
- Multi-domain requests are redirected
- Forecasting requests are rejected

## Notes

- Prefer Mode B for KPI-heavy Q&A and consistent metric logic.
- Prefer Mode A if you need flexible low-level slicing from base tables.
