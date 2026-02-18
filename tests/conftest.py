"""
Pytest configuration and shared fixtures for Databricks testing
All tests run against actual Databricks workspace via MCP tools
"""

import pytest
from datetime import date, datetime
import random


@pytest.fixture(scope="session")
def databricks_config():
    """
    Databricks workspace configuration for all tests.

    All tests use MCP tools to query actual Unity Catalog tables.
    No local Spark session required.

    Returns:
        Dict with catalog, schema, and MCP tool references
    """
    return {
        'catalog': 'juan_use1_catalog',
        'schema': 'retail',
        'full_schema': 'juan_use1_catalog.retail',
    }


@pytest.fixture(scope="function")
def mcp_query(databricks_config):
    """
    Helper function to execute SQL queries via MCP tool.

    Usage in tests:
        result = mcp_query("SELECT COUNT(*) as cnt FROM gold_inventory_fact")
        assert result is not None

    Note: Actual MCP tool call must be made by the test framework.
    This fixture provides the configuration and helper pattern.
    """
    def execute_query(sql):
        """
        Execute SQL query against Databricks workspace.
        Tests should use mcp__dbrx-admin-mcp__run_sql_query tool directly.

        Args:
            sql: SQL query string

        Returns:
            Query results (structure depends on MCP tool response)
        """
        # This is a placeholder - actual execution happens via MCP tool
        # in the test itself using: mcp__dbrx-admin-mcp__run_sql_query(sql=sql)
        return {
            'catalog': databricks_config['catalog'],
            'schema': databricks_config['schema'],
            'sql': sql,
            'note': 'Execute via mcp__dbrx-admin-mcp__run_sql_query tool'
        }

    return execute_query


@pytest.fixture(scope="function")
def table_exists():
    """
    Helper to check if a table exists in Unity Catalog.

    Usage:
        exists = table_exists("gold_inventory_fact")
    """
    def check_table(table_name, catalog='juan_use1_catalog', schema='retail'):
        sql = f"SHOW TABLES IN {catalog}.{schema} LIKE '{table_name}'"
        # Return SQL query for MCP tool execution
        return sql

    return check_table


@pytest.fixture(scope="function")
def get_table_schema():
    """
    Helper to get table schema from Unity Catalog.

    Usage:
        schema_sql = get_table_schema("gold_inventory_fact")
        # Execute via MCP: mcp__dbrx-admin-mcp__run_sql_query(sql=schema_sql)
    """
    def get_schema(table_name, catalog='juan_use1_catalog', schema='retail'):
        sql = f"DESCRIBE {catalog}.{schema}.{table_name}"
        return sql

    return get_schema


@pytest.fixture(scope="function")
def sample_date_keys():
    """
    Generate sample date keys for testing.

    Returns:
        List of date_key integers (YYYYMMDD format)
    """
    return [
        20250101,  # Jan 1, 2025
        20250102,  # Jan 2, 2025
        20250103,  # Jan 3, 2025
        20250104,  # Jan 4, 2025
        20250105,  # Jan 5, 2025
    ]


@pytest.fixture(scope="function")
def expected_inventory_columns():
    """
    Expected columns for gold_inventory_fact table after schema updates.
    Used in contract tests.
    """
    return {
        # Existing columns
        'product_key': 'int',
        'location_key': 'int',
        'date_key': 'int',
        'quantity_on_hand': 'int',
        'quantity_available': 'int',
        'quantity_reserved': 'int',
        'quantity_in_transit': 'int',
        'quantity_damaged': 'int',
        'inventory_value_cost': 'double',
        'inventory_value_retail': 'double',
        'days_of_supply': 'int',
        'stock_cover_days': 'int',
        'reorder_point': 'int',
        'reorder_quantity': 'int',
        'is_overstock': 'boolean',
        'is_discontinued': 'boolean',
        'source_system': 'string',
        'etl_timestamp': 'timestamp',
        # NEW columns (after implementation)
        'is_stockout': 'boolean',
        'stockout_duration_days': 'int',
        'last_replenishment_date': 'date',
        'next_replenishment_date': 'date',
    }


@pytest.fixture(scope="function")
def expected_sales_columns():
    """
    Expected columns for gold_sales_fact table after schema updates.
    Used in contract tests.
    """
    return {
        # Existing columns
        'transaction_id': 'string',
        'line_item_id': 'string',
        'customer_key': 'int',
        'product_key': 'int',
        'date_key': 'int',
        'time_key': 'int',
        'location_key': 'int',
        'channel_key': 'int',
        'order_number': 'string',
        'quantity_sold': 'int',
        'unit_price': 'double',
        'discount_amount': 'double',
        'tax_amount': 'double',
        'net_sales_amount': 'double',
        'gross_margin_amount': 'double',
        'is_return': 'boolean',
        'is_exchange': 'boolean',
        'is_promotional': 'boolean',
        'is_clearance': 'boolean',
        'fulfillment_type': 'string',
        'payment_method': 'string',
        'source_system': 'string',
        'etl_timestamp': 'timestamp',
        # NEW columns (after implementation)
        'quantity_requested': 'int',
        'is_inventory_constrained': 'boolean',
        'inventory_at_purchase': 'int',
        'return_restocked_date_key': 'int',
    }


@pytest.fixture(scope="function")
def expected_stockout_event_columns():
    """
    Expected columns for new gold_stockout_events table.
    Used in contract tests.
    """
    return {
        'stockout_id': 'bigint',
        'product_key': 'int',
        'location_key': 'int',
        'stockout_start_date_key': 'int',
        'stockout_end_date_key': 'int',
        'stockout_duration_days': 'int',
        'lost_sales_attempts': 'int',
        'lost_sales_quantity': 'int',
        'lost_sales_revenue': 'double',
        'peak_season_flag': 'boolean',
        'source_system': 'string',
        'etl_timestamp': 'timestamp',
    }


@pytest.fixture(scope="function")
def expected_cart_abandonment_columns():
    """
    Expected columns for gold_cart_abandonment_fact table after updates.
    Used in contract tests.
    """
    return {
        # Existing columns
        'abandonment_id': 'int',
        'cart_id': 'string',
        'customer_key': 'int',
        'date_key': 'int',
        'time_key': 'int',
        'channel_key': 'int',
        'cart_value': 'double',
        'items_count': 'int',
        'minutes_in_cart': 'int',
        'recovery_email_sent': 'boolean',
        'recovery_email_opened': 'boolean',
        'recovery_email_clicked': 'boolean',
        'is_recovered': 'boolean',
        'recovery_date_key': 'int',
        'recovery_revenue': 'double',
        'abandonment_stage': 'string',
        'suspected_reason': 'string',
        'source_system': 'string',
        'etl_timestamp': 'timestamp',
        # NEW columns (after implementation)
        'low_inventory_trigger': 'boolean',
        'inventory_constrained_items': 'int',
    }


@pytest.fixture(scope="function")
def reset_random_seed():
    """
    Reset random seed before each test for reproducibility.
    """
    random.seed(42)
    yield


# Pytest configuration
def pytest_configure(config):
    """
    Register custom markers for test categorization.
    """
    config.addinivalue_line(
        "markers", "contract: Contract tests for Delta table schemas"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests requiring Databricks"
    )
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take >5 seconds to run"
    )
    config.addinivalue_line(
        "markers", "mcp: Tests using Databricks MCP tools"
    )


def pytest_collection_modifyitems(config, items):
    """
    Automatically mark tests based on their location.
    All tests are marked as 'mcp' since they use Databricks MCP tools.
    """
    for item in items:
        # Add location-based markers
        if "contract" in str(item.fspath):
            item.add_marker(pytest.mark.contract)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # All tests use MCP tools
        item.add_marker(pytest.mark.mcp)
