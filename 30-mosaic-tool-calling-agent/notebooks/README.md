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

**What it does**:
- Loads agent from Unity Catalog
- Tests single-domain queries (inventory, customer behavior)
- Tests multi-domain queries (cross-domain analysis)
- Tests conversation context and follow-ups
- Validates performance (<90s per query)
- Manages model aliases (`challenger`, `champion`, etc.)

**Test Scenarios**:
1. ✅ Single-domain queries (FR-001, FR-003)
2. ✅ Multi-domain queries (FR-005, FR-006)
3. ✅ Context-aware follow-ups (FR-011)
4. ✅ Error handling (FR-008)
5. ✅ Performance < 90s (FR-012)

**Dependencies**:
- `mlflow` (to load agent from UC)
- `databricks-langchain`
- `langgraph`
- `langchain-core`

**Unity Catalog Model**: `juan_dev.genai.retail_multi_genie_agent`

---

### 3. `04-deploy-agent.ipynb`
**Purpose**: Deploy agent to Databricks Model Serving endpoint

**What it does**:
- Creates or updates a Model Serving endpoint
- Deploys UC-registered model to production
- Configures CPU workload with scale-to-zero
- Runs comprehensive endpoint tests
- Provides integration examples

**Endpoint Configuration**:
- **Name**: `retail-multi-genie-agent`
- **Model**: `juan_dev.genai.retail_multi_genie_agent@challenger`
- **Workload**: CPU Small (0-4 concurrent requests)
- **Scale to Zero**: Enabled (cost optimization)
- **Authentication**: Automatic Genie Space passthrough

**Test Coverage**:
1. ✅ Single domain queries
2. ✅ Multi-domain queries
3. ✅ Conversation context
4. ✅ Performance validation
5. ✅ Integration examples

**Dependencies**:
- `databricks-sdk` (for endpoint management)
- `mlflow` (for model references)

**Deployment Time**: ~10-15 minutes for initial deployment

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

### Endpoint deployment fails
- Check Unity Catalog model permissions
- Verify model version/alias exists
- Check Model Serving quota/permissions
- Monitor deployment progress in UI: `/ml/endpoints/<endpoint-name>`

### Endpoint queries failing
- Verify endpoint is in READY state
- Check authentication token is valid
- Ensure payload format matches: `{"input": [{"role": "user", "content": "..."}]}`
- Review endpoint logs in UI

---

## Configuration

Agent configuration is in:
- `../src/config/agent_config.py` - Domain configs (Genie space IDs), agent parameters
- `../src/config/prompts.py` - System prompt

## Deployment

### Model Serving Endpoint
- **Endpoint Name**: `retail-multi-genie-agent`
- **UC Model**: `juan_dev.genai.retail_multi_genie_agent`
- **Workload**: CPU Small (scalable to Medium/Large)
- **Cost**: Scale-to-zero enabled (only pay when in use)

### Scaling Guide
- **Small**: 0-4 concurrent requests (development/testing)
- **Medium**: 8-16 concurrent requests (production)
- **Large**: 16-64 concurrent requests (high traffic)

Update endpoint configuration in `04-deploy-agent.ipynb` or via UI.

### Integration
See `04-deploy-agent.ipynb` for Python and cURL examples.

**Endpoint URL**: `https://<workspace>.databricks.com/serving-endpoints/retail-multi-genie-agent/invocations`
