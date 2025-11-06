# Tasks: Databricks Inventory Analytics Genie Room Configuration

**Input**: Design documents from `/specs/004-databricks-inventory-analytics/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Implementation plan loaded successfully
   → Project Type: Genie Space Configuration (documentation and configuration artifacts)
2. Load optional design documents:
   → data-model.md: Table schemas and comment requirements
   → contracts/: genie_instructions.md, sample_queries.md → configuration tasks
   → quickstart.md: Step-by-step configuration steps → task breakdown
3. Generate tasks by category:
   → Setup: Verify table comments, create directory structure
   → Configuration: Copy configuration artifacts, create Genie space
   → Validation: Test queries, error handling, multi-domain detection
   → Documentation: Update README, document space ID
4. Apply task rules:
   → Configuration artifact copying = parallel [P] (different files)
   → Sequential steps: Table comments → Space creation → Configuration → Testing
   → Testing before finalization
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All configuration artifacts copied?
   → All quickstart steps covered?
   → All validation scenarios tested?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Configuration artifacts**: `10-genie-rooms/genie-configs/inventory-analytics/`
- **Specification docs**: `specs/004-databricks-inventory-analytics/`
- **Test notebook**: `10-genie-rooms/notebooks/test-genie-configuration.ipynb`

## Phase 3.1: Setup & Prerequisites
- [ ] T001 Verify table comments exist for core inventory tables
  - Check `juan_dev.retail.gold_inventory_fact` has table-level comment
  - Check `juan_dev.retail.gold_stockout_events` has table-level comment
  - Check `juan_dev.retail.gold_inventory_movement_fact` has table-level comment
  - Verify key columns have column-level comments
  - Reference: `specs/004-databricks-inventory-analytics/data-model.md` for comment format examples

- [ ] T002 Add table comments if missing (if needed)
  - Add table-level comments describing purpose, grain, and key metrics
  - Add column-level comments for key columns (quantity_available, days_of_supply, reorder_point, etc.)
  - Use format from `specs/004-databricks-inventory-analytics/data-model.md` section "Example Table Comment Format"
  - Verify comments are comprehensive for automatic schema discovery

- [x] T003 Create configuration directory structure
  - Create `10-genie-rooms/genie-configs/inventory-analytics/` directory
  - Verify directory exists and is accessible
  - Prepare for configuration artifact placement
  - ✅ **COMPLETED**: Directory created successfully

## Phase 3.2: Configuration Artifacts Setup
**CRITICAL: Configuration artifacts must be copied before applying to Genie space**

- [x] T004 [P] Copy genie instructions to configuration directory
  - Copy `specs/004-databricks-inventory-analytics/contracts/genie_instructions.md` 
  - To: `10-genie-rooms/genie-configs/inventory-analytics/instructions.md`
  - Verify file content matches contract document
  - ✅ **COMPLETED**: File copied successfully

- [x] T005 [P] Copy sample queries to configuration directory
  - Copy `specs/004-databricks-inventory-analytics/contracts/sample_queries.md`
  - To: `10-genie-rooms/genie-configs/inventory-analytics/sample_queries.md`
  - Verify file content matches contract document
  - ✅ **COMPLETED**: File copied successfully

- [x] T006 [P] Copy data model reference documentation
  - Copy `specs/004-databricks-inventory-analytics/data-model.md`
  - To: `10-genie-rooms/genie-configs/inventory-analytics/data-model.md` (optional reference)
  - Note: Genie uses automatic schema discovery, but this serves as reference
  - ✅ **COMPLETED**: File copied successfully

- [x] T007 [P] Copy quickstart guide
  - Copy `specs/004-databricks-inventory-analytics/quickstart.md`
  - To: `10-genie-rooms/genie-configs/inventory-analytics/quickstart.md`
  - Verify all steps are documented
  - ✅ **COMPLETED**: File copied successfully

## Phase 3.3: Genie Space Creation & Configuration
**Sequential steps: Create space → Add tables → Configure instructions → Add sample queries**

- [ ] T008 Create Genie space in Databricks
  - Navigate to Genie interface in Databricks workspace
  - Create new space named "Inventory Analytics"
  - Add description: "Natural language queries for inventory analytics, stockout risk, overstock, replenishment, and inventory movements"
  - Note the Genie space ID for documentation

- [ ] T009 Add core inventory tables to Genie space
  - Add `juan_dev.retail.gold_inventory_fact` to space
  - Add `juan_dev.retail.gold_stockout_events` to space
  - Add `juan_dev.retail.gold_inventory_movement_fact` to space
  - Verify Unity Catalog permissions allow access
  - Verify tables appear in Genie space data list

- [ ] T010 Add supporting dimension tables to Genie space
  - Add `juan_dev.retail.gold_product_dim` to space
  - Add `juan_dev.retail.gold_location_dim` to space
  - Add `juan_dev.retail.gold_date_dim` to space
  - Verify tables appear in Genie space data list

- [ ] T011 Apply Genie instructions to space
  - Open Genie space settings → Instructions/System Prompt section
  - Copy content from `10-genie-rooms/genie-configs/inventory-analytics/instructions.md`
  - Paste into Instructions field
  - Verify all sections are present:
    - Business Context
    - Key Business Terms
    - Common Analysis Patterns
    - Response Guidelines
    - Error Handling
    - Multi-Domain Detection
    - Forecasting Boundaries
  - Save configuration

- [ ] T012 Add sample queries to Genie space
  - Open Genie space settings → Sample Queries section
  - Copy queries from `10-genie-rooms/genie-configs/inventory-analytics/sample_queries.md`
  - Add queries organized by category:
    - Start with Simple queries from each category
    - Add Medium complexity queries
    - Add Complex queries
    - Include error handling and multi-domain detection queries
  - Save sample queries configuration

## Phase 3.4: Validation & Testing
**CRITICAL: Test all query types and error scenarios**

- [ ] T013 Test simple query: Current stock status
  - Query: "What products are currently out of stock?"
  - Verify response includes:
    - Natural language explanation
    - Structured data table
    - Actionable insights/recommendations
  - Verify response time <10 seconds

- [ ] T014 Test medium complexity query: Stockout risk
  - Query: "Which products are at risk of stockout?"
  - Verify response includes:
    - Risk level assessment (High/Medium/Low)
    - Prioritized list of products
    - Recommended actions
  - Verify response time <60 seconds

- [ ] T015 Test follow-up question: Context maintenance
  - First query: "Which products are at risk of stockout?"
  - Follow-up: "What about their replenishment schedule?"
  - Verify Genie understands context and returns replenishment schedule for previously mentioned products
  - Verify conversation context is maintained

- [ ] T016 Test error handling: Ambiguous query
  - Query: "inventory"
  - Verify Genie asks clarifying questions or provides multiple interpretations
  - Verify guidance is provided on how to refine query

- [ ] T017 Test error handling: Future date query
  - Query: "What will inventory levels be next month?"
  - Verify Genie explains forecasting is out of scope
  - Verify Genie suggests analyzing historical trends or current status instead
  - Verify available date range is specified

- [ ] T018 Test error handling: Non-existent location
  - Query: "What is the inventory at location XYZ?"
  - Verify Genie indicates location doesn't exist
  - Verify Genie lists available locations
  - Verify Genie suggests querying available data

- [ ] T019 Test multi-domain detection
  - Query: "Which customers are affected by stockouts?"
  - Verify Genie detects multi-domain query
  - Verify Genie redirects to multi-domain agent with clear message
  - Verify message explains why (combines inventory with customer behavior)

- [ ] T020 Test multi-domain detection (alternative)
  - Query: "Show me customer behavior for products that are out of stock"
  - Verify Genie detects multi-domain query
  - Verify appropriate redirect message

- [ ] T021 Test complex query: Inventory turnover
  - Query: "What is the inventory turnover rate by category?"
  - Verify response includes calculated turnover rates
  - Verify response time <60 seconds
  - Verify response includes comparisons and trends

- [ ] T022 Test historical trends query
  - Query: "How have inventory levels changed over time?"
  - Verify response includes time-series analysis
  - Verify response includes historical trends and patterns
  - Verify visualizations (charts/graphs) are included when helpful

- [ ] T023 Test performance boundaries
  - Test simple query response time: Target <10 seconds
  - Test complex query response time: Target <60 seconds
  - Verify Genie suggests filters for large dataset queries if needed

## Phase 3.5: Documentation & Finalization
- [x] T024 Create README for configuration directory
  - Create `10-genie-rooms/genie-configs/inventory-analytics/README.md`
  - Document Genie space ID
  - Document configuration date
  - Document any customizations or deviations from standard configuration
  - Include links to specification and quickstart guide
  - ✅ **COMPLETED**: README created with configuration details

- [x] T025 Document table access permissions
  - Document Unity Catalog permissions for inventory tables
  - Note any permission requirements for users
  - Document schema location: `juan_dev.retail`
  - ✅ **COMPLETED**: PERMISSIONS.md created with permission documentation

- [x] T026 Update main README (if applicable)
  - Update `10-genie-rooms/README.md` to reference inventory analytics configuration
  - Add inventory analytics to list of configured Genie spaces
  - Include link to configuration directory
  - ✅ **COMPLETED**: Main README updated with inventory analytics section

- [ ] T027 Commit configuration artifacts to version control
  - Commit all files in `10-genie-rooms/genie-configs/inventory-analytics/`
  - Commit any updated documentation
  - Ensure configuration is version-controlled

- [ ] T028 Create user-facing documentation (optional)
  - Create user guide for inventory analysts
  - Document example queries users can ask
  - Include troubleshooting tips
  - Document response format expectations

## Dependencies
- **T001-T003** (Setup) must complete before configuration (T004-T012)
- **T004-T007** (Copy artifacts) can run in parallel [P] - different files
- **T008** (Create space) must complete before T009-T012 (Add tables & configure)
- **T009-T010** (Add tables) can run in parallel after T008
- **T011** (Apply instructions) must complete before T012 (Add sample queries)
- **T012** (Add sample queries) must complete before testing (T013-T023)
- **T013-T023** (Testing) can run mostly in parallel after T012, but:
  - T015 requires T014 to complete first (follow-up question)
  - T021-T022 should run after basic queries pass
- **T024-T028** (Documentation) can run in parallel [P] after testing completes

## Parallel Execution Examples

### Example 1: Copy Configuration Artifacts (T004-T007)
```
# Launch T004-T007 together:
Task: "Copy genie instructions to configuration directory"
Task: "Copy sample queries to configuration directory"
Task: "Copy data model reference documentation"
Task: "Copy quickstart guide"
```
**Rationale**: Different files, no dependencies, can run simultaneously

### Example 2: Add Tables to Space (T009-T010)
```
# Launch T009-T010 together after T008:
Task: "Add core inventory tables to Genie space"
Task: "Add supporting dimension tables to Genie space"
```
**Rationale**: Different table groups, no dependencies between them

### Example 3: Basic Query Testing (T013-T014, T016-T018)
```
# Launch after T012 completes:
Task: "Test simple query: Current stock status"
Task: "Test medium complexity query: Stockout risk"
Task: "Test error handling: Ambiguous query"
Task: "Test error handling: Future date query"
Task: "Test error handling: Non-existent location"
```
**Rationale**: Different query types, independent test scenarios

### Example 4: Documentation Tasks (T024-T027)
```
# Launch after testing completes:
Task: "Create README for configuration directory"
Task: "Document table access permissions"
Task: "Update main README (if applicable)"
Task: "Commit configuration artifacts to version control"
```
**Rationale**: Different documentation files, can be written in parallel

## Notes
- **[P] tasks** = different files, no dependencies
- **Sequential tasks** = same Genie space configuration, must run in order
- **Testing order**: Simple queries first, then complex, then error handling, then multi-domain detection
- **Verification**: After each configuration step, verify it was applied correctly
- **Commit**: Commit configuration artifacts after copying, commit documentation after completion
- **Avoid**: Applying configuration before verifying table comments exist
- **Avoid**: Testing before configuration is complete

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - `genie_instructions.md` → Copy task (T004)
   - `sample_queries.md` → Copy task (T005)
   
2. **From Data Model**:
   - Table comment verification → Prerequisite tasks (T001-T002)
   - Table relationships → Add tables tasks (T009-T010)
   
3. **From Quickstart Guide**:
   - Each step → Configuration task
   - Verification steps → Testing tasks
   - Troubleshooting → Documentation notes

4. **From User Stories**:
   - Each acceptance scenario → Test task (T013-T022)
   - Error handling scenarios → Test tasks (T016-T018)
   - Multi-domain detection → Test tasks (T019-T020)

5. **Ordering**:
   - Setup → Copy Artifacts → Create Space → Configure → Test → Document
   - Dependencies block parallel execution
   - Testing comes after configuration is complete

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All configuration artifacts have copy tasks
- [x] All quickstart steps have corresponding tasks
- [x] All acceptance scenarios have test tasks
- [x] All error handling scenarios have test tasks
- [x] Table comment verification comes before space creation
- [x] Configuration comes before testing
- [x] Parallel tasks truly independent (different files)
- [x] Each task specifies exact file path or action
- [x] No task modifies same Genie space configuration as another [P] task

---

**Task Generation Complete**: 28 tasks ready for execution, covering setup, configuration, validation, and documentation phases.

