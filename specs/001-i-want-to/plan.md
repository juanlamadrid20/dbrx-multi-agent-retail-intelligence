
# Implementation Plan: Align Customer Behavior Synthetic Data with Real-Time Inventory Data

**Branch**: `001-i-want-to` | **Date**: 2025-10-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-i-want-to/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 8. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

This feature addresses the critical need to align synthetic customer behavior data generation with real-time inventory levels in the Databricks multi-agent retail intelligence system. Currently, the `00-data` directory generates customer transactions and inventory snapshots independently, leading to unrealistic scenarios where customers purchase out-of-stock items. The solution will refactor the synthetic data generators to enforce inventory constraints, implement realistic stockout patterns (5-10% of product-location-day combinations), handle returns with 1-3 day delays, and increase cart abandonment rates by 10 percentage points during low-inventory scenarios.

## Technical Context

**Language/Version**: Python 3.11+ (Databricks Runtime compatible)
**Primary Dependencies**: PySpark 3.5+, Delta Lake, Databricks SDK
**Storage**: Delta Tables in Unity Catalog (catalog: juan_dev, schema: retail)
**Testing**: pytest with PySpark test fixtures
**Target Platform**: Databricks workspace (cloud-based Spark environment)
**Project Type**: Single data pipeline project
**Performance Goals**: Generate 100K+ customer records, 10K+ products, 730 days of historical data with inventory-aligned transactions
**Constraints**: Daily granularity for inventory snapshots, memory-efficient batch processing for large-scale data generation
**Scale/Scope**: Fashion retail star schema with 5 dimension tables, 5 fact tables, 3 aggregate tables

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: The project constitution template is unpopulated. Proceeding with standard best practices:

### ✅ Code Quality Gates
- [ ] All code changes include unit tests (TDD approach)
- [ ] Integration tests for data generation pipeline
- [ ] Contract tests for Delta table schemas
- [ ] Documentation for new functions and modules

### ✅ Data Engineering Best Practices
- [ ] Delta table schema evolution handled properly
- [ ] Idempotent data generation (reproducible with seed)
- [ ] Batch processing for memory efficiency
- [ ] Data validation checks post-generation

### ✅ Databricks-Specific
- [ ] Unity Catalog integration maintained
- [ ] Spark optimization (broadcast joins, partitioning)
- [ ] Logging and observability for long-running jobs

## Project Structure

### Documentation (this feature)
```
specs/001-i-want-to/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
00-data/
├── fashion-retail-main.py                    # UPDATED: Add inventory alignment config params
├── fashion-retail-dimension-generator.py     # NO CHANGES NEEDED
├── fashion-retail-fact-generator.py          # MAJOR REFACTOR: Lines 114-358
│   ├── __init__ (lines 16-30)                # UPDATED: Add inventory_manager, sales_validator
│   ├── create_sales_fact (lines 114-263)     # REFACTOR: Validate against inventory before sale
│   ├── create_inventory_fact (lines 276-358) # REFACTOR: Track state, reflect sales deductions
│   └── _write_batch                          # UPDATED: Reduce batch size to 50K
├── fashion-retail-aggregates.py              # MINIMAL: Handle new stockout event data
├── fashion-retail-notebook.py                # UPDATED: Add inventory validation params
├── inventory_manager.py                      # NEW: 200 lines - Inventory state tracking
├── sales_validator.py                        # NEW: 150 lines - Purchase validation logic
└── stockout_generator.py                     # NEW: 100 lines - Stockout event generation

tests/
├── contract/
│   ├── test_inventory_snapshot_schema.py     # NEW: Validate is_stockout, stockout_duration_days columns
│   ├── test_sales_fact_schema.py             # NEW: Validate quantity_requested, is_inventory_constrained
│   └── test_stockout_event_schema.py         # NEW: Validate new table schema
├── integration/
│   ├── test_inventory_sales_alignment.py     # NEW: End-to-end validation
│   ├── test_stockout_frequency.py            # NEW: Validate 5-10% rate
│   └── test_return_processing.py             # NEW: Validate 1-3 day delays
└── unit/
    ├── test_inventory_manager.py             # NEW: Test state tracking logic
    ├── test_sales_validator.py               # NEW: Test random allocation
    └── test_stockout_generator.py            # NEW: Test stockout detection
```

**Structure Decision**: Enhance existing `00-data/` directory with inventory alignment. **CRITICAL FINDING**: Current implementation generates sales and inventory **completely independently** (see `fashion-retail-fact-generator.py` lines 114-358). Sales generation (line 212) uses `quantity = random.choice([1, 2, 3])` with NO inventory checks. Inventory generation (lines 276-358) creates random snapshots with NO deduction from sales. This is the core problem to fix.

## Phase 0: Outline & Research

**Status**: Ready to execute

### Research Tasks

1. **PySpark Stateful Processing Patterns**
   - Research: Best practices for maintaining inventory state across date iterations
   - Key question: How to efficiently track inventory levels for 10K products × 13 locations × 730 days
   - Output: Recommended approach (in-memory dict, broadcast variables, or Delta merge)

2. **Delta Lake Schema Evolution**
   - Research: How to add new columns to existing fact tables without breaking downstream consumers
   - Key question: Adding `stockout_flag`, `lost_sales_qty` columns to sales_fact
   - Output: Migration strategy and backwards compatibility approach

3. **Randomization with Constraints**
   - Research: Algorithms for random allocation with inventory caps
   - Key question: How to randomly distribute limited inventory among competing purchase attempts
   - Output: Algorithm (reservoir sampling, weighted selection, or simple shuffle)

4. **Testing Databricks Workflows**
   - Research: Best practices for testing PySpark code locally vs. on Databricks
   - Key question: How to write tests that run both in pytest (local) and Databricks notebooks
   - Output: Testing framework setup and fixtures

5. **Performance Optimization**
   - Research: Memory-efficient batch writing for 100K+ transaction records
   - Key question: Optimal batch size for Delta writes (current: 100K)
   - Output: Performance tuning recommendations

**Output**: research.md with all findings consolidated

## Phase 1: Design & Contracts

**Status**: Pending Phase 0 completion

### Planned Outputs

1. **data-model.md**: Enhanced entity definitions
   - Inventory Snapshot (updated with real-time tracking fields)
   - Sales Transaction (updated with inventory validation flags)
   - Stockout Event (new entity)
   - Cart Abandonment Event (updated with inventory correlation)
   - Inventory Movement (updated with return delay tracking)

2. **contracts/**: Delta table schema definitions
   - `gold_inventory_fact.json`: Updated schema with stockout tracking
   - `gold_sales_fact.json`: Updated schema with validation flags
   - `gold_stockout_events.json`: New table schema
   - `gold_cart_abandonment_fact.json`: Updated schema with inventory triggers

3. **quickstart.md**: Validation workflow
   - Step 1: Run data generation with seed=42
   - Step 2: Validate stockout rate (should be 5-10%)
   - Step 3: Validate inventory consistency (no negative quantities)
   - Step 4: Validate return delays (1-3 days)
   - Step 5: Validate cart abandonment correlation

4. **Agent Context**: CLAUDE.md (incremental update)
   - Add: PySpark stateful processing patterns
   - Add: Delta Lake inventory management approach
   - Add: Testing strategy for Databricks pipelines

## Phase 2: Task Planning Approach

**This section describes what the /tasks command will do - DO NOT execute during /plan**

### Task Generation Strategy

Tasks will be generated following TDD principles with dependency ordering:

**Contract Tests First** (Parallel execution possible):
1. Write schema contract test for updated `gold_inventory_fact`
2. Write schema contract test for updated `gold_sales_fact`
3. Write schema contract test for new `gold_stockout_events`
4. Write schema contract test for updated `gold_cart_abandonment_fact`

**Unit Tests & Implementation** (Sequential by module):
5. Write unit tests for InventoryManager class
6. Implement InventoryManager (track inventory state, handle depletion/replenishment)
7. Write unit tests for SalesValidator class
8. Implement SalesValidator (validate purchases against inventory, random allocation)
9. Write unit tests for StockoutGenerator class
10. Implement StockoutGenerator (generate stockout events, track lost sales)

**Integration Tests** (Sequential, depends on implementations):
11. Write integration test for inventory-sales alignment
12. Write integration test for stockout frequency (5-10% validation)
13. Write integration test for return processing delays (1-3 days)
14. Write integration test for cart abandonment rate increase (10pp)

**Refactor Existing Generators** (Sequential):
15. Refactor FactGenerator.create_sales_fact() to use SalesValidator
16. Refactor FactGenerator.create_inventory_fact() to use InventoryManager
17. Refactor FactGenerator.create_cart_abandonment_fact() to correlate with inventory
18. Update AggregateGenerator to handle new stockout data

**Pipeline Integration** (Sequential):
19. Update fashion-retail-main.py to wire new components
20. Update fashion-retail-notebook.py for notebook execution
21. Add data validation checks post-generation

**Documentation & Quickstart**:
22. Create quickstart.md validation workflow
23. Update README with new data alignment features

### Ordering Strategy

- **TDD First**: All tests written before implementations
- **Dependency Order**: Models → Validators → Generators → Pipeline
- **Parallel Markers [P]**: Independent schema tests and unit tests can run in parallel
- **Sequential Integration**: Integration tests run after all implementations complete

### Estimated Output

23 numbered, dependency-ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation

**These phases are beyond the scope of the /plan command**

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following TDD and constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, verify 5-10% stockout rate, validate performance)

## Complexity Tracking

**No constitutional violations detected**. The approach follows standard data engineering best practices:
- Modular design (separate concerns: inventory tracking, sales validation, stockout generation)
- Test-first development (contract → unit → integration tests)
- Delta Lake best practices (schema evolution, batch writes, idempotency)
- No unnecessary abstractions or patterns

## Progress Tracking

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) ✅
- [x] Phase 1: Design complete (/plan command) ✅
- [x] Phase 2: Task planning complete (/plan command - describe approach only) ✅
- [x] Phase 3: Tasks generated (/tasks command) ✅ - 28 tasks ready for execution
- [ ] Phase 4: Implementation complete (execute tasks.md)
- [ ] Phase 5: Validation passed (run quickstart.md)

**Gate Status**:
- [x] Initial Constitution Check: PASS (best practices applied, no violations) ✅
- [x] Post-Design Constitution Check: PASS (modular design, no unnecessary abstractions) ✅
- [x] All NEEDS CLARIFICATION resolved (via /clarify session 2025-10-06) ✅
- [x] Complexity deviations documented: N/A ✅

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
