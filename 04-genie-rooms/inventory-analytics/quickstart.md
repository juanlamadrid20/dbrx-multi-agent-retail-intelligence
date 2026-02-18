# Quickstart: Inventory Analytics Genie

Use this guide to create a working Genie room in minutes.

## 1) Choose Setup Mode

- **Mode A (tables-based)**: flexible analysis over base tables
- **Mode B (metric-views-only)**: faster KPI-focused analysis with consistent calculations

Canonical object lists are in `README.genie.inventory.md`.

## 2) Create the Genie Room

- Open Genie in Databricks and create a new room.
- Suggested name: `Inventory Analytics`.
- Keep this room inventory-only (no cross-domain sources).

## 3) Add Data Sources

- **Mode A**: add only the tables listed in `README.genie.inventory.md`.
- **Mode B**: add only the metric views listed in `README.genie.inventory.md`.

If you use Mode B and views are missing, run `metric-views/inventory_metric_views.ipynb` first.

## 4) Apply the Right Instructions

- Open `instructions.md`.
- Copy the prompt from the mode-specific file:
  - Mode A -> `instructions.tables.md`
  - Mode B -> `instructions.metric-views.md`
- Paste into Genie room Instructions/System Prompt and save.

## 5) Add Sample Queries

- Open `sample-queries/sample_queries.ipynb`.
- Add representative simple/medium/complex examples to Genie.
- Include at least one error-handling and one multi-domain detection example.

## 6) Smoke Test

Run these prompts:
- "What products are currently out of stock?"
- "Which products are at risk of stockout?"
- "What is the inventory value by location?"
- "Which customers are affected by stockouts?" (should redirect as multi-domain)
- "What will inventory levels be next month?" (should reject forecasting)

## 7) If Something Fails

Use `operations.md` for:
- permissions verification and grant examples
- troubleshooting for missing data sources, weak responses, and prompt issues
- recommended next steps for ongoing quality improvements
