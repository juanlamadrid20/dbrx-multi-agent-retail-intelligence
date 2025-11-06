# Manual Tasks Guide: Inventory Analytics Genie Configuration

**Configuration Location**: `10-genie-rooms/genie-configs/inventory-analytics/`  
**Reference**: `specs/004-databricks-inventory-analytics/tasks.md`

## Overview

This document provides guidance for completing manual tasks that require Databricks UI interaction. Some tasks have been automated (configuration artifacts copied), but the following tasks require manual execution in the Databricks workspace.

## Completed Tasks ✅

- ✅ **T003**: Configuration directory structure created
- ✅ **T004-T007**: Configuration artifacts copied to `10-genie-rooms/genie-configs/inventory-analytics/`
- ✅ **T024**: README created for configuration directory
- ✅ **T025**: Table access permissions documented

## Manual Tasks Remaining

### Phase 3.1: Setup & Prerequisites

#### T001: Verify Table Comments
**Status**: ⚠️ Manual - Requires Databricks SQL access

**Steps**:
1. Connect to Databricks workspace
2. Run SQL queries to check table comments:
   ```sql
   DESCRIBE EXTENDED juan_dev.retail.gold_inventory_fact;
   DESCRIBE EXTENDED juan_dev.retail.gold_stockout_events;
   DESCRIBE EXTENDED juan_dev.retail.gold_inventory_movement_fact;
   ```
3. Verify table-level comments exist and describe purpose, grain, and key metrics
4. Verify key columns have column-level comments
5. Reference: `specs/004-databricks-inventory-analytics/data-model.md` for comment format examples

**Expected Result**: All tables have comprehensive comments for automatic schema discovery

#### T002: Add Table Comments if Missing
**Status**: ⚠️ Manual - Only if T001 reveals missing comments

**Steps** (if needed):
1. Use format from `specs/004-databricks-inventory-analytics/data-model.md` section "Example Table Comment Format"
2. Add table-level comments:
   ```sql
   COMMENT ON TABLE juan_dev.retail.gold_inventory_fact IS 
   'Daily inventory snapshot fact table. Grain: Product × Location × Date. 
   Tracks inventory levels, stockout status, days of supply, reorder points, and inventory values.';
   ```
3. Add column-level comments for key columns (quantity_available, days_of_supply, reorder_point, etc.)
4. Verify comments are comprehensive

### Phase 3.3: Genie Space Creation & Configuration

#### T008: Create Genie Space
**Status**: ⚠️ Manual - Requires Databricks Genie UI access

**Steps**:
1. Navigate to Genie interface in Databricks workspace
2. Click "Create Space" or "New Space"
3. Name: "Inventory Analytics"
4. Description: "Natural language queries for inventory analytics, stockout risk, overstock, replenishment, and inventory movements"
5. Click "Create"
6. **Important**: Note the Genie space ID (appears in URL or space settings)
7. Update `10-genie-rooms/genie-configs/inventory-analytics/README.md` with space ID

**Expected Result**: Genie space created, space ID documented

#### T009: Add Core Inventory Tables
**Status**: ⚠️ Manual - Requires Genie space access

**Steps**:
1. In Genie space settings, navigate to "Data" or "Tables" section
2. Add `juan_dev.retail.gold_inventory_fact`
3. Add `juan_dev.retail.gold_stockout_events`
4. Add `juan_dev.retail.gold_inventory_movement_fact`
5. Verify Unity Catalog permissions allow access
6. Verify tables appear in Genie space data list

**Expected Result**: Three core inventory tables added to Genie space

#### T010: Add Supporting Dimension Tables
**Status**: ⚠️ Manual - Requires Genie space access

**Steps**:
1. In Genie space settings, navigate to "Data" or "Tables" section
2. Add `juan_dev.retail.gold_product_dim`
3. Add `juan_dev.retail.gold_location_dim`
4. Add `juan_dev.retail.gold_date_dim`
5. Verify tables appear in Genie space data list

**Expected Result**: Three dimension tables added to Genie space

#### T011: Apply Genie Instructions
**Status**: ⚠️ Manual - Requires Genie space configuration access

**Steps**:
1. Open Genie space settings → Instructions/System Prompt section
2. Click "Edit"
3. Copy content from `10-genie-rooms/genie-configs/inventory-analytics/instructions.md`
4. Paste into Instructions field
5. Verify all sections are present:
   - Business Context
   - Key Business Terms
   - Common Analysis Patterns
   - Response Guidelines
   - Error Handling
   - Multi-Domain Detection
   - Forecasting Boundaries
6. Click "Save" or "Apply"

**Expected Result**: Instructions applied to Genie space

#### T012: Add Sample Queries
**Status**: ⚠️ Manual - Requires Genie space configuration access

**Steps**:
1. Open Genie space settings → Sample Queries section
2. Click "Edit"
3. Copy queries from `10-genie-rooms/genie-configs/inventory-analytics/sample_queries.md`
4. Add queries organized by category:
   - Start with Simple queries from each category
   - Add Medium complexity queries
   - Add Complex queries
   - Include error handling and multi-domain detection queries
5. Click "Save" or "Apply"

**Expected Result**: Sample queries added to Genie space

### Phase 3.4: Validation & Testing

**Status**: ⚠️ Manual - Requires Genie space access and testing

All testing tasks (T013-T023) require manual execution in the Genie space:

#### T013: Test Simple Query
- Query: "What products are currently out of stock?"
- Verify: Natural language explanation, structured data table, actionable insights, response time <10 seconds

#### T014: Test Medium Complexity Query
- Query: "Which products are at risk of stockout?"
- Verify: Risk level assessment, prioritized list, recommended actions, response time <60 seconds

#### T015: Test Follow-Up Question
- First: "Which products are at risk of stockout?"
- Follow-up: "What about their replenishment schedule?"
- Verify: Context maintained, relevant response

#### T016-T018: Test Error Handling
- T016: Ambiguous query "inventory" → Should ask clarifying questions
- T017: Future date query → Should explain forecasting out of scope
- T018: Non-existent location → Should list available locations

#### T019-T020: Test Multi-Domain Detection
- T019: "Which customers are affected by stockouts?" → Should redirect
- T020: "Show me customer behavior for products that are out of stock" → Should redirect

#### T021-T023: Test Complex Queries and Performance
- T021: Inventory turnover query → Verify calculations and trends
- T022: Historical trends query → Verify time-series analysis
- T023: Performance boundaries → Verify response times

## Remaining Documentation Tasks

#### T026: Update Main README
**Status**: ✅ Completed - Main README updated

#### T027: Commit to Version Control
**Status**: ⚠️ Manual - Requires git access

**Steps**:
```bash
cd /Users/juan.lamadrid/dev/databricks-projects/ml/agent-bricks/dbrx-multi-agent-retail-intelligence
git add 10-genie-rooms/genie-configs/inventory-analytics/
git commit -m "feat: Add Inventory Analytics Genie configuration artifacts"
```

#### T028: Create User-Facing Documentation
**Status**: ⚠️ Optional - Can be created based on user feedback

**Content Suggestions**:
- Example queries users can ask
- Troubleshooting tips
- Response format expectations
- Best practices for querying

## Progress Summary

**Completed**: 7 tasks (T003, T004-T007, T024-T025)
**Manual Remaining**: 21 tasks (T001-T002, T008-T023, T027-T028)

**Next Steps**:
1. Complete T001-T002: Verify/add table comments
2. Complete T008-T012: Create and configure Genie space
3. Complete T013-T023: Test queries and validate configuration
4. Complete T027: Commit to version control

## Reference Files

- **Tasks**: `specs/004-databricks-inventory-analytics/tasks.md`
- **Quickstart Guide**: `10-genie-rooms/genie-configs/inventory-analytics/quickstart.md`
- **Configuration**: `10-genie-rooms/genie-configs/inventory-analytics/`
- **Specification**: `specs/004-databricks-inventory-analytics/spec.md`

