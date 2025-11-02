
# Implementation Plan: Multi-Tool Calling Agent

**Branch**: `002-multi-tool-calling` | **Date**: 2025-11-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-multi-tool-calling/spec.md`

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
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code, or `AGENTS.md` for all other agents).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Build a conversational AI agent that answers natural language questions across multiple retail data domains (Customer Behavior and Inventory Management). The agent maintains conversation history for context-aware follow-ups, orchestrates multiple tool calls to Databricks Genie spaces, synthesizes insights from different domains, and proactively suggests related information. All data access respects Unity Catalog permissions with no caching to ensure fresh results within 60 seconds.

## Technical Context
**Language/Version**: Python 3.12+ (Databricks Runtime compatible)
**Primary Dependencies**:
- **Databricks Mosaic AI Agent Framework** (core agent orchestration)
- **MLflow** (conversation tracking, deployment, evaluation)
- **Databricks SDK** (Genie API integration)
- **Foundation Model APIs** (via Agent Framework - Claude, DBRX, etc.)
**Storage**:
- Conversation history: MLflow tracking (durable, traceable)
- Data: Delta Lake tables (via Genie/Unity Catalog)
**Testing**: pytest, MLflow evaluation framework, integration tests with Genie API
**Target Platform**:
- Primary: Databricks workspace (Model Serving endpoint)
- Development: Databricks notebook + local testing
**Project Type**: Standalone Databricks Agent (new implementation, not extending `20-agent-brick/`)
**Performance Goals**: <60 seconds response time for complex multi-domain queries
**Constraints**: No caching (always fetch fresh data), Unity Catalog permission enforcement, maintain full conversation context
**Scale/Scope**: 2 initial data domains (Customer Behavior, Inventory), extensible architecture for additional domains

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Initial Check (Pre-Research)**:
- ✅ **Modularity**: Agent implemented using Databricks Mosaic AI Agent Framework (platform standard)
- ✅ **Testability**: MLflow evaluation framework + pytest for unit/integration tests
- ✅ **Dependencies**: Leverages existing infrastructure (Genie spaces, multi-agent supervisor, Unity Catalog)
- ✅ **Data Access**: Unity Catalog permissions enforced via Genie (no custom auth layer)
- ✅ **Simplicity**: Agent Framework handles orchestration, we define tools and synthesis logic
- ✅ **Platform Integration**: Uses Databricks-native services (MLflow, Model Serving, Genie API)

**Post-Design Check (Post-Phase 1)**:
- ✅ **Clean Interfaces**: AgentInterface contract defines clear public API
- ✅ **Data Model**: Entities well-defined with validation rules and relationships
- ✅ **Separation of Concerns**: Orchestrator, conversation, routing, tool calling, synthesis as separate modules
- ✅ **No Over-Engineering**: Leverages existing Genie MCP infrastructure, no custom abstractions
- ✅ **Test Coverage**: Contract tests map 1:1 to functional requirements
- ✅ **Documentation**: Quickstart provides clear validation path

**Complexity Assessment**: ✅ No constitutional violations
- In-memory conversation storage is appropriate for initial implementation
- LLM-based routing is justified by requirement for semantic understanding
- No unnecessary layers or abstractions introduced

## Project Structure

### Documentation (this feature)
```
specs/002-multi-tool-calling/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

**Note**: Implementation code lives in `30-mosaic-tool-calling-agent/`, NOT in `specs/` or `src/`

### Source Code (repository root)
```
30-mosaic-tool-calling-agent/           # New: Standalone agent implementation
├── notebooks/
│   ├── 01-setup-agent.ipynb           # Agent definition and tool setup
│   ├── 02-test-agent.ipynb            # Interactive testing
│   ├── 03-deploy-agent.ipynb          # Model Serving deployment
│   └── 04-evaluate-agent.ipynb        # MLflow evaluation
├── src/
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── customer_behavior.py      # Genie tool for customer behavior
│   │   └── inventory.py               # Genie tool for inventory
│   ├── config/
│   │   ├── __init__.py
│   │   ├── agent_config.py            # Agent configuration
│   │   └── prompts.py                 # System prompts
│   └── utils/
│       ├── __init__.py
│       └── genie_client.py            # Genie API wrapper
├── tests/
│   ├── test_tools.py                  # Unit tests for tool functions
│   ├── test_agent.py                  # Agent integration tests
│   └── fixtures/                      # Test data and mocks
├── evaluation/
│   ├── eval_dataset.json              # MLflow evaluation dataset
│   └── eval_config.yaml               # Evaluation metrics config
├── requirements.txt                    # Python dependencies
└── README.md                           # Agent documentation

# Completely separate from:
20-agent-brick/                         # Documentation only - DO NOT USE
├── mas-setup.ipynb                    # Reference docs (not for implementation)

# Genie spaces (referenced by tools, not modified):
10-genie-rooms/
├── README.genie.customer-behavior.md
└── README.genie.inventory.md
```

**Structure Decision**: **Standalone directory** `30-mosaic-tool-calling-agent/` for all agent implementation. This is completely separate from `20-agent-brick/` (which is just documentation). The agent will call Genie APIs (configured in `10-genie-rooms/`) but will not modify or integrate with any existing agent code.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh claude`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:

The /tasks command will generate implementation tasks based on the following approach:

1. **Setup & Structure** (Tasks 1-3) [P]:
   - Task 1: Create `30-mosaic-tool-calling-agent/` directory structure
   - Task 2: Set up requirements.txt with dependencies
   - Task 3: Create README.md with setup instructions

2. **Genie Tool Functions** (Tasks 4-6) [P]:
   - Task 4: Implement `customer_behavior.py` Genie tool (FR-003)
   - Task 5: Implement `inventory.py` Genie tool (FR-004)
   - Task 6: Create `genie_client.py` wrapper for Databricks SDK

3. **Agent Configuration** (Tasks 7-9) [P]:
   - Task 7: Create `agent_config.py` with domain definitions
   - Task 8: Create `prompts.py` with system prompt (FR-006, FR-007, FR-009, FR-013)
   - Task 9: Create domain relationship graph for suggestions (FR-013)

4. **Agent Definition Notebook** (Tasks 10-12):
   - Task 10: Create `01-setup-agent.ipynb` - define agent with tools
   - Task 11: Configure agent system prompt and parameters
   - Task 12: Register agent with MLflow (FR-011 tracking)

5. **Testing Notebooks** (Tasks 13-17):
   - Task 13: Create `02-test-agent.ipynb` - interactive testing
   - Task 14: Implement test for single-domain query (FR-001, FR-003)
   - Task 15: Implement test for multi-domain query (FR-005, FR-006)
   - Task 16: Implement test for conversation context (FR-011)
   - Task 17: Implement test for proactive suggestions (FR-013)

6. **Unit Tests** (Tasks 18-21) [P]:
   - Task 18: Create `test_tools.py` - unit tests for Genie tools
   - Task 19: Create test fixtures for Genie API responses
   - Task 20: Create `test_agent.py` - agent integration tests
   - Task 21: Map acceptance scenarios from spec.md to test cases

7. **MLflow Evaluation** (Tasks 22-25):
   - Task 22: Create `eval_dataset.json` with test queries
   - Task 23: Create `eval_config.yaml` with quality metrics
   - Task 24: Create `04-evaluate-agent.ipynb` - MLflow eval
   - Task 25: Validate agent meets FR-012 (60s timeout) and FR-015 (no caching)

8. **Deployment** (Tasks 26-28):
   - Task 26: Create `03-deploy-agent.ipynb` - Model Serving deployment
   - Task 27: Test deployed endpoint
   - Task 28: Document deployment process in README.md

**Ordering Strategy**:
- **Structure First**: Directory setup (Tasks 1-3) before all else
- **Tools Before Agent**: Genie tools (4-6) + config (7-9) before agent definition (10-12)
- **Agent Then Tests**: Agent setup (10-12) before testing notebooks (13-17)
- **Parallel Execution**: Tasks marked [P] can run concurrently (independent modules)
- **Evaluation Last**: MLflow eval (22-25) and deployment (26-28) after agent works

**Estimated Output**: 28 numbered, dependency-ordered tasks in tasks.md

**Key Dependencies**:
```
Tasks 1-3 (setup) [P] ──→ Tasks 4-6 (tools) [P] ──→ Tasks 7-9 (config) [P] ──→ Task 10-12 (agent) ──→ Tasks 13-17 (test notebooks)
                                                                                         ↓
                                                                    Tasks 18-21 (unit tests) [P]
                                                                                         ↓
                                                                    Tasks 22-25 (evaluation) ──→ Tasks 26-28 (deployment)
```

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
- [x] Phase 0: Research complete (/plan command) - ✅ research.md created
- [x] Phase 1: Design complete (/plan command) - ✅ data-model.md, contracts/, quickstart.md created
- [x] Phase 2: Task planning complete (/plan command - describe approach only) - ✅ 30-task strategy documented
- [ ] Phase 3: Tasks generated (/tasks command) - ⏳ Ready for /tasks execution
- [ ] Phase 4: Implementation complete - ⏳ Awaiting task execution
- [ ] Phase 5: Validation passed - ⏳ Awaiting implementation

**Gate Status**:
- [x] Initial Constitution Check: PASS - ✅ No violations identified
- [x] Post-Design Constitution Check: PASS - ✅ Clean interfaces, no over-engineering
- [x] All NEEDS CLARIFICATION resolved - ✅ Technical Context fully specified
- [x] Complexity deviations documented - ✅ None required (no violations)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
