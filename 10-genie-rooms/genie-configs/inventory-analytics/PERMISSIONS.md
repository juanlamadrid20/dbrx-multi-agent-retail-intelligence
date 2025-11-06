# Table Access Permissions: Inventory Analytics Genie

**Schema**: `juan_dev.retail`  
**Genie Space**: Inventory Analytics  
**Configuration Date**: 2025-01-27

## Required Tables

### Core Inventory Tables
- `juan_dev.retail.gold_inventory_fact`
- `juan_dev.retail.gold_stockout_events`
- `juan_dev.retail.gold_inventory_movement_fact`

### Supporting Dimension Tables
- `juan_dev.retail.gold_product_dim`
- `juan_dev.retail.gold_location_dim`
- `juan_dev.retail.gold_date_dim`

## Permission Requirements

**Unity Catalog Permissions**:
- Users accessing the Genie space must have **SELECT** permission on all tables listed above
- Permission should be granted at the schema level (`juan_dev.retail`) or individually per table
- Genie space owner must have permissions to add tables to the space

## Verification Steps

1. **Verify Schema Access**:
   ```sql
   SHOW TABLES IN juan_dev.retail;
   ```

2. **Verify Table Access**:
   ```sql
   SELECT * FROM juan_dev.retail.gold_inventory_fact LIMIT 1;
   SELECT * FROM juan_dev.retail.gold_stockout_events LIMIT 1;
   SELECT * FROM juan_dev.retail.gold_inventory_movement_fact LIMIT 1;
   ```

3. **Verify Dimension Tables**:
   ```sql
   SELECT * FROM juan_dev.retail.gold_product_dim LIMIT 1;
   SELECT * FROM juan_dev.retail.gold_location_dim LIMIT 1;
   SELECT * FROM juan_dev.retail.gold_date_dim LIMIT 1;
   ```

## Granting Permissions

If permissions are missing, the Genie space owner or catalog administrator should grant:

```sql
-- Grant SELECT on schema (recommended)
GRANT SELECT ON SCHEMA juan_dev.retail TO `user@example.com`;

-- Or grant individually per table
GRANT SELECT ON TABLE juan_dev.retail.gold_inventory_fact TO `user@example.com`;
GRANT SELECT ON TABLE juan_dev.retail.gold_stockout_events TO `user@example.com`;
GRANT SELECT ON TABLE juan_dev.retail.gold_inventory_movement_fact TO `user@example.com`;
GRANT SELECT ON TABLE juan_dev.retail.gold_product_dim TO `user@example.com`;
GRANT SELECT ON TABLE juan_dev.retail.gold_location_dim TO `user@example.com`;
GRANT SELECT ON TABLE juan_dev.retail.gold_date_dim TO `user@example.com`;
```

## Troubleshooting

**Issue**: Tables not visible in Genie space
- **Solution**: Verify Unity Catalog permissions allow access to `juan_dev.retail` schema

**Issue**: Queries fail with permission errors
- **Solution**: Ensure users have SELECT permission on all required tables

**Issue**: Genie cannot discover schema
- **Solution**: Verify tables have proper comments (see `data-model.md` for examples)

## Notes

- Unity Catalog permissions are enforced at query time
- Genie space must have access to tables to add them to the space
- Users querying the Genie space need SELECT permissions, not the Genie space itself
- Permission errors will be clearly communicated to users by Genie (FR-016)

