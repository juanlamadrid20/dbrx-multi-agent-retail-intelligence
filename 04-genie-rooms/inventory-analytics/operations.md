# Inventory Analytics Genie Operations

Use this runbook for permissions, troubleshooting, and post-launch quality checks.

## Permissions

Users of the Genie room need `SELECT` on all room data sources.

Recommended grant:

```sql
GRANT SELECT ON SCHEMA juan_use1_catalog.retail TO `user@example.com`;
```

Mode-specific object-level examples:

```sql
-- Mode A examples
GRANT SELECT ON TABLE juan_use1_catalog.retail.gold_inventory_fact TO `user@example.com`;
GRANT SELECT ON TABLE juan_use1_catalog.retail.gold_stockout_events TO `user@example.com`;

-- Mode B examples
GRANT SELECT ON TABLE juan_use1_catalog.retail.inventory_current_status_mv TO `user@example.com`;
GRANT SELECT ON TABLE juan_use1_catalog.retail.inventory_stockout_risk_mv TO `user@example.com`;
```

Quick verification:

```sql
SHOW TABLES IN juan_use1_catalog.retail;
SELECT * FROM juan_use1_catalog.retail.gold_inventory_fact LIMIT 1;
SELECT * FROM juan_use1_catalog.retail.inventory_current_status_mv LIMIT 1;
```

## Common Issues

### Data sources not found
- Confirm objects exist in catalog/schema.
- Confirm correct names were added to Genie.
- Confirm user and room owner permissions.

### Weak or off-target answers
- Ensure correct mode instructions were applied.
- Ensure sample queries include representative inventory patterns.
- For Mode A, ensure table/column comments are present.

### Multi-domain redirect not happening
- Confirm instruction file includes multi-domain guardrail text.
- Add sample queries that explicitly test redirection behavior.

### Forecasting not being rejected
- Confirm instruction file includes forecasting boundary text.
- Add sample prompts like "forecast inventory needs" to reinforce behavior.

## Ongoing Quality Loop

- Weekly: review top user prompts and add missing sample queries.
- Monthly: validate smoke tests from `quickstart.md`.
- After schema/view changes: refresh instructions and sample queries.
