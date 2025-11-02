# Quickstart: Multi-Tool Calling Agent

**Feature**: 002-multi-tool-calling
**Purpose**: Validate agent implementation against acceptance scenarios
**Estimated Time**: 10-15 minutes

## Prerequisites

- ✅ Python 3.12+ installed
- ✅ Databricks Genie MCP tools configured
- ✅ Unity Catalog access to retail datasets
- ✅ Environment variables set (see Setup)

## Setup

### 1. Install Dependencies

```bash
cd /path/to/dbrx-multi-agent-retail-intelligence/30-mosaic-tool-calling-agent
pip install -r requirements.txt
pip install pytest databricks-sdk mlflow
```

### 2. Configure Environment

Create `.env` file with:

```bash
# Anthropic API
ANTHROPIC_API_KEY=your_api_key_here

# Databricks Configuration (if not using MCP)
DATABRICKS_HOST=your_workspace_url
DATABRICKS_TOKEN=your_token_here

# MCP Configuration (optional, for local development)
MCP_SERVER_CONFIG_PATH=~/.config/claude/mcp_servers.json
```

### 3. Verify Genie MCP Tools

```bash
# Test that Genie tools are available
python -c "
from anthropic import Anthropic
client = Anthropic()
# List available tools
print('Genie MCP tools configured successfully')
"
```

## Quick Test Scenarios

### Scenario 1: Simple Single-Domain Query

**Test**: Basic customer behavior query

```python
# Run from: 30-mosaic-tool-calling-agent/notebooks/02-test-agent.ipynb
# OR import from 30-mosaic-tool-calling-agent/src/

import sys
sys.path.append('../src')

from databricks import agents
from tools.customer_behavior import query_customer_behavior
from tools.inventory import query_inventory

# Initialize agent (defined in notebook 01-setup-agent.ipynb)
# agent = agents.Agent(...)

# Start conversation
session_id = agent.start_new_conversation()

# Ask question
from fashion_retail.agent.contracts.agent_interface import QueryRequest
request = QueryRequest(
    query="What are the top selling products this month?",
    session_id=session_id
)

response = agent.query(request)

# Verify
print(f"Answer: {response.answer}")
print(f"Sources: {response.sources}")
print(f"Suggestions: {response.suggestions}")
print(f"Execution time: {response.execution_time_ms}ms")

assert response.answer, "Should have an answer"
assert len(response.sources) > 0, "Should cite sources"
assert len(response.suggestions) > 0, "Should provide suggestions (FR-013)"
assert response.execution_time_ms < 60000, "Should complete within 60s (FR-012)"

print("✅ Scenario 1: PASS")
```

**Expected Output**:
- Natural language answer about top selling products
- At least one source (customer_behavior)
- 1-3 proactive suggestions (e.g., "Would you like to see inventory levels?")
- Execution time < 60 seconds

---

### Scenario 2: Multi-Domain Query

**Test**: Cart abandonment + inventory status (Acceptance Scenario 1 from spec)

```python
from fashion_retail.agent.orchestrator import MultiToolAgent
from fashion_retail.agent.contracts.agent_interface import QueryRequest

agent = MultiToolAgent()
session_id = agent.start_new_conversation()

request = QueryRequest(
    query="What products are frequently abandoned in carts and do we have inventory issues with those items?",
    session_id=session_id
)

response = agent.query(request)

# Verify multi-domain access
print(f"Answer: {response.answer}")
print(f"Sources: {response.sources}")

assert len(response.sources) >= 2, "Should access multiple domains"
assert "customer" in str(response.sources).lower() or "behavior" in str(response.sources).lower()
assert "inventory" in str(response.sources).lower()
assert "abandon" in response.answer.lower() or "cart" in response.answer.lower()
assert "inventory" in response.answer.lower() or "stock" in response.answer.lower()

print("✅ Scenario 2: PASS")
```

**Expected Output**:
- Synthesized answer combining cart abandonment data and inventory status
- At least 2 sources (customer_behavior, inventory)
- Coherent narrative (not separate responses)

---

### Scenario 3: Context-Aware Follow-Up

**Test**: Follow-up question using conversation history (Acceptance Scenario 5 from spec)

```python
from fashion_retail.agent.orchestrator import MultiToolAgent
from fashion_retail.agent.contracts.agent_interface import QueryRequest

agent = MultiToolAgent()
session_id = agent.start_new_conversation()

# First question
request1 = QueryRequest(
    query="What are the top cart abandonment products?",
    session_id=session_id
)
response1 = agent.query(request1)
print(f"Q1 Answer: {response1.answer}\n")

# Follow-up with pronoun reference
request2 = QueryRequest(
    query="What about their demographics?",  # "their" = customers who abandoned
    session_id=session_id
)
response2 = agent.query(request2)
print(f"Q2 Answer: {response2.answer}\n")

# Verify context understanding
assert response2.answer, "Should answer follow-up"
assert "demographic" in response2.answer.lower() or "customer" in response2.answer.lower()

# Check conversation history
history = agent.get_conversation_history(session_id)
print(f"Conversation length: {len(history)} messages")
assert len(history) >= 4  # 2 user queries + 2 assistant responses

print("✅ Scenario 3: PASS")
```

**Expected Output**:
- Agent understands "their" refers to customers from first query
- Provides demographic information about cart abandoners
- Conversation history contains all 4 messages

---

### Scenario 4: Proactive Suggestions

**Test**: Agent suggests related insights (FR-013)

```python
from fashion_retail.agent.orchestrator import MultiToolAgent
from fashion_retail.agent.contracts.agent_interface import QueryRequest

agent = MultiToolAgent()

request = QueryRequest(
    query="Show me this month's sales data",
    session_id=None
)

response = agent.query(request)

print(f"Answer: {response.answer}")
print(f"Suggestions: {response.suggestions}")

assert len(response.suggestions) > 0, "Must provide suggestions (FR-013)"
assert len(response.suggestions) <= 3, "Max 3 suggestions (per research.md)"

for suggestion in response.suggestions:
    print(f"  - {suggestion}")
    assert len(suggestion) > 10, "Suggestions should be meaningful"

print("✅ Scenario 4: PASS")
```

**Expected Output**:
- 1-3 proactive suggestions
- Examples: "Check inventory levels for top products", "View customer demographics for purchasers"

---

### Scenario 5: Error Handling

**Test**: Graceful handling when data unavailable (FR-008)

```python
from fashion_retail.agent.orchestrator import MultiToolAgent
from fashion_retail.agent.contracts.agent_interface import QueryRequest

agent = MultiToolAgent()

# Query potentially outside available domains
request = QueryRequest(
    query="What is the weather forecast for next week?",  # Not a retail data question
    session_id=None
)

response = agent.query(request)

print(f"Answer: {response.answer}")
print(f"Partial results: {response.partial_results}")
print(f"Error details: {response.error_details}")

# Agent should gracefully explain it can't answer
assert response.answer, "Should provide some response"
assert "cannot" in response.answer.lower() or "don't have" in response.answer.lower() or "unavailable" in response.answer.lower()

print("✅ Scenario 5: PASS")
```

**Expected Output**:
- Polite explanation that weather data is not available
- Suggestion to rephrase or ask about retail data domains

---

### Scenario 6: Performance Check

**Test**: Response time within 60 seconds (FR-012)

```python
import time
from fashion_retail.agent.orchestrator import MultiToolAgent
from fashion_retail.agent.contracts.agent_interface import QueryRequest

agent = MultiToolAgent()

# Complex multi-domain query
request = QueryRequest(
    query="Analyze cart abandonment patterns, correlate with inventory stockouts, and identify customer segments most affected",
    session_id=None
)

start_time = time.time()
response = agent.query(request)
elapsed_ms = (time.time() - start_time) * 1000

print(f"Elapsed time: {elapsed_ms}ms")
print(f"Response reported time: {response.execution_time_ms}ms")

assert elapsed_ms < 60000, f"Query exceeded 60s limit: {elapsed_ms}ms"
assert response.execution_time_ms < 60000, f"Reported time exceeded limit: {response.execution_time_ms}ms"

print("✅ Scenario 6: PASS")
```

**Expected Output**:
- Complete response within 60 seconds
- Both measured and reported times < 60000ms

---

## Contract Test Suite

Run all contract tests to verify implementation:

```bash
# Run contract tests
pytest specs/002-multi-tool-calling/contracts/test_agent_contract.py -v

# Run with coverage
pytest specs/002-multi-tool-calling/contracts/ --cov=fashion_retail.agent --cov-report=html

# View coverage report
open htmlcov/index.html
```

**Expected Results**:
- All contract tests PASS
- Coverage >= 80% for agent module

---

## Integration Test Suite

Run full integration tests with real Genie tools:

```bash
# Integration tests (requires Genie MCP access)
pytest tests/agent/integration/ -v -s

# Specific scenario
pytest tests/agent/integration/test_acceptance_scenarios.py::test_scenario_1 -v
```

---

## Validation Checklist

After running quickstart scenarios:

- [ ] ✅ Single-domain queries work (Scenario 1)
- [ ] ✅ Multi-domain queries synthesize correctly (Scenario 2)
- [ ] ✅ Conversation history maintained (Scenario 3)
- [ ] ✅ Proactive suggestions provided (Scenario 4)
- [ ] ✅ Errors handled gracefully (Scenario 5)
- [ ] ✅ Performance within 60s limit (Scenario 6)
- [ ] ✅ All contract tests pass
- [ ] ✅ Sources cited in all responses (FR-009)
- [ ] ✅ No result caching (FR-015)
- [ ] ✅ Unity Catalog permissions respected (FR-014)

---

## Troubleshooting

### Issue: "ImportError: No module named tools"

**Solution**: Ensure you're in the correct directory

```bash
# Verify you're in the right location
cd 30-mosaic-tool-calling-agent
ls src/tools/  # Should see customer_behavior.py, inventory.py

# Run from notebooks directory or add to path
cd notebooks
# Notebooks have sys.path.append('../src') at top
```

### Issue: "Genie MCP tools not available"

**Solution**: Verify MCP server configuration

```bash
# Check MCP config
cat ~/.config/claude/mcp_servers.json

# Ensure Genie tools are listed
# Should see: mcp__few-genie-customer-behavior__*
```

### Issue: "Permission denied errors"

**Solution**: Verify Unity Catalog access

```bash
# Check Databricks access
databricks auth login

# Test Genie access directly
# (Use Genie web interface to verify you can query customer_behavior and inventory spaces)
```

### Issue: "Queries timeout (> 60s)"

**Solution**: Check Genie query complexity and data volume

- Simplify queries during testing
- Verify Genie spaces are responsive
- Check for parallel tool execution (should be implemented)

---

## Next Steps

Once all scenarios pass:

1. **Deploy to Databricks**: Package agent as Databricks job
2. **Create CLI**: Add command-line interface for interactive use
3. **Add Observability**: Implement logging and tracing
4. **Extend Domains**: Add new data domains beyond customer_behavior and inventory

---

## Reference

- **Spec**: [spec.md](./spec.md)
- **Plan**: [plan.md](./plan.md)
- **Research**: [research.md](./research.md)
- **Data Model**: [data-model.md](./data-model.md)
- **Contracts**: [contracts/](./contracts/)

---

**Quickstart Status**: ✅ Ready for implementation validation
