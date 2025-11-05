# Tasks: Customer Behavior Genie Room Configuration

**Input**: Design documents from `/specs/003-cutomer-behavior-genie/`
**Prerequisites**: plan.md, research.md, data-model.md

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Implementation plan loaded successfully
   → Project Type: Configuration and Documentation (no code implementation)
2. Load optional design documents:
   → data-model.md: Loaded - contains entities and data structures
   → research.md: Loaded - Genie configuration best practices
   → contracts/: Directory exists but empty - needs configuration artifacts
3. Generate tasks by category:
   → Setup: Directory structure, configuration artifact templates
   → Documentation: Data model docs, Genie instructions, sample queries
   → Configuration: Organize and format artifacts
   → Validation: Test configuration, validate improvements
   → Polish: Documentation updates, quickstart guide
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Documentation before configuration
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All configuration artifacts created?
   → All functional requirements covered in sample queries?
   → Validation tests created?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Configuration artifacts**: `10-genie-rooms/genie-configs/customer-behavior/`
- **Specs documentation**: `specs/003-cutomer-behavior-genie/contracts/`
- **Test notebooks**: `10-genie-rooms/notebooks/`

## Phase 3.1: Setup
- [x] T001 Create directory structure for Genie configuration artifacts
  - Create `10-genie-rooms/genie-configs/customer-behavior/` directory
  - Create subdirectories if needed for organization
  - Ensure directory structure matches plan.md structure

## Phase 3.2: Documentation Creation (Can be parallel)
- [x] T002 [P] Revise data-model.md for Genie space understanding
  - File: `specs/003-cutomer-behavior-genie/data-model.md`
  - Focus on customer behavior tables and schemas accessible to Genie
  - Document key tables: gold_customer_dim, gold_sales_fact, gold_cart_abandonment_fact, gold_customer_product_affinity_agg
  - Include table relationships and join patterns
  - Document key metrics and calculations (CLTV, abandonment rate, RFM scores)
  - Add data quality notes and constraints
  - Reference existing data model from `00-data/README.md` and `specs/001-i-want-to/data-model.md`

- [x] T003 [P] Create Genie instructions document
  - File: `specs/003-cutomer-behavior-genie/contracts/genie_instructions.md`
  - Include domain overview: Customer behavior analysis context
  - Document available data: Tables, schemas, key metrics
  - Define query patterns: Common analytical patterns to recognize
  - Response guidelines: How to structure answers with insights and recommendations (FR-012, FR-020)
  - Error handling: How to provide specific errors with actionable guidance (FR-022)
  - Performance guidelines: Query optimization for medium-scale data (1-10M rows, FR-018)
  - Boundaries: Multi-domain query detection and redirection (FR-021)
  - Use examples within instructions to illustrate concepts
  - Reference functional requirements to guide behavior

- [x] T004 [P] Create sample queries document organized by category
  - File: `specs/003-cutomer-behavior-genie/contracts/sample_queries.md`
  - Organize by analytical category from README.genie.customer-behavior.md:
    - Customer Segmentation & Value (FR-002, FR-008)
    - Purchase Patterns & RFM Analysis (FR-009, FR-010)
    - Product & Category Affinity (FR-003, FR-005)
    - Channel Behavior & Migration (FR-006)
    - Engagement & Funnel Analysis (FR-007)
    - Abandonment & Recovery (FR-004)
    - Personalization & Affinity Impact (FR-011)
  - Cover all 12 acceptance scenarios from spec.md
  - Include queries for each functional requirement (FR-001 through FR-022)
  - Group by complexity: Simple, Medium, Complex
  - Include expected insights/response patterns for each query
  - Add multi-domain detection test queries (should redirect per FR-021)
  - Include edge case queries (ambiguous, data quality, no results)

## Phase 3.3: Configuration Artifacts Organization
- [x] T005 Copy and organize configuration artifacts to genie-configs directory
  - Copy `contracts/genie_instructions.md` → `10-genie-rooms/genie-configs/customer-behavior/instructions.md`
  - Copy `contracts/sample_queries.md` → `10-genie-rooms/genie-configs/customer-behavior/sample_queries.md`
  - Copy revised `data-model.md` → `10-genie-rooms/genie-configs/customer-behavior/data_model.md`
  - Ensure formatting is suitable for Genie space configuration UI
  - Verify all files are properly formatted and readable

- [x] T006 Create quickstart guide for applying configuration
  - File: `specs/003-cutomer-behavior-genie/quickstart.md`
  - Step-by-step guide for applying configuration via Databricks UI
  - UI navigation instructions for Genie space configuration
  - Instructions for adding instructions to Genie space
  - Instructions for adding sample queries to Genie space
  - Instructions for adding data model documentation
  - Validation checklist: How to verify configuration was applied correctly
  - Reference Genie space ID: `01f09cdbacf01b5fa7ff7c237365502c`

## Phase 3.4: Validation and Testing
- [x] T007 [P] Create test notebook for configuration validation
  - File: `10-genie-rooms/notebooks/test-genie-configuration.ipynb`
  - Test all sample queries return valid responses
  - Verify responses include actionable insights (FR-012, FR-020)
  - Test error scenarios return specific guidance (FR-022)
  - Validate multi-domain query detection (FR-021)
  - Performance validation: Verify queries meet targets (<10s simple, <60s complex per FR-018)
  - Use existing test utilities from `src/fashion_retail/agents/genie/test_utils.py`
  - Document expected responses for sample queries
  - Track quality metrics before/after configuration

- [x] T008 [P] Create validation test cases document
  - File: `specs/003-cutomer-behavior-genie/contracts/validation_tests.md`
  - Test cases for each sample query category
  - Validation criteria for response quality
  - Performance benchmarks (<10s simple, <60s complex)
  - Error handling validation scenarios
  - Multi-domain detection test cases
  - Expected response patterns for each query type

## Phase 3.5: Polish and Documentation
- [x] T009 Update README.genie.customer-behavior.md with configuration guide
  - File: `10-genie-rooms/README.genie.customer-behavior.md`
  - Add section on Genie space configuration
  - Link to configuration artifacts in genie-configs/
  - Reference quickstart.md for application steps
  - Update examples section with sample queries reference
  - Add configuration validation section

- [x] T010 [P] Create configuration summary document
  - File: `specs/003-cutomer-behavior-genie/contracts/configuration_summary.md`
  - Summary of all configuration artifacts created
  - Mapping of functional requirements to sample queries
  - Mapping of functional requirements to instruction sections
  - Configuration application checklist
  - Before/after comparison guide

- [x] T011 Final validation and documentation review
  - Review all configuration artifacts for completeness
  - Verify all functional requirements (FR-001 through FR-022) are addressed
  - Ensure all acceptance scenarios have corresponding sample queries
  - Verify error handling guidance is comprehensive (FR-022)
  - Confirm multi-domain detection is documented (FR-021)
  - Check that performance guidelines are clear (FR-018)
  - Review quickstart.md for accuracy and clarity

## Dependencies
- T001 (Setup) before all documentation tasks (T002-T004)
- T002-T004 (Documentation) can run in parallel [P]
- T002-T004 must complete before T005 (Configuration organization)
- T005 must complete before T006 (Quickstart guide)
- T002-T004 must complete before T007-T008 (Validation)
- T005-T006 must complete before T009-T010 (Polish)
- T007-T008 (Validation) can run in parallel [P]
- T009-T010 (Polish) can run in parallel [P]
- All tasks must complete before T011 (Final validation)

## Parallel Execution Examples

**Example 1: Documentation Creation (T002-T004)**
```
# Launch T002-T004 together:
Task: "Revise data-model.md for Genie space understanding"
Task: "Create Genie instructions document"
Task: "Create sample queries document organized by category"
```

**Example 2: Validation Tasks (T007-T008)**
```
# Launch T007-T008 together:
Task: "Create test notebook for configuration validation"
Task: "Create validation test cases document"
```

**Example 3: Polish Tasks (T009-T010)**
```
# Launch T009-T010 together:
Task: "Update README.genie.customer-behavior.md with configuration guide"
Task: "Create configuration summary document"
```

## Task Details

### T001: Create Directory Structure
**File**: `10-genie-rooms/genie-configs/customer-behavior/`
**Description**: Create the directory structure for storing Genie configuration artifacts. This matches the structure defined in plan.md.

**Steps**:
1. Create `10-genie-rooms/genie-configs/` directory
2. Create `10-genie-rooms/genie-configs/customer-behavior/` subdirectory
3. Verify directory structure matches plan.md project structure

### T002: Revise Data Model Documentation
**File**: `specs/003-cutomer-behavior-genie/data-model.md`
**Description**: Revise the existing data-model.md to focus on Genie space understanding. Document customer behavior tables, relationships, and metrics that Genie needs to know about.

**Key Sections**:
- Customer behavior tables (gold_customer_dim, gold_sales_fact, gold_cart_abandonment_fact, etc.)
- Table relationships and join patterns
- Key metrics and calculations (CLTV, abandonment rate, RFM)
- Data quality notes
- Time periods and temporal granularity

**References**:
- `00-data/README.md` for full schema
- `specs/001-i-want-to/data-model.md` for inventory alignment details
- Existing `specs/003-cutomer-behavior-genie/data-model.md` (needs revision)

### T003: Create Genie Instructions
**File**: `specs/003-cutomer-behavior-genie/contracts/genie_instructions.md`
**Description**: Create comprehensive instructions for the Genie space that guide it on customer behavior domain analysis.

**Required Sections**:
1. **Domain Overview**: Customer behavior analysis context and terminology
2. **Available Data**: Tables, schemas, and key metrics available
3. **Query Patterns**: Common analytical patterns (segmentation, RFM, funnel analysis, etc.)
4. **Response Guidelines**: Structure answers with insights and recommendations (FR-012, FR-020)
5. **Error Handling**: Provide specific errors with actionable guidance (FR-022)
6. **Performance Guidelines**: Query optimization for 1-10M rows (FR-018)
7. **Boundaries**: Multi-domain query detection and redirection (FR-021)

**Requirements**:
- Clear and concise (avoid overloading)
- Use examples to illustrate concepts
- Reference functional requirements
- Balance detail with readability

### T004: Create Sample Queries Document
**File**: `specs/003-cutomer-behavior-genie/contracts/sample_queries.md`
**Description**: Create organized sample queries covering all functional requirements and acceptance scenarios.

**Organization**:
- By analytical category (from README.genie.customer-behavior.md):
  - Customer Segmentation & Value
  - Purchase Patterns & RFM Analysis
  - Product & Category Affinity
  - Channel Behavior & Migration
  - Engagement & Funnel Analysis
  - Abandonment & Recovery
  - Personalization & Affinity Impact
- By complexity: Simple, Medium, Complex
- Include expected insights/response patterns

**Coverage Requirements**:
- All 12 acceptance scenarios from spec.md
- All functional requirements (FR-001 through FR-022)
- Edge cases (ambiguous queries, data quality issues, no results)
- Multi-domain detection test queries (should redirect)

**Example Queries** (from spec.md acceptance scenarios):
1. "What products are trending?"
2. "Which products or categories are at risk of stockout or overstock?"
3. "Through which channels do customers prefer to shop?"
4. "Which segments respond best to personalization?"
5. "What are the key customer segments, and how do their lifetime values differ?"
6. "Which customers are at risk of churning, and which are the most loyal?"
7. "What is the rate of cart abandonment, and how effective are recovery campaigns?"
8. "Which product categories are most often purchased together?"
9. "What are the conversion rates at each stage of the engagement funnel?"
10. "How do customers migrate between acquisition and preferred channels over time?"
11. Follow-up questions (e.g., "What about their demographics?")
12. Permission error scenarios

### T005: Copy and Organize Configuration Artifacts
**File**: `10-genie-rooms/genie-configs/customer-behavior/`
**Description**: Copy configuration artifacts from specs directory to genie-configs directory for easy access.

**Files to Copy**:
- `contracts/genie_instructions.md` → `genie-configs/customer-behavior/instructions.md`
- `contracts/sample_queries.md` → `genie-configs/customer-behavior/sample_queries.md`
- Revised `data-model.md` → `genie-configs/customer-behavior/data_model.md`

**Requirements**:
- Ensure formatting suitable for Genie space configuration UI
- Verify all files are properly formatted and readable
- Maintain version control in specs directory

### T006: Create Quickstart Guide
**File**: `specs/003-cutomer-behavior-genie/quickstart.md`
**Description**: Create step-by-step guide for applying configuration to Genie space via Databricks UI.

**Required Sections**:
1. Prerequisites (Genie space access, permissions)
2. Step-by-step UI navigation
3. Instructions for adding instructions to Genie space
4. Instructions for adding sample queries
5. Instructions for adding data model documentation
6. Validation checklist
7. Troubleshooting tips

**Reference**: Genie space ID `01f09cdbacf01b5fa7ff7c237365502c`

### T007: Create Test Notebook
**File**: `10-genie-rooms/notebooks/test-genie-configuration.ipynb`
**Description**: Create Databricks notebook for validating Genie configuration improvements.

**Test Cases**:
- Test all sample queries return valid responses
- Verify responses include actionable insights (FR-012, FR-020)
- Test error scenarios return specific guidance (FR-022)
- Validate multi-domain query detection (FR-021)
- Performance validation (<10s simple, <60s complex per FR-018)

**Implementation**:
- Use existing test utilities from `src/fashion_retail/agents/genie/test_utils.py`
- Document expected responses for sample queries
- Track quality metrics before/after configuration

### T008: Create Validation Test Cases
**File**: `specs/003-cutomer-behavior-genie/contracts/validation_tests.md`
**Description**: Document validation test cases and criteria for configuration quality.

**Required Sections**:
1. Test cases for each sample query category
2. Validation criteria for response quality
3. Performance benchmarks
4. Error handling validation scenarios
5. Multi-domain detection test cases
6. Expected response patterns

### T009: Update README
**File**: `10-genie-rooms/README.genie.customer-behavior.md`
**Description**: Update existing README with configuration guide and references.

**Additions**:
- Section on Genie space configuration
- Link to configuration artifacts
- Reference to quickstart.md
- Configuration validation section

### T010: Create Configuration Summary
**File**: `specs/003-cutomer-behavior-genie/contracts/configuration_summary.md`
**Description**: Create summary document mapping requirements to configuration artifacts.

**Required Sections**:
1. Summary of all configuration artifacts
2. Mapping: FR-001 through FR-022 → Sample queries
3. Mapping: FR-001 through FR-022 → Instruction sections
4. Configuration application checklist
5. Before/after comparison guide

### T011: Final Validation
**Description**: Review all artifacts for completeness and accuracy.

**Checklist**:
- [ ] All functional requirements addressed
- [ ] All acceptance scenarios have sample queries
- [ ] Error handling guidance comprehensive
- [ ] Multi-domain detection documented
- [ ] Performance guidelines clear
- [ ] Quickstart guide accurate
- [ ] All files properly formatted

## Notes
- [P] tasks = different files, no dependencies
- Configuration artifacts are documentation, not code
- All artifacts should be human-readable and suitable for Genie UI
- Maintain version control in specs directory
- Configuration applied via Databricks Genie UI

## Task Generation Rules
*Applied during main() execution*

1. **From Plan**:
   - Configuration artifacts → creation tasks [P]
   - Documentation → creation tasks [P]
   
2. **From Spec**:
   - Functional requirements → sample queries
   - Acceptance scenarios → sample queries
   - Edge cases → error handling guidance
   
3. **Ordering**:
   - Setup → Documentation → Configuration → Validation → Polish
   - Documentation can be parallel [P]
   - Validation can be parallel [P]

## Validation Checklist
*GATE: Checked before returning*

- [x] All configuration artifacts have creation tasks
- [x] All functional requirements mapped to sample queries
- [x] Documentation tasks come before configuration
- [x] Parallel tasks truly independent
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Validation tests created for configuration quality

