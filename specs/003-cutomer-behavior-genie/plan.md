# Implementation Plan: Customer Behavior Genie Room Configuration

**Branch**: `003-cutomer-behavior-genie` | **Date**: 2025-11-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-cutomer-behavior-genie/spec.md`

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
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file
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
Improve the Customer Behavior Genie room quality by implementing best practices: comprehensive instructions, organized sample queries covering all functional requirements, data model documentation, and configuration guidance. The goal is to enhance Genie's understanding of the customer behavior domain, improve query response quality, and provide better user guidance - all through Genie space configuration, not code implementation.

## Technical Context
**Language/Version**: Markdown, YAML, JSON (configuration artifacts)
**Primary Dependencies**: 
- Databricks Genie space configuration UI
- Existing Genie space: `01f09cdbacf01b5fa7ff7c237365502c`
- Documentation from `10-genie-rooms/README.genie.customer-behavior.md`
**Storage**: 
- Configuration artifacts in `10-genie-rooms/` directory
- Applied to Genie space via Databricks UI
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
**Scale/Scope**: Single Genie space configuration, extensible pattern for other domains

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Initial Check (Pre-Research)**:
- ✅ **Documentation-First**: Configuration artifacts are documentation, not code
- ✅ **Reuse Existing**: Leverages existing README and test utilities
- ✅ **No Over-Engineering**: Configuration improvements only, no custom code
- ✅ **Testability**: Configuration can be validated via existing Genie test utilities
- ✅ **Simplicity**: Documentation-based approach, applied via UI

**Post-Design Check (Post-Phase 1)**:
- ✅ **Clear Structure**: Configuration artifacts well-organized by category
- ✅ **Comprehensive Coverage**: All functional requirements addressed in sample queries
- ✅ **Actionable Guidance**: Instructions provide clear guidance for Genie
- ✅ **No Code Complexity**: Pure configuration/documentation artifacts
- ✅ **Validation Path**: Clear testing approach for configuration validation

**Complexity Assessment**: ✅ No constitutional violations
- Configuration-only approach is appropriate and simple
- No code implementation needed
- Documentation artifacts are maintainable and version-controlled

## Project Structure

### Documentation (this feature)
```
specs/003-cutomer-behavior-genie/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output - Customer behavior data model
├── quickstart.md        # Phase 1 output - Configuration guide
├── contracts/           # Phase 1 output - Configuration artifacts
│   ├── genie_instructions.md      # Instructions for Genie space
│   ├── sample_queries.md           # Organized sample queries
│   └── genie_config.yaml          # Configuration schema (optional)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Configuration Artifacts (applied to Genie space)
```
10-genie-rooms/
├── README.genie.customer-behavior.md  # EXISTING - Enhanced with configuration guide
├── genie-configs/                     # NEW - Configuration artifacts
│   └── customer-behavior/
│       ├── instructions.md            # Genie space instructions
│       ├── sample_queries.md          # Sample queries by category
│       └── data_model.md              # Data model documentation
└── notebooks/
    └── test-genie-configuration.ipynb # NEW - Configuration validation tests
```

**Structure Decision**: Configuration artifacts live in `10-genie-rooms/genie-configs/` for easy access and application. Documentation in specs directory for planning/tracking. Applied via Databricks Genie space configuration UI.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - All technical decisions resolved - Genie configuration best practices identified
   - No NEEDS CLARIFICATION markers in spec

2. **Research Findings** (see `research.md` for details):
   - Genie room configuration best practices
   - Sample query organization by analytical category
   - Instructions structure for domain guidance
   - Data model documentation approach
   - Configuration methods (UI-based)
   - Testing and validation approach

3. **Consolidate findings** in `research.md`:
   - Decision: Configuration-only approach (no code implementation)
   - Rationale: Improve Genie room quality through best practices
   - Alternatives considered: UC Function wrapper (rejected - not the goal)

**Output**: research.md with all technical decisions resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract data model from existing documentation** → `data-model.md`:
   - Customer behavior tables and schemas
   - Key metrics and calculations
   - Table relationships and join patterns
   - Data quality notes

2. **Generate configuration artifacts**:
   - **Genie Instructions** (`contracts/genie_instructions.md`): Comprehensive instructions for Genie space
   - **Sample Queries** (`contracts/sample_queries.md`): Organized by category, covering all FRs
   - **Data Model Documentation**: Reference for Genie understanding

3. **Generate validation tests**:
   - Test cases for sample queries
   - Validation criteria for response quality
   - Performance benchmarks
   - Error handling validation

4. **Extract configuration steps** from research:
   - Step-by-step guide for applying configuration
   - UI navigation instructions
   - Validation checklist

5. **Update agent file incrementally**:
   - Run `.specify/scripts/bash/update-agent-context.sh claude`
   - Add Genie configuration patterns (not code patterns)

**Output**: data-model.md, /contracts/genie_instructions.md, /contracts/sample_queries.md, quickstart.md, CLAUDE.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (instructions, sample queries, data model)
- Each configuration artifact → creation task [P]
- Sample query validation → test task
- Configuration application → documentation task
- Testing and validation → validation task

**Ordering Strategy**:
- Documentation order: Data model → Instructions → Sample queries
- Validation order: Create artifacts → Apply configuration → Test queries → Validate improvements
- Parallel execution: Configuration artifacts can be created in parallel [P]

**Estimated Output**: 10-15 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Configuration application (apply artifacts to Genie space via UI)  
**Phase 5**: Validation (test queries, validate improvements, document results)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

No violations detected - complexity tracking not needed.

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [ ] Phase 1: Design complete (/plan command)
- [ ] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Configuration applied
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [ ] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
