# Tests: Inventory-Aligned Synthetic Data Generation

Test suite for validating inventory-constrained customer behavior data generation.

## Setup

### Install test dependencies
```bash
pip install -r tests/requirements-test.txt
```

### Verify pytest configuration
```bash
pytest --collect-only tests/
```

Expected output: `collected 0 items` (directories exist but no tests yet)

## Structure

```
tests/
├── contract/       # Delta table schema validation tests
├── integration/    # End-to-end pipeline validation tests
├── unit/          # Component unit tests (InventoryManager, SalesValidator, etc.)
└── conftest.py    # Shared pytest fixtures (PySpark, sample data)
```

## Running Tests

### All tests
```bash
pytest tests/ -v
```

### By category
```bash
pytest tests/contract/ -v          # Contract tests only
pytest tests/unit/ -v              # Unit tests only
pytest tests/integration/ -v       # Integration tests only
```

### Specific test file
```bash
pytest tests/contract/test_inventory_snapshot_schema.py -v
```

### With Databricks MCP tool
Tests can query actual Databricks tables via MCP `run_sql_query` tool for validation.

## Test Requirements

- **Contract Tests**: Require Delta tables to exist in Unity Catalog (`juan_dev.retail`)
- **Integration Tests**: Require full data generation pipeline to have run
- **Unit Tests**: Standalone, no external dependencies

## Databricks MCP Integration

This test suite can leverage the Databricks MCP server for:
- Direct SQL query execution against Unity Catalog tables
- Schema validation without local Spark session
- Real-time data validation during pipeline runs

Example:
```python
# In contract tests, can use MCP tool:
# mcp__dbrx-admin-mcp__run_sql_query(sql="DESCRIBE juan_dev.retail.gold_inventory_fact")
```

## TDD Workflow

1. **Write tests first** (must FAIL initially)
2. Implement features to make tests PASS
3. Run full test suite to verify no regressions

See `specs/001-i-want-to/tasks.md` for test execution order.
