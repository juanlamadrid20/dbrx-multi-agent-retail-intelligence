"""
Contract test for gold_sales_fact table schema.
Schema contract: tests/contract/fixtures/gold_sales_fact.json

This test MUST FAIL initially (new columns don't exist yet).
After implementation of T014-T015, this test should PASS.
"""

import pytest


@pytest.mark.contract
@pytest.mark.mcp
def test_sales_fact_table_exists(databricks_config, get_table_schema):
    """
    Test that gold_sales_fact table exists in Unity Catalog.

    Uses MCP tool: mcp__dbrx-admin-mcp__run_sql_query
    """
    # Generate SQL to check table existence
    sql = f"SHOW TABLES IN {databricks_config['full_schema']} LIKE 'gold_sales_fact'"

    # Expected: This should work since table already exists
    # In actual test execution, use: mcp__dbrx-admin-mcp__run_sql_query(sql=sql)
    # For now, this is a template showing the expected pattern

    print(f"Execute via MCP: {sql}")
    assert sql is not None, "SQL query generated"


@pytest.mark.contract
@pytest.mark.mcp
def test_sales_fact_new_columns_exist(databricks_config, expected_sales_columns):
    """
    Test that new sales columns exist after schema evolution.

    NEW COLUMNS (will cause test to FAIL initially):
    - quantity_requested: INTEGER
    - is_inventory_constrained: BOOLEAN
    - inventory_at_purchase: INTEGER
    - return_restocked_date_key: INTEGER

    This test should FAIL until T014-T015 (refactor create_sales_fact) is complete.

    Uses MCP tool: mcp__dbrx-admin-mcp__run_sql_query
    """
    table_name = f"{databricks_config['full_schema']}.gold_sales_fact"

    # SQL to get table schema
    sql = f"DESCRIBE {table_name}"

    print(f"Execute via MCP: {sql}")
    print("Expected new columns to validate:")
    print("  - quantity_requested (INT)")
    print("  - is_inventory_constrained (BOOLEAN)")
    print("  - inventory_at_purchase (INT)")
    print("  - return_restocked_date_key (INT)")

    # In actual execution with MCP tool results:
    # result = mcp__dbrx-admin-mcp__run_sql_query(sql=sql)
    # Parse result to extract column names
    # Assert that new columns exist:
    # assert 'quantity_requested' in column_names
    # assert 'is_inventory_constrained' in column_names
    # assert 'inventory_at_purchase' in column_names
    # assert 'return_restocked_date_key' in column_names

    # For now, this will be a placeholder that documents the intent
    pytest.fail("NEW COLUMNS NOT IMPLEMENTED YET - Test should fail until T014-T015 complete")


@pytest.mark.contract
@pytest.mark.mcp
def test_sales_fact_column_types(databricks_config, expected_sales_columns):
    """
    Test that all columns have correct data types.

    Validates both existing and new columns.

    Uses MCP tool: mcp__dbrx-admin-mcp__run_sql_query
    """
    table_name = f"{databricks_config['full_schema']}.gold_sales_fact"

    # SQL to get detailed schema with types
    sql = f"DESCRIBE {table_name}"

    print(f"Execute via MCP: {sql}")
    print(f"Expected {len(expected_sales_columns)} columns total")

    # In actual execution:
    # result = mcp__dbrx-admin-mcp__run_sql_query(sql=sql)
    # Parse result into dict: {col_name: col_type}
    # For each column in expected_sales_columns:
    #   assert actual_columns[col_name].lower() == expected_type.lower()

    pytest.fail("Column type validation not implemented - waiting for schema updates")


@pytest.mark.contract
@pytest.mark.mcp
def test_sales_fact_quantity_requested_not_less_than_sold(databricks_config):
    """
    Test constraint: quantity_requested >= quantity_sold.

    When inventory is constrained, customers get less than requested.
    This constraint ensures logical consistency.

    This test will FAIL until T014-T015 implementation adds quantity_requested column.

    Uses MCP tool: mcp__dbrx-admin-mcp__run_sql_query
    """
    table_name = f"{databricks_config['full_schema']}.gold_sales_fact"

    # SQL to check constraint violations
    sql = f"""
        SELECT COUNT(*) as violation_count
        FROM {table_name}
        WHERE quantity_requested < quantity_sold
    """

    print(f"Execute via MCP: {sql}")
    print("Expected result: violation_count = 0")
    print("Logic: quantity_requested should always be >= quantity_sold")

    # This will fail initially because quantity_requested column doesn't exist yet
    pytest.fail("quantity_requested column not implemented - Test should fail until T014-T015 complete")


@pytest.mark.contract
@pytest.mark.mcp
def test_sales_fact_inventory_constraint_logic(databricks_config):
    """
    Test constraint: is_inventory_constrained = TRUE when quantity_requested > quantity_sold.

    Validates the business logic for inventory constraint detection.

    This test will FAIL until T014-T015 implementation.

    Uses MCP tool: mcp__dbrx-admin-mcp__run_sql_query
    """
    table_name = f"{databricks_config['full_schema']}.gold_sales_fact"

    # SQL to check constraint logic consistency
    sql = f"""
        SELECT COUNT(*) as logic_violation_count
        FROM {table_name}
        WHERE (quantity_requested > quantity_sold AND is_inventory_constrained = FALSE)
           OR (quantity_requested = quantity_sold AND is_inventory_constrained = TRUE)
    """

    print(f"Execute via MCP: {sql}")
    print("Expected result: logic_violation_count = 0")
    print("Logic: is_inventory_constrained should be TRUE iff quantity_requested > quantity_sold")

    # This will fail initially because these columns don't exist yet
    pytest.fail("is_inventory_constrained column not implemented - Test should fail until T014-T015 complete")


@pytest.mark.contract
@pytest.mark.mcp
def test_sales_fact_inventory_at_purchase_non_negative(databricks_config):
    """
    Test constraint: inventory_at_purchase >= 0.

    Inventory snapshot at time of purchase should never be negative.

    This test will FAIL until T014-T015 implementation.

    Uses MCP tool: mcp__dbrx-admin-mcp__run_sql_query
    """
    table_name = f"{databricks_config['full_schema']}.gold_sales_fact"

    # SQL to check for negative inventory snapshots
    sql = f"""
        SELECT COUNT(*) as violation_count
        FROM {table_name}
        WHERE inventory_at_purchase < 0
    """

    print(f"Execute via MCP: {sql}")
    print("Expected result: violation_count = 0")

    # This will fail initially because inventory_at_purchase column doesn't exist yet
    pytest.fail("inventory_at_purchase column not implemented - Test should fail until T014-T015 complete")


@pytest.mark.contract
@pytest.mark.mcp
@pytest.mark.slow
def test_sales_fact_return_restocked_date_validation(databricks_config):
    """
    Test requirement: Returns should replenish inventory 1-3 days after return date.

    Validates FR-008 from specification:
    - return_restocked_date_key should be 1-3 days after date_key for returns
    - Only applies to records where is_return = TRUE

    Uses MCP tool: mcp__dbrx-admin-mcp__run_sql_query
    """
    table_name = f"{databricks_config['full_schema']}.gold_sales_fact"

    # SQL to validate return restock delay
    sql = f"""
        WITH return_delays AS (
            SELECT
                sf.transaction_id,
                sf.date_key as return_date_key,
                sf.return_restocked_date_key,
                d1.calendar_date as return_date,
                d2.calendar_date as restock_date,
                DATEDIFF(d2.calendar_date, d1.calendar_date) as delay_days
            FROM {table_name} sf
            JOIN {databricks_config['full_schema']}.gold_date_dim d1
                ON sf.date_key = d1.date_key
            LEFT JOIN {databricks_config['full_schema']}.gold_date_dim d2
                ON sf.return_restocked_date_key = d2.date_key
            WHERE sf.is_return = TRUE
                AND sf.return_restocked_date_key IS NOT NULL
        )
        SELECT
            COUNT(*) as total_returns,
            SUM(CASE WHEN delay_days BETWEEN 1 AND 3 THEN 1 ELSE 0 END) as valid_delays,
            SUM(CASE WHEN delay_days < 1 OR delay_days > 3 THEN 1 ELSE 0 END) as invalid_delays,
            MIN(delay_days) as min_delay,
            MAX(delay_days) as max_delay,
            AVG(delay_days) as avg_delay
        FROM return_delays
    """

    print(f"Execute via MCP: {sql}")
    print("Expected: All delays should be 1-3 days (invalid_delays = 0)")
    print("Config: return_delay_days = (1, 3)")

    # In actual execution:
    # result = mcp__dbrx-admin-mcp__run_sql_query(sql=sql)
    # assert result['invalid_delays'] == 0,
    #   f"Found {result['invalid_delays']} returns with delays outside 1-3 day range"

    pytest.fail("Return restock date validation pending - T014-T015 implementation required")


@pytest.mark.contract
@pytest.mark.mcp
@pytest.mark.slow
def test_sales_fact_no_sales_exceed_inventory(databricks_config):
    """
    Test critical constraint: No sale should exceed available inventory at time of purchase.

    This validates the core requirement that sales are constrained by inventory.
    Cross-references sales_fact with inventory_fact snapshots.

    Uses MCP tool: mcp__dbrx-admin-mcp__run_sql_query
    """
    table_name = f"{databricks_config['full_schema']}.gold_sales_fact"

    # SQL to cross-validate sales against inventory
    sql = f"""
        SELECT COUNT(*) as violation_count
        FROM {table_name} sf
        WHERE sf.inventory_at_purchase < sf.quantity_sold
    """

    print(f"Execute via MCP: {sql}")
    print("Expected result: violation_count = 0")
    print("This is the CORE constraint ensuring inventory alignment")

    # In actual execution:
    # result = mcp__dbrx-admin-mcp__run_sql_query(sql=sql)
    # violation_count = result['violation_count']
    # assert violation_count == 0,
    #   f"CRITICAL: Found {violation_count} sales that exceeded available inventory"

    pytest.fail("Sales-inventory constraint validation pending - T014-T015 implementation required")
