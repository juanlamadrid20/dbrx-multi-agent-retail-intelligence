# Multi-Agent System with Genie - Notebooks

Run these notebooks **in order** in Databricks.

## Execution Order

### ~~1. `01-register-uc-functions.ipynb`~~ (DEPRECATED)
**Status**: No longer needed! We use GenieAgent instead of custom UC Functions.

See notebook for migration details.

---

### 0. `00-test-genie-access.ipynb` (Optional but Recommended)
**Purpose**: Test Genie space access and responses before creating the agent

**What it does**:
- Verifies permissions on both Genie spaces
- Sends domain-specific test queries
- Validates actual responses (not just permissions)
- Shows full responses and generated SQL
- Supports custom query testing

**When to use**:
- Before running 02-create-agent.ipynb for the first time
- Debugging Genie access issues
- Testing new queries

---

### 1. `02-create-agent.ipynb`
**Purpose**: Create multi-agent system with GenieAgent and log to MLflow

**What it does**:
- Creates supervisor agent coordinating multiple Genie agents
- Uses `GenieAgent` from `databricks_langchain` for Genie Space access
- Automatic authentication (no UC Functions needed!)
- Logs multi-agent system to MLflow
- Runs quick smoke tests

**Dependencies**:
- `mlflow`
- `databricks-langchain`
- `langgraph`
- `langchain-core`

**Pattern**: Based on [Databricks Multi-Agent Genie Guide](https://docs.databricks.com/aws/en/generative-ai/agent-framework/multi-agent-genie)

---

### 2. `03-test-agent.ipynb`
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

## Architecture Change

**Previous approach** (deprecated):
- Custom UC Functions calling Genie API
- Authentication issues in serverless Spark
- Required UC Function registration

**Current approach** (recommended):
- GenieAgent from databricks_langchain
- Automatic authentication
- Supervisor pattern for multi-domain queries
- No UC Function registration needed

---

## Troubleshooting

### Import errors
Run the `%pip install` cell in each notebook to install dependencies.

### GenieAgent import errors
Ensure `databricks-langchain` is installed: `%pip install --upgrade databricks-langchain`

### Genie queries timing out
Run `00-test-genie-access.ipynb` to verify Genie spaces are responding. The SDK now uses `wait_get_message_genie_completed()` which properly waits for responses.

### Agent not found in MLflow
Re-run `02-create-agent.ipynb` to create and log the agent.

### Genie space ID errors
Update space IDs in `../src/config/agent_config.py`. No re-registration needed!

---

## Configuration

Agent configuration is in:
- `../src/config/agent_config.py` - Domain configs (Genie space IDs), agent parameters
- `../src/config/prompts.py` - System prompt
