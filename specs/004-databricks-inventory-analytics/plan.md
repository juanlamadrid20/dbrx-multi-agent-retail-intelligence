
# Implementation Plan: Databricks Inventory Analytics Genie Room Implementation

**Branch**: `004-databricks-inventory-analytics` | **Date**: 2025-01-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-databricks-inventory-analytics/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → Feature spec loaded successfully
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → No NEEDS CLARIFICATION markers found
   → Project Type: Genie Space Configuration (documentation and configuration artifacts)
3. Fill the Constitution Check section based on the content of the constitution document.
   → Constitution check completed - no violations
4. Evaluate Constitution Check section below
   → ✅ PASS - No violations detected
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → Research completed - Genie configuration best practices identified
6. Execute Phase 1 → contracts, data-model.md, quickstart.md
   → Design artifacts generated (configuration artifacts, not code)
7. Re-evaluate Constitution Check section
   → ✅ PASS - Post-design check confirms no violations
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
   → Task planning approach documented
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Improve the Inventory Analytics Genie room quality by implementing best practices: comprehensive instructions, organized sample queries covering all functional requirements, and configuration guidance. The goal is to enhance Genie's understanding of the inventory analytics domain, improve query response quality, and provide better user guidance - all through Genie space configuration and automatic schema discovery, not code implementation.

## Technical Context
**Language/Version**: Markdown, YAML, JSON (configuration artifacts)
**Primary Dependencies**: 
- Databricks Genie space configuration UI
- Inventory tables in `juan_dev.retail` schema (gold_inventory_fact, gold_stockout_events, gold_inventory_movement_fact)
- Automatic schema discovery (tables must have proper comments/descriptions)
- Documentation from `specs/001-i-want-to/data-model.md` and `DATA_MODEL_ALIGNMENT.md`
**Storage**: 
- Configuration artifacts in `10-genie-rooms/genie-configs/inventory-analytics/` directory
- Applied to Genie space via Databricks UI
- Tables rely on automatic schema discovery (no explicit data model docs needed)
**Testing**: pytest (validate configuration artifacts), Genie test utilities for query validation
**Target Platform**: Databricks workspace (Genie space configuration)
**Project Type**: Configuration and Documentation (no code implementation)
**Performance Goals**: 
- Improved query accuracy and response quality
- Better error handling with actionable guidance
- Query response times: <10s simple, <60s complex (via Genie optimization)
**Constraints**: 
- Configuration via Databricks UI (primary method)
- Must align with existing Genie space capabilities
- Must respect Unity Catalog permissions
- Must maintain session-based conversation context
- Automatic schema discovery (no explicit data model documentation)
- English-only queries
- No forecasting capabilities
**Scale/Scope**: Single Genie space configuration, extensible pattern for other inventory domains

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Initial Check (Pre-Research)**:
- ✅ **Documentation-First**: Configuration artifacts are documentation, not code
- ✅ **Reuse Existing**: Leverages existing inventory data model and test utilities
- ✅ **No Over-Engineering**: Configuration improvements only, no custom code
- ✅ **Testability**: Configuration can be validated via existing Genie test utilities
- ✅ **Simplicity**: Documentation-based approach, applied via UI with automatic schema discovery

**Post-Design Check (Post-Phase 1)**:
- ✅ **Clear Structure**: Configuration artifacts well-organized by analytical category
- ✅ **Comprehensive Coverage**: All functional requirements addressed in sample queries
- ✅ **Actionable Guidance**: Instructions provide clear guidance for Genie
- ✅ **No Code Complexity**: Pure configuration/documentation artifacts
- ✅ **Validation Path**: Clear testing approach for configuration validation

**Complexity Assessment**: ✅ No constitutional violations
- Configuration-only approach is appropriate and simple
- No code implementation needed
- Documentation artifacts are maintainable and version-controlled
- Automatic schema discovery simplifies configuration (no manual data model docs)

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Configuration Artifacts (applied to Genie space)
```
10-genie-rooms/
├── genie-configs/
│   └── inventory-analytics/          # NEW - Configuration artifacts
│       ├── instructions.md           # Genie space instructions
│       └── sample_queries.md         # Sample queries by category
└── notebooks/
    └── test-genie-configuration.ipynb # EXISTING - Can be reused/adapted
```

**Structure Decision**: Configuration artifacts live in `10-genie-rooms/genie-configs/inventory-analytics/` for easy access and application. Documentation in specs directory for planning/tracking. Applied via Databricks Genie space configuration UI. Tables rely on automatic schema discovery (no explicit data model documentation in genie-configs).

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - All technical decisions resolved - Genie configuration best practices identified
   - No NEEDS CLARIFICATION markers in spec

2. **Research Findings** (see `research.md` for details):
   - Genie room configuration best practices for inventory analytics
   - Sample query organization by analytical category
   - Instructions structure for domain guidance
   - Automatic schema discovery approach (no explicit data model docs needed)
   - Configuration methods (UI-based)
   - Testing and validation approach

3. **Consolidate findings** in `research.md`:
   - Decision: Configuration-only approach (no code implementation)
   - Rationale: Improve Genie room quality through best practices with automatic schema discovery
   - Alternatives considered: Explicit data model documentation (rejected - clarification determined automatic schema discovery is sufficient)

**Output**: research.md with all technical decisions resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract data model from existing documentation** → `data-model.md`:
   - Inventory analytics tables and schemas (reference documentation)
   - Key metrics and calculations
   - Table relationships and join patterns
   - Data quality notes
   - Automatic schema discovery requirements (table comments)

2. **Generate configuration artifacts**:
   - **Genie Instructions** (`contracts/genie_instructions.md`): Comprehensive instructions for Genie space
   - **Sample Queries** (`contracts/sample_queries.md`): Organized by category, covering all FRs (FR-001 to FR-024)
   - **Data Model Reference**: Documentation for reference (Genie uses automatic schema discovery)

3. **Generate validation tests**:
   - Test cases for sample queries
   - Validation criteria for response quality
   - Error handling test scenarios
   - Multi-domain detection tests

4. **Extract test scenarios** from user stories:
   - Each acceptance scenario → integration test scenario
   - Quickstart test = configuration validation steps

5. **Generate quickstart guide**:
   - Step-by-step configuration instructions
   - Table comment verification steps
   - Configuration application steps
   - Testing and validation steps

**Output**: data-model.md, /contracts/*, quickstart.md, validation approach documented

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each configuration artifact → configuration task
- Each sample query category → validation test task
- Each quickstart step → configuration step task
- Testing and validation tasks

**Ordering Strategy**:
- Prerequisites first: Table comment verification
- Configuration tasks: Instructions, sample queries
- Validation tasks: Test sample queries, error handling, multi-domain detection
- Documentation tasks: User documentation, configuration guide updates

**Estimated Output**: 15-20 numbered, ordered tasks in tasks.md covering:
- Table comment verification and updates
- Genie space creation and configuration
- Instructions and sample queries application
- Testing and validation
- Documentation updates

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [x] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none - configuration-only approach)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
