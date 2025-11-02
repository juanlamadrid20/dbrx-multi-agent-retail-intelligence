# Multi-Tool Calling Agent - Notebooks

Run these notebooks **in order** in Databricks.

## Execution Order

### 1. `01-register-uc-functions.ipynb`
**Purpose**: Register Genie tools as Unity Catalog Functions

**What it does**:
- Registers `juan_dev.genai.query_customer_behavior_genie`
- Registers `juan_dev.genai.query_inventory_genie`
- Verifies registration

**Dependencies**:
- `unitycatalog-ai`
- `databricks-sdk`

**Run once**: Only needs to be re-run if tool logic changes

---

### 2. `02-create-agent.ipynb`
**Purpose**: Create LangGraph agent and log to MLflow

**What it does**:
- Loads UC Functions as tools via UCFunctionToolkit
- Creates agent using `create_react_agent` (LangGraph pattern)
- Logs agent to MLflow
- Runs quick smoke test

**Dependencies**:
- `mlflow`
- `databricks-langchain`
- `langgraph`
- `langchain-core`

**Pattern**: Based on [Databricks LangGraph Guide](https://docs.databricks.com/aws/en/notebooks/source/generative-ai/responses-agent-langgraph.html)

---

### 3. `03-test-agent.ipynb`
**Purpose**: Comprehensive testing of all functional requirements

**Test Scenarios**:
1. ✅ Single-domain queries (FR-001, FR-003)
2. ✅ Multi-domain queries (FR-005, FR-006)
3. ✅ Context-aware follow-ups (FR-011)
4. ✅ Proactive suggestions (FR-013)
5. ✅ Error handling (FR-008)
6. ✅ Performance < 60s (FR-012)

**Dependencies**:
- `mlflow` (to load agent)
- `langgraph`
- `langchain-core`

---

## Old Notebooks (Deprecated)

- `01-setup-agent.ipynb` - Old monolithic setup (replaced by 01-02 split)
- `02-test-agent.ipynb` - Old test notebook (replaced by 03)

These can be deleted after verifying the new notebooks work.

---

## Troubleshooting

### Import errors
Run the `%pip install` cell in each notebook to install dependencies.

### UC Function not found
Re-run `01-register-uc-functions.ipynb` to register the functions.

### Agent not found in MLflow
Re-run `02-create-agent.ipynb` to create and log the agent.

### Genie space ID errors
Update space IDs in `../src/config/agent_config.py` and re-register UC Functions.

---

## Configuration

Agent configuration is in:
- `../src/config/agent_config.py` - Domain configs, UC Function names, agent parameters
- `../src/config/prompts.py` - System prompt
- `../src/tools/` - UC Function implementations
