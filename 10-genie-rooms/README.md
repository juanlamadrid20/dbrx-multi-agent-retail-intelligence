# Genie Rooms Testing

This directory contains resources for testing and documenting Databricks Genie spaces.

## Notebooks

### `test-genie-access.ipynb`
Comprehensive testing notebook for verifying Genie space access and responses.

**Features**:
- Tests all configured Genie spaces
- Sends domain-specific queries
- Validates actual responses (not just permissions)
- Shows generated SQL queries
- Supports custom queries for debugging

**When to use**:
- Before creating the multi-agent system
- Debugging Genie access issues
- Testing new queries
- Verifying permissions

**Usage**:
```python
# Run all tests
test_all_genie_spaces(domains=DOMAINS, test_queries={...})

# Test individual space
test_genie_space(space_id="...", query="...")
```

---

## Configuration Artifacts

### `genie-configs/customer-behavior/`
Configuration artifacts for Customer Behavior Genie space.

### `genie-configs/inventory-analytics/`
Configuration artifacts for Inventory Analytics Genie space.

**Contents**:
- `instructions.md` - Genie space instructions
- `sample_queries.md` - Sample queries organized by category
- `data-model.md` - Reference data model documentation
- `quickstart.md` - Configuration guide
- `README.md` - Configuration documentation

See `genie-configs/inventory-analytics/README.md` for details.

## Documentation

### `README.genie.customer-behavior.md`
Documentation for Customer Behavior Genie space.

**Contents**:
- Available data and metrics
- Example queries
- Data schema information

### `README.genie.inventory.md`
Documentation for Inventory Management Genie space.

**Contents**:
- Available data and metrics
- Example queries
- Data schema information

---

## Related Code

The testing utilities are implemented in:
- `../30-mosaic-tool-calling-agent/src/genie/test_utils.py` - Reusable testing functions
- `../30-mosaic-tool-calling-agent/src/config/agent_config.py` - Genie space configuration

---

## Quick Start

1. **Run test notebook**: Open `test-genie-access.ipynb` in Databricks
2. **Verify access**: Confirm all Genie spaces return valid responses
3. **If tests fail**: Request permissions from Genie space owners
4. **Proceed to agent**: Once tests pass, create the multi-agent system in `../30-mosaic-tool-calling-agent/notebooks/02-create-agent.ipynb`
