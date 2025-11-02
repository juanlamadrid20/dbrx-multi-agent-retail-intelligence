# Implementation Tasks: Multi-Tool Calling Agent

**Feature**: 002-multi-tool-calling
**Branch**: `002-multi-tool-calling`
**Status**: Ready for implementation
**Generated**: 2025-11-02

---

## Task Execution Order

```
Tasks 1-3 (setup) [P] ──→ Tasks 4-6 (tools) [P] ──→ Tasks 7-9 (config) [P] ──→ Task 10-12 (agent) ──→ Tasks 13-17 (test notebooks)
                                                                                         ↓
                                                                    Tasks 18-21 (unit tests) [P]
                                                                                         ↓
                                                                    Tasks 22-25 (evaluation) ──→ Tasks 26-28 (deployment)
```

**Legend**:
- `[P]` = Parallelizable (can run concurrently with other [P] tasks)
- Dependencies shown with arrows (→)

---

## Phase 1: Setup & Structure

### Task 1: Create directory structure [P]
**Priority**: High
**Dependencies**: None
**Estimated Time**: 15 minutes

**Description**: Create the `30-mosaic-tool-calling-agent/` directory structure for the standalone agent implementation.

**Actions**:
```bash
cd /Users/juan.lamadrid/dev/databricks-projects/ml/agent-bricks/dbrx-multi-agent-retail-intelligence

mkdir -p 30-mosaic-tool-calling-agent/notebooks
mkdir -p 30-mosaic-tool-calling-agent/src/tools
mkdir -p 30-mosaic-tool-calling-agent/src/config
mkdir -p 30-mosaic-tool-calling-agent/src/utils
mkdir -p 30-mosaic-tool-calling-agent/tests/fixtures
mkdir -p 30-mosaic-tool-calling-agent/evaluation
```

**Verification**:
- [ ] Directory structure exists
- [ ] All subdirectories created
- [ ] No files in `20-agent-brick/` are referenced or modified

**References**: plan.md:94-134

---

### Task 2: Create requirements.txt [P]
**Priority**: High
**Dependencies**: Task 1
**Estimated Time**: 10 minutes

**Description**: Create Python dependencies file based on research.md technical decisions.

**File**: `30-mosaic-tool-calling-agent/requirements.txt`

**Content**:
```txt
# Core Databricks Dependencies
unitycatalog-ai>=0.1.0
databricks-langchain>=0.1.0
databricks-sdk>=0.20.0
mlflow>=2.10.0
langchain>=0.1.0
langchain-core>=0.1.0

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0

# Utilities
python-dotenv>=1.0.0
pydantic>=2.0.0
```

**Verification**:
- [ ] requirements.txt exists
- [ ] All dependencies from plan.md:38-47 included
- [ ] Version constraints specified

**References**: plan.md:38-47, research.md:107-120

---

### Task 3: Create README.md with setup instructions [P]
**Priority**: Medium
**Dependencies**: Task 1
**Estimated Time**: 20 minutes

**Description**: Document agent setup, architecture overview, and quick start guide.

**File**: `30-mosaic-tool-calling-agent/README.md`

**Must Include**:
- Agent purpose and capabilities
- Architecture diagram (text-based)
- Installation instructions
- Quick start example
- Unity Catalog function registration
- Notebook execution order
- Links to spec.md and plan.md

**Verification**:
- [ ] README.md exists
- [ ] Setup instructions complete
- [ ] References to Genie spaces (10-genie-rooms/)
- [ ] No references to 20-agent-brick/

**References**: plan.md:122-134

---

## Phase 2: Genie Tool Functions (UC Functions)

### Task 4: Implement customer_behavior.py Genie tool [P]
**Priority**: High
**Dependencies**: Tasks 1-3
**Estimated Time**: 45 minutes

**Description**: Create Unity Catalog Function for Customer Behavior Genie space following official Databricks UC Functions pattern.

**File**: `30-mosaic-tool-calling-agent/src/tools/customer_behavior.py`

**Implementation Pattern** (from research.md:107-206):
```python
from unitycatalog.ai.core.databricks import DatabricksFunctionClient
from databricks.sdk import WorkspaceClient

def query_customer_behavior_genie(query: str) -> str:
    """Query customer behavior data using Genie natural language interface.

    This tool accesses the Customer Behavior Genie space to answer questions about:
    - Customer purchasing patterns and lifecycle
    - Cart abandonment rates and affected products
    - Customer segmentation (RFM analysis)
    - Product affinity and basket analysis

    Args:
        query (str): Natural language question about customer behavior

    Returns:
        str: Natural language answer from Genie with optional SQL query

    Examples:
        "What are the top 10 products by cart abandonment rate?"
        "Show me customer segments with highest lifetime value"
    """
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient()

    # Get Customer Behavior Genie space ID from config
    space_id = "<customer_behavior_space_id>"  # TODO: Load from config

    conversation = w.genie.start_conversation(space_id=space_id)

    message = w.genie.post_message(
        conversation_id=conversation.conversation_id,
        content=query
    )

    answer = message.content
    sql = message.attachments[0].query.query if message.attachments else None

    result = f"[Source: Customer Behavior Genie]\n{answer}"
    if sql:
        result += f"\n\n[SQL Query]: {sql}"

    return result


def register_customer_behavior_tool(catalog: str = "main", schema: str = "default") -> str:
    """Register customer behavior tool as Unity Catalog Function."""
    client = DatabricksFunctionClient()

    func = client.create_python_function(
        func=query_customer_behavior_genie,
        catalog=catalog,
        schema=schema,
        replace=True
    )

    return f"{catalog}.{schema}.query_customer_behavior_genie"
```

**Requirements** (from research.md:130-145):
- ✅ Type hints on all parameters and returns
- ✅ Google-style docstring with Args, Returns, Examples
- ✅ Imports INSIDE function body (not at module level)
- ✅ Error handling for Genie API failures

**Verification**:
- [ ] File created at correct path
- [ ] Function signature matches pattern
- [ ] Docstring follows Google style
- [ ] Type hints present
- [ ] Imports inside function body
- [ ] Error handling implemented (FR-008)

**References**: research.md:107-206, spec.md FR-003, plan.md:204

---

### Task 5: Implement inventory.py Genie tool [P]
**Priority**: High
**Dependencies**: Tasks 1-3
**Estimated Time**: 45 minutes

**Description**: Create Unity Catalog Function for Inventory Management Genie space.

**File**: `30-mosaic-tool-calling-agent/src/tools/inventory.py`

**Implementation Pattern**:
```python
from unitycatalog.ai.core.databricks import DatabricksFunctionClient
from databricks.sdk import WorkspaceClient

def query_inventory_genie(query: str) -> str:
    """Query inventory management data using Genie natural language interface.

    This tool accesses the Inventory Management Genie space to answer questions about:
    - Current stock levels and availability
    - Stockout events and inventory constraints
    - Inventory turnover and aging
    - Replenishment delays and supply chain issues

    Args:
        query (str): Natural language question about inventory

    Returns:
        str: Natural language answer from Genie with optional SQL query

    Examples:
        "What products have low inventory levels?"
        "Show me stockout events in the last 30 days"
    """
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient()

    # Get Inventory Genie space ID from config
    space_id = "<inventory_space_id>"  # TODO: Load from config

    conversation = w.genie.start_conversation(space_id=space_id)

    message = w.genie.post_message(
        conversation_id=conversation.conversation_id,
        content=query
    )

    answer = message.content
    sql = message.attachments[0].query.query if message.attachments else None

    result = f"[Source: Inventory Genie]\n{answer}"
    if sql:
        result += f"\n\n[SQL Query]: {sql}"

    return result


def register_inventory_tool(catalog: str = "main", schema: str = "default") -> str:
    """Register inventory tool as Unity Catalog Function."""
    client = DatabricksFunctionClient()

    func = client.create_python_function(
        func=query_inventory_genie,
        catalog=catalog,
        schema=schema,
        replace=True
    )

    return f"{catalog}.{schema}.query_inventory_genie"
```

**Requirements**:
- Same as Task 4 (type hints, docstrings, imports, error handling)

**Verification**:
- [ ] File created at correct path
- [ ] Function signature matches pattern
- [ ] Docstring follows Google style
- [ ] Type hints present
- [ ] Imports inside function body
- [ ] Error handling implemented (FR-008)

**References**: research.md:107-206, spec.md FR-004, plan.md:205

---

### Task 6: Create genie_client.py utility wrapper [P]
**Priority**: Medium
**Dependencies**: Tasks 4-5
**Estimated Time**: 30 minutes

**Description**: Create utility module for common Genie API operations (error handling, response parsing).

**File**: `30-mosaic-tool-calling-agent/src/utils/genie_client.py`

**Must Include**:
- Error handling wrapper for Genie API calls (FR-008)
- Response parsing helpers
- Timeout management (FR-012)
- Logging utilities

**Example Structure**:
```python
from databricks.sdk import WorkspaceClient
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class GenieClientError(Exception):
    """Base exception for Genie client errors"""
    pass

def safe_genie_query(space_id: str, query: str, timeout_seconds: int = 50) -> Dict:
    """
    Safely execute Genie query with error handling and timeout.

    Args:
        space_id: Genie space identifier
        query: Natural language query
        timeout_seconds: Max execution time (default 50s, leaves 10s buffer for FR-012)

    Returns:
        Dict with keys: answer (str), sql (Optional[str]), error (Optional[str])
    """
    # Implementation here
    pass
```

**Verification**:
- [ ] File created
- [ ] Error handling implemented (FR-008)
- [ ] Timeout support (FR-012)
- [ ] Logging configured

**References**: plan.md:206, spec.md FR-008, FR-012

---

## Phase 3: Agent Configuration

### Task 7: Create agent_config.py with domain definitions [P]
**Priority**: High
**Dependencies**: Tasks 4-6
**Estimated Time**: 30 minutes

**Description**: Define domain metadata and configuration for agent.

**File**: `30-mosaic-tool-calling-agent/src/config/agent_config.py`

**Must Include**:
```python
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class DomainConfig:
    """Configuration for a data domain"""
    name: str
    display_name: str
    description: str
    capabilities: List[str]
    genie_space_id: str
    uc_function_name: str

# Domain definitions (FR-002)
DOMAINS = {
    "customer_behavior": DomainConfig(
        name="customer_behavior",
        display_name="Customer Behavior",
        description="Customer purchasing patterns, cart abandonment, segmentation",
        capabilities=[
            "Cart abandonment analysis",
            "Customer segmentation (RFM)",
            "Product affinity",
            "Purchase patterns"
        ],
        genie_space_id="<customer_behavior_space_id>",
        uc_function_name="main.default.query_customer_behavior_genie"
    ),
    "inventory": DomainConfig(
        name="inventory",
        display_name="Inventory Management",
        description="Stock levels, stockouts, replenishment delays",
        capabilities=[
            "Inventory status",
            "Stockout events",
            "Inventory constraints",
            "Replenishment tracking"
        ],
        genie_space_id="<inventory_space_id>",
        uc_function_name="main.default.query_inventory_genie"
    )
}

# Agent configuration
AGENT_CONFIG = {
    "model_endpoint": "databricks-meta-llama-3-1-70b-instruct",
    "temperature": 0.0,
    "max_tokens": 2000,
    "timeout_seconds": 60,  # FR-012
    "max_suggestions": 3,   # Research decision
}
```

**Verification**:
- [ ] File created
- [ ] Both domains defined
- [ ] Agent config includes timeout (FR-012)
- [ ] Max suggestions = 3 (from research.md)

**References**: plan.md:207, data-model.md:46-67, research.md:88-92

---

### Task 8: Create prompts.py with system prompt [P]
**Priority**: High
**Dependencies**: Task 7
**Estimated Time**: 45 minutes

**Description**: Create system prompt that implements FR-006, FR-007, FR-009, FR-013.

**File**: `30-mosaic-tool-calling-agent/src/config/prompts.py`

**System Prompt Must Include**:
- Role definition: Multi-domain retail intelligence assistant
- Available tools and capabilities (from DOMAINS)
- Response format requirements (FR-007, FR-009)
- Proactive suggestion requirement (FR-013)
- Conversation history awareness (FR-011)
- Error handling guidance (FR-008)

**Example Structure**:
```python
SYSTEM_PROMPT = """You are a retail intelligence assistant with access to multiple data domains.

## Available Tools
You have access to the following data domains:
1. Customer Behavior: Cart abandonment, customer segmentation, purchase patterns
2. Inventory Management: Stock levels, stockouts, replenishment delays

## Response Requirements
1. Always cite data sources used (e.g., "[Source: Customer Behavior Genie]")
2. Provide clear, actionable answers in natural language
3. Synthesize information from multiple domains into coherent responses
4. When data is unavailable, explain gracefully and suggest alternatives

## Proactive Suggestions (REQUIRED)
At the end of EVERY response, provide 1-3 suggestions for related insights from OTHER domains.
Example: After answering about cart abandonment, suggest checking inventory levels for those products.

## Conversation Context
Maintain context from previous messages in the conversation to handle follow-up questions.

## Performance
Aim to respond within 60 seconds. For complex queries, prioritize the most relevant information.
"""

SUGGESTION_PROMPT = """Based on the current query about {domain}, suggest 1-3 related insights from other domains: {other_domains}"""
```

**Verification**:
- [ ] System prompt created
- [ ] All FR requirements addressed
- [ ] Suggestion prompt included
- [ ] Clear citation requirements (FR-009)

**References**: plan.md:208, spec.md FR-006, FR-007, FR-009, FR-013

---

### Task 9: Create domain relationship graph for suggestions [P]
**Priority**: Medium
**Dependencies**: Tasks 7-8
**Estimated Time**: 30 minutes

**Description**: Define relationships between domains to power proactive suggestions (FR-013).

**File**: `30-mosaic-tool-calling-agent/src/config/domain_relationships.py`

**Must Include**:
```python
from typing import Dict, List

# Domain relationship graph for suggestions (FR-013)
DOMAIN_RELATIONSHIPS = {
    "customer_behavior": {
        "related_domains": ["inventory"],
        "suggestion_templates": [
            "Check inventory levels for the products mentioned",
            "View stockout events for these items",
            "Analyze inventory constraints affecting these products"
        ]
    },
    "inventory": {
        "related_domains": ["customer_behavior"],
        "suggestion_templates": [
            "View customer purchase patterns for these products",
            "Analyze cart abandonment for items with low stock",
            "Check customer segments affected by stockouts"
        ]
    }
}

def get_suggestions_for_domain(domain: str, context: str) -> List[str]:
    """Generate proactive suggestions based on domain and context"""
    # Implementation here
    pass
```

**Verification**:
- [ ] File created
- [ ] Bidirectional relationships defined
- [ ] Suggestion templates provided
- [ ] Helper function implemented

**References**: plan.md:209, spec.md FR-013, research.md:88-92

---

## Phase 4: Agent Definition Notebook

### Task 10: Create 01-setup-agent.ipynb - define agent with tools
**Priority**: High
**Dependencies**: Tasks 1-9
**Estimated Time**: 60 minutes

**Description**: Create notebook that registers UC Functions and defines the agent using UCFunctionToolkit.

**File**: `30-mosaic-tool-calling-agent/notebooks/01-setup-agent.ipynb`

**Notebook Cells**:

**Cell 1: Imports and setup**
```python
import sys
sys.path.append('../src')

from tools.customer_behavior import register_customer_behavior_tool
from tools.inventory import register_inventory_tool
from config.agent_config import AGENT_CONFIG, DOMAINS
from config.prompts import SYSTEM_PROMPT

from databricks_langchain import UCFunctionToolkit, ChatDatabricks
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
import mlflow
```

**Cell 2: Register UC Functions**
```python
# Register tools as Unity Catalog Functions
customer_func = register_customer_behavior_tool(catalog="main", schema="default")
inventory_func = register_inventory_tool(catalog="main", schema="default")

print(f"Registered: {customer_func}")
print(f"Registered: {inventory_func}")
```

**Cell 3: Create toolkit from UC Functions** (from research.md:172-184)
```python
toolkit = UCFunctionToolkit(
    function_names=[
        "main.default.query_customer_behavior_genie",
        "main.default.query_inventory_genie"
    ]
)

print(f"Available tools: {[tool.name for tool in toolkit.tools]}")
```

**Cell 4: Create agent**
```python
llm = ChatDatabricks(
    endpoint=AGENT_CONFIG["model_endpoint"],
    temperature=AGENT_CONFIG["temperature"],
    max_tokens=AGENT_CONFIG["max_tokens"]
)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, toolkit.tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=toolkit.tools,
    verbose=True,
    return_intermediate_steps=True
)
```

**Verification**:
- [ ] Notebook created
- [ ] UC Functions registered
- [ ] UCFunctionToolkit used (not manual tool list)
- [ ] Agent executor configured
- [ ] Follows research.md pattern

**References**: plan.md:210, research.md:172-206

---

### Task 11: Configure agent system prompt and parameters
**Priority**: High
**Dependencies**: Task 10
**Estimated Time**: 30 minutes

**Description**: Add conversation management and MLflow tracking to notebook.

**File**: `30-mosaic-tool-calling-agent/notebooks/01-setup-agent.ipynb` (additional cells)

**Cell 5: Conversation manager**
```python
from typing import Dict, List
import uuid
from datetime import datetime

class ConversationManager:
    """Manages conversation history (FR-011)"""

    def __init__(self):
        self.conversations: Dict[str, List[Dict]] = {}

    def start_conversation(self) -> str:
        session_id = str(uuid.uuid4())
        self.conversations[session_id] = []
        return session_id

    def add_message(self, session_id: str, role: str, content: str):
        if session_id not in self.conversations:
            raise ValueError(f"Session {session_id} not found")

        self.conversations[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })

    def get_history(self, session_id: str) -> List[Dict]:
        if session_id not in self.conversations:
            raise ValueError(f"Session {session_id} not found")
        return self.conversations[session_id]

conversation_manager = ConversationManager()
```

**Cell 6: Test conversation**
```python
# Test conversation management
session_id = conversation_manager.start_conversation()
print(f"Started conversation: {session_id}")

conversation_manager.add_message(session_id, "user", "Test query")
conversation_manager.add_message(session_id, "assistant", "Test response")

history = conversation_manager.get_history(session_id)
print(f"History length: {len(history)}")
```

**Verification**:
- [ ] Conversation manager implemented (FR-011)
- [ ] Session management working
- [ ] History retrieval functional

**References**: plan.md:211, spec.md FR-011

---

### Task 12: Register agent with MLflow
**Priority**: High
**Dependencies**: Task 11
**Estimated Time**: 45 minutes

**Description**: Add MLflow tracking and model registration.

**File**: `30-mosaic-tool-calling-agent/notebooks/01-setup-agent.ipynb` (additional cells)

**Cell 7: MLflow logging** (from research.md:186-206)
```python
mlflow.set_experiment("/Workspace/Users/<your_email>/multi-tool-calling-agent")

with mlflow.start_run(run_name="agent-setup") as run:
    # Log configuration
    mlflow.log_params(AGENT_CONFIG)

    # Log agent as langchain model
    mlflow.langchain.log_model(
        lc_model=agent_executor,
        artifact_path="agent",
        input_example={"input": "What are the top cart abandonment products?"},
        registered_model_name="multi_tool_calling_agent"
    )

    print(f"Run ID: {run.info.run_id}")
    print(f"Model URI: runs:/{run.info.run_id}/agent")
```

**Verification**:
- [ ] MLflow experiment created
- [ ] Agent logged to MLflow
- [ ] Model registered
- [ ] Run ID captured

**References**: plan.md:212, research.md:186-206

---

## Phase 5: Testing Notebooks

### Task 13: Create 02-test-agent.ipynb - interactive testing
**Priority**: High
**Dependencies**: Tasks 10-12
**Estimated Time**: 45 minutes

**Description**: Create notebook for interactive agent testing.

**File**: `30-mosaic-tool-calling-agent/notebooks/02-test-agent.ipynb`

**Must Include**:
- Load agent from MLflow
- Conversation manager setup
- Helper function for queries
- Response formatting utilities

**Key Cell**:
```python
import mlflow

# Load agent from MLflow
model_uri = "models:/multi_tool_calling_agent/latest"
agent = mlflow.langchain.load_model(model_uri)

def query_agent(query: str, session_id: str = None):
    """Helper function to query agent"""
    if session_id is None:
        session_id = conversation_manager.start_conversation()

    conversation_manager.add_message(session_id, "user", query)

    result = agent.invoke({
        "input": query,
        "chat_history": conversation_manager.get_history(session_id)
    })

    conversation_manager.add_message(session_id, "assistant", result["output"])

    return {
        "answer": result["output"],
        "session_id": session_id,
        "intermediate_steps": result.get("intermediate_steps", [])
    }
```

**Verification**:
- [ ] Notebook created
- [ ] Agent loading works
- [ ] Query helper functional
- [ ] Conversation tracking integrated

**References**: plan.md:213

---

### Task 14: Implement test for single-domain query
**Priority**: High
**Dependencies**: Task 13
**Estimated Time**: 30 minutes

**Description**: Add test cell for single-domain query (FR-001, FR-003).

**File**: `30-mosaic-tool-calling-agent/notebooks/02-test-agent.ipynb` (additional cells)

**Test Cell**:
```python
# Test: Single-domain query (FR-001, FR-003)
response = query_agent("What are the top cart abandonment products?")

print(f"Answer: {response['answer']}")
print(f"Session: {response['session_id']}")
print(f"Tools called: {[step[0].tool for step in response['intermediate_steps']]}")

# Assertions
assert response['answer'], "Should have answer"
assert 'customer' in str(response['intermediate_steps']).lower() or 'behavior' in str(response['intermediate_steps']).lower()
print("✅ Single-domain query test PASSED")
```

**Verification**:
- [ ] Test cell added
- [ ] Assertions validate FR-001, FR-003
- [ ] Output clearly formatted

**References**: plan.md:214, quickstart.md:54-96

---

### Task 15: Implement test for multi-domain query
**Priority**: High
**Dependencies**: Task 14
**Estimated Time**: 30 minutes

**Description**: Add test cell for multi-domain query (FR-005, FR-006).

**File**: `30-mosaic-tool-calling-agent/notebooks/02-test-agent.ipynb` (additional cells)

**Test Cell** (from quickstart.md:106-141):
```python
# Test: Multi-domain query (FR-005, FR-006)
response = query_agent(
    "What products are frequently abandoned in carts and do we have inventory issues with those items?"
)

print(f"Answer: {response['answer']}")
tools_called = [step[0].tool for step in response['intermediate_steps']]
print(f"Tools called: {tools_called}")

# Assertions
assert len(set(tools_called)) >= 2, "Should call multiple domain tools (FR-005)"
assert 'abandon' in response['answer'].lower() or 'cart' in response['answer'].lower()
assert 'inventory' in response['answer'].lower() or 'stock' in response['answer'].lower()
print("✅ Multi-domain query test PASSED")
```

**Verification**:
- [ ] Test cell added
- [ ] Validates FR-005 (multiple domains)
- [ ] Validates FR-006 (synthesized response)

**References**: plan.md:215, quickstart.md:106-141

---

### Task 16: Implement test for conversation context
**Priority**: High
**Dependencies**: Task 15
**Estimated Time**: 30 minutes

**Description**: Add test cell for context-aware follow-up (FR-011).

**File**: `30-mosaic-tool-calling-agent/notebooks/02-test-agent.ipynb` (additional cells)

**Test Cell** (from quickstart.md:143-187):
```python
# Test: Context-aware follow-up (FR-011)
session_id = conversation_manager.start_conversation()

# First query
response1 = query_agent("What are the top cart abandonment products?", session_id)
print(f"Q1: {response1['answer'][:200]}...")

# Follow-up with pronoun reference
response2 = query_agent("What about their demographics?", session_id)
print(f"Q2: {response2['answer'][:200]}...")

# Check history
history = conversation_manager.get_history(session_id)
print(f"Conversation length: {len(history)} messages")

# Assertions
assert len(history) >= 4, "Should have at least 4 messages (2 user + 2 assistant)"
assert 'demographic' in response2['answer'].lower() or 'customer' in response2['answer'].lower()
print("✅ Context-aware follow-up test PASSED")
```

**Verification**:
- [ ] Test cell added
- [ ] Validates conversation history (FR-011)
- [ ] Pronoun reference resolved

**References**: plan.md:216, quickstart.md:143-187

---

### Task 17: Implement test for proactive suggestions
**Priority**: High
**Dependencies**: Task 16
**Estimated Time**: 30 minutes

**Description**: Add test cell for proactive suggestions (FR-013).

**File**: `30-mosaic-tool-calling-agent/notebooks/02-test-agent.ipynb` (additional cells)

**Test Cell** (from quickstart.md:189-223):
```python
# Test: Proactive suggestions (FR-013)
response = query_agent("What are the top selling products this month?")

print(f"Answer: {response['answer']}")

# Extract suggestions from response (implementation-specific)
# Agent should include suggestions in response per system prompt
import re
suggestions = re.findall(r'\d+\.\s+(.+)', response['answer'])

print(f"Suggestions found: {len(suggestions)}")
for i, suggestion in enumerate(suggestions, 1):
    print(f"  {i}. {suggestion}")

# Assertions
assert len(suggestions) > 0, "Must provide suggestions (FR-013)"
assert len(suggestions) <= 3, "Max 3 suggestions (research.md)"
print("✅ Proactive suggestions test PASSED")
```

**Verification**:
- [ ] Test cell added
- [ ] Validates FR-013 (suggestions always provided)
- [ ] Validates max 3 suggestions limit

**References**: plan.md:217, quickstart.md:189-223, research.md:88-92

---

## Phase 6: Unit Tests

### Task 18: Create test_tools.py - unit tests for Genie tools [P]
**Priority**: High
**Dependencies**: Tasks 4-6
**Estimated Time**: 60 minutes

**Description**: Create unit tests for UC Functions with mocked Genie API.

**File**: `30-mosaic-tool-calling-agent/tests/test_tools.py`

**Must Include**:
```python
import pytest
from unittest.mock import Mock, patch
import sys
sys.path.append('../src')

from tools.customer_behavior import query_customer_behavior_genie
from tools.inventory import query_inventory_genie

class TestCustomerBehaviorTool:
    @patch('tools.customer_behavior.WorkspaceClient')
    def test_successful_query(self, mock_client):
        # Mock Genie response
        mock_message = Mock()
        mock_message.content = "Top abandoned products are..."
        mock_message.attachments = []

        mock_client.return_value.genie.post_message.return_value = mock_message

        result = query_customer_behavior_genie("What are top abandoned products?")

        assert "[Source: Customer Behavior Genie]" in result
        assert "Top abandoned products" in result

    @patch('tools.customer_behavior.WorkspaceClient')
    def test_error_handling(self, mock_client):
        # Mock Genie error
        mock_client.return_value.genie.post_message.side_effect = Exception("API error")

        # Should handle gracefully (FR-008)
        result = query_customer_behavior_genie("Test query")

        assert "error" in result.lower() or "unavailable" in result.lower()

class TestInventoryTool:
    # Similar tests for inventory tool
    pass
```

**Verification**:
- [ ] Test file created
- [ ] Success cases tested
- [ ] Error handling tested (FR-008)
- [ ] Mocking correctly implemented

**References**: plan.md:218, contracts/test_agent_contract.py

---

### Task 19: Create test fixtures for Genie API responses [P]
**Priority**: Medium
**Dependencies**: Task 18
**Estimated Time**: 30 minutes

**Description**: Create reusable test fixtures for mocking Genie responses.

**File**: `30-mosaic-tool-calling-agent/tests/fixtures/genie_responses.py`

**Must Include**:
```python
from typing import Dict

# Mock Genie responses for testing
CUSTOMER_BEHAVIOR_RESPONSES = {
    "cart_abandonment": {
        "content": "The top 5 cart abandonment products are: Product A (15%), Product B (12%)...",
        "sql": "SELECT product_id, COUNT(*) as abandonment_count FROM cart_abandonment GROUP BY product_id ORDER BY abandonment_count DESC LIMIT 5"
    },
    "customer_segments": {
        "content": "Customer segmentation analysis shows 3 primary segments...",
        "sql": "SELECT segment_name, COUNT(DISTINCT customer_id) FROM customer_segments GROUP BY segment_name"
    }
}

INVENTORY_RESPONSES = {
    "stock_levels": {
        "content": "Current inventory status: 45 products low stock, 12 stockouts...",
        "sql": "SELECT product_id, current_stock, status FROM inventory WHERE status IN ('low', 'out')"
    }
}

def mock_genie_message(response_key: str, domain: str = "customer_behavior") -> Dict:
    """Create mock Genie message object"""
    # Implementation here
    pass
```

**Verification**:
- [ ] Fixtures file created
- [ ] Multiple scenarios covered
- [ ] Reusable across tests

**References**: plan.md:219

---

### Task 20: Create test_agent.py - agent integration tests [P]
**Priority**: High
**Dependencies**: Tasks 18-19
**Estimated Time**: 60 minutes

**Description**: Create integration tests for full agent behavior.

**File**: `30-mosaic-tool-calling-agent/tests/test_agent.py`

**Must Include**:
```python
import pytest
from unittest.mock import patch
import sys
sys.path.append('../src')

# These tests should mirror contract tests but with mocked tools
class TestAgentIntegration:
    def test_agent_handles_single_domain_query(self):
        # Test FR-001, FR-003
        pass

    def test_agent_handles_multi_domain_query(self):
        # Test FR-005, FR-006
        pass

    def test_agent_maintains_conversation_history(self):
        # Test FR-011
        pass

    def test_agent_provides_suggestions(self):
        # Test FR-013
        pass

    def test_agent_handles_tool_failures(self):
        # Test FR-008
        pass
```

**Verification**:
- [ ] Test file created
- [ ] Mirrors contract tests
- [ ] All FRs covered

**References**: plan.md:220, contracts/test_agent_contract.py

---

### Task 21: Map acceptance scenarios from spec.md to test cases [P]
**Priority**: High
**Dependencies**: Task 20
**Estimated Time**: 45 minutes

**Description**: Create test cases for all 5 acceptance scenarios from spec.md.

**File**: `30-mosaic-tool-calling-agent/tests/test_acceptance_scenarios.py`

**Structure** (from contracts/test_agent_contract.py:415-512):
```python
import pytest

class TestAcceptanceScenarios:
    """Map to spec.md acceptance scenarios"""

    def test_scenario_1_multi_domain_cart_and_inventory(self):
        """
        Acceptance Scenario 1: Cart abandonment + inventory issues
        Query: "What products are frequently abandoned in carts and do we have inventory issues?"
        """
        pass

    def test_scenario_2_single_domain_with_suggestions(self):
        """Acceptance Scenario 2: Single domain + suggestions"""
        pass

    def test_scenario_3_sequential_multi_part_query(self):
        """Acceptance Scenario 3: Sequential tool calls"""
        pass

    def test_scenario_4_error_handling(self):
        """Acceptance Scenario 4: Tool error handling"""
        pass

    def test_scenario_5_context_aware_followup(self):
        """Acceptance Scenario 5: Follow-up question"""
        pass
```

**Verification**:
- [ ] All 5 scenarios implemented
- [ ] Tests map 1:1 to spec.md
- [ ] Assertions validate expected behavior

**References**: plan.md:221, contracts/test_agent_contract.py:415-512

---

## Phase 7: MLflow Evaluation

### Task 22: Create eval_dataset.json with test queries
**Priority**: High
**Dependencies**: Tasks 10-17
**Estimated Time**: 45 minutes

**Description**: Create MLflow evaluation dataset with diverse test queries.

**File**: `30-mosaic-tool-calling-agent/evaluation/eval_dataset.json`

**Must Include**:
```json
[
  {
    "request": "What are the top cart abandonment products?",
    "expected_sources": ["customer_behavior"],
    "expected_suggestions": true,
    "complexity": "simple"
  },
  {
    "request": "What products are frequently abandoned in carts and do we have inventory issues with those items?",
    "expected_sources": ["customer_behavior", "inventory"],
    "expected_suggestions": true,
    "complexity": "complex"
  },
  {
    "request": "Show me stockout events in the last 30 days",
    "expected_sources": ["inventory"],
    "expected_suggestions": true,
    "complexity": "simple"
  }
]
```

**Verification**:
- [ ] Dataset created with 10+ queries
- [ ] Mix of simple and complex queries
- [ ] Both domains covered
- [ ] Expected behaviors documented

**References**: plan.md:222

---

### Task 23: Create eval_config.yaml with quality metrics
**Priority**: High
**Dependencies**: Task 22
**Estimated Time**: 30 minutes

**Description**: Define MLflow evaluation metrics.

**File**: `30-mosaic-tool-calling-agent/evaluation/eval_config.yaml`

**Must Include**:
```yaml
metrics:
  - name: relevance
    type: llm_judge
    model: databricks-meta-llama-3-1-70b-instruct

  - name: answer_correctness
    type: llm_judge
    model: databricks-meta-llama-3-1-70b-instruct

  - name: source_citation
    type: custom
    function: check_sources_cited

  - name: suggestions_provided
    type: custom
    function: check_suggestions_present

  - name: response_time
    type: custom
    function: check_under_60_seconds

thresholds:
  relevance: 0.7
  answer_correctness: 0.7
  source_citation: 1.0  # Must always cite sources (FR-009)
  suggestions_provided: 1.0  # Must always suggest (FR-013)
  response_time: 1.0  # Must be under 60s (FR-012)
```

**Verification**:
- [ ] Config file created
- [ ] All key FRs have metrics
- [ ] Thresholds defined

**References**: plan.md:223

---

### Task 24: Create 04-evaluate-agent.ipynb - MLflow eval
**Priority**: High
**Dependencies**: Tasks 22-23
**Estimated Time**: 60 minutes

**Description**: Create notebook for MLflow-based agent evaluation.

**File**: `30-mosaic-tool-calling-agent/notebooks/04-evaluate-agent.ipynb`

**Key Cells**:

**Cell 1: Load evaluation data**
```python
import json
import mlflow

with open('../evaluation/eval_dataset.json', 'r') as f:
    eval_data = json.load(f)

print(f"Loaded {len(eval_data)} evaluation examples")
```

**Cell 2: Define custom metrics**
```python
def check_sources_cited(response):
    """FR-009: Must cite sources"""
    return 1.0 if "[Source:" in response else 0.0

def check_suggestions_present(response):
    """FR-013: Must provide suggestions"""
    # Implementation depends on response format
    return 1.0 if len(extract_suggestions(response)) > 0 else 0.0

def check_under_60_seconds(execution_time_ms):
    """FR-012: Response time < 60s"""
    return 1.0 if execution_time_ms < 60000 else 0.0
```

**Cell 3: Run evaluation** (from research.md:198-206)
```python
model_uri = "models:/multi_tool_calling_agent/latest"

results = mlflow.evaluate(
    model=model_uri,
    data=eval_data,
    model_type="question-answering",
    evaluators=["default"],
    extra_metrics=[
        check_sources_cited,
        check_suggestions_present,
        check_under_60_seconds
    ]
)

print(results.metrics)
```

**Verification**:
- [ ] Notebook created
- [ ] Custom metrics implemented
- [ ] Evaluation runs successfully
- [ ] Results displayed

**References**: plan.md:224, research.md:198-206

---

### Task 25: Validate agent meets FR-012 (60s timeout) and FR-015 (no caching)
**Priority**: High
**Dependencies**: Task 24
**Estimated Time**: 30 minutes

**Description**: Add specific validation cells for performance and caching requirements.

**File**: `30-mosaic-tool-calling-agent/notebooks/04-evaluate-agent.ipynb` (additional cells)

**Cell: Performance validation**
```python
# FR-012: Validate all responses < 60s
import time

performance_tests = [
    "Complex multi-domain query about cart abandonment, inventory, and customer segments",
    "What products are frequently abandoned in carts and do we have inventory issues?",
    "Analyze cart abandonment patterns and correlate with inventory stockouts"
]

for query in performance_tests:
    start = time.time()
    response = agent.invoke({"input": query})
    elapsed_ms = (time.time() - start) * 1000

    print(f"Query: {query[:50]}...")
    print(f"Elapsed: {elapsed_ms:.0f}ms")
    assert elapsed_ms < 60000, f"Query exceeded 60s: {elapsed_ms}ms"
    print("✅ PASS\n")
```

**Cell: No caching validation**
```python
# FR-015: Validate no caching (results always fresh)
query = "What is the current inventory status?"

# Make same query twice with brief pause
response1 = agent.invoke({"input": query})
time.sleep(0.5)
response2 = agent.invoke({"input": query})

# Both should have executed tools (not cached)
print("Query 1 tool calls:", len(response1.get('intermediate_steps', [])))
print("Query 2 tool calls:", len(response2.get('intermediate_steps', [])))

assert len(response1.get('intermediate_steps', [])) > 0, "Should execute tools"
assert len(response2.get('intermediate_steps', [])) > 0, "Should execute tools again (no cache)"
print("✅ No caching verified")
```

**Verification**:
- [ ] Performance tests pass (FR-012)
- [ ] No caching verified (FR-015)

**References**: plan.md:225, spec.md FR-012, FR-015

---

## Phase 8: Deployment

### Task 26: Create 03-deploy-agent.ipynb - Model Serving deployment
**Priority**: High
**Dependencies**: Tasks 10-12, 22-25
**Estimated Time**: 45 minutes

**Description**: Create notebook for deploying agent to Databricks Model Serving.

**File**: `30-mosaic-tool-calling-agent/notebooks/03-deploy-agent.ipynb`

**Key Cells** (from research.md:190-197):

**Cell 1: Deploy to Model Serving**
```python
import mlflow
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import EndpointCoreConfigInput, ServedModelInput

w = WorkspaceClient()

# Get latest model version
model_name = "multi_tool_calling_agent"
model_uri = f"models:/{model_name}/latest"

# Create serving endpoint
endpoint_name = "multi-tool-calling-agent"

w.serving_endpoints.create(
    name=endpoint_name,
    config=EndpointCoreConfigInput(
        served_models=[
            ServedModelInput(
                model_name=model_name,
                model_version="latest",
                workload_size="Small",
                scale_to_zero_enabled=True
            )
        ]
    )
)

print(f"Endpoint created: {endpoint_name}")
print(f"Endpoint URL: https://<workspace-url>/serving-endpoints/{endpoint_name}")
```

**Cell 2: Wait for endpoint ready**
```python
import time

# Wait for endpoint to be ready
while True:
    endpoint = w.serving_endpoints.get(endpoint_name)
    if endpoint.state.ready == "READY":
        print("✅ Endpoint is ready")
        break
    print(f"Endpoint state: {endpoint.state.config_update}")
    time.sleep(30)
```

**Verification**:
- [ ] Notebook created
- [ ] Endpoint creation code works
- [ ] Status checking implemented

**References**: plan.md:226, research.md:190-197

---

### Task 27: Test deployed endpoint
**Priority**: High
**Dependencies**: Task 26
**Estimated Time**: 30 minutes

**Description**: Add test cells to validate deployed endpoint.

**File**: `30-mosaic-tool-calling-agent/notebooks/03-deploy-agent.ipynb` (additional cells)

**Cell: Test endpoint**
```python
import requests
import json

# Query deployed endpoint
endpoint_url = f"https://<workspace-url>/serving-endpoints/{endpoint_name}/invocations"

headers = {
    "Authorization": f"Bearer {dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()}",
    "Content-Type": "application/json"
}

payload = {
    "inputs": {
        "input": "What are the top cart abandonment products?"
    }
}

response = requests.post(endpoint_url, headers=headers, json=payload)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

assert response.status_code == 200, "Endpoint should return 200"
print("✅ Endpoint test PASSED")
```

**Cell: Test conversation continuity**
```python
# Test that conversation history works via endpoint
session_id = str(uuid.uuid4())

# First query
payload1 = {
    "inputs": {
        "input": "What are the top cart abandonment products?",
        "session_id": session_id
    }
}
response1 = requests.post(endpoint_url, headers=headers, json=payload1)
print(f"Q1: {response1.json()}")

# Follow-up
payload2 = {
    "inputs": {
        "input": "What about their demographics?",
        "session_id": session_id
    }
}
response2 = requests.post(endpoint_url, headers=headers, json=payload2)
print(f"Q2: {response2.json()}")

assert response2.status_code == 200
print("✅ Conversation continuity test PASSED")
```

**Verification**:
- [ ] Endpoint responds correctly
- [ ] Conversation history maintained
- [ ] All FR requirements met

**References**: plan.md:227

---

### Task 28: Document deployment process in README.md
**Priority**: Medium
**Dependencies**: Tasks 26-27
**Estimated Time**: 30 minutes

**Description**: Update README.md with deployment instructions.

**File**: `30-mosaic-tool-calling-agent/README.md` (update)

**Add Section**:
```markdown
## Deployment

### Prerequisites
- Agent registered in MLflow (see `notebooks/01-setup-agent.ipynb`)
- Agent evaluated (see `notebooks/04-evaluate-agent.ipynb`)
- Databricks workspace access with Model Serving permissions

### Deploy to Model Serving

1. Run deployment notebook:
   ```bash
   # Open in Databricks
   notebooks/03-deploy-agent.ipynb
   ```

2. Verify endpoint:
   ```bash
   # Check endpoint status
   databricks serving-endpoints get --name multi-tool-calling-agent
   ```

3. Test endpoint:
   ```bash
   curl -X POST https://<workspace-url>/serving-endpoints/multi-tool-calling-agent/invocations \
     -H "Authorization: Bearer $DATABRICKS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"inputs": {"input": "What are the top cart abandonment products?"}}'
   ```

### Monitoring

- **Metrics**: View in Databricks Model Serving UI
- **Logs**: Available in Model Serving endpoint logs
- **MLflow**: Track all queries via MLflow tracking

### Scaling

- Default: Small workload size with scale-to-zero
- For production: Adjust workload size in deployment config
- Auto-scaling: Configured via Databricks Model Serving
```

**Verification**:
- [ ] Deployment section added
- [ ] Instructions complete
- [ ] Examples provided

**References**: plan.md:228

---

## Task Completion Checklist

### Phase 1: Setup & Structure
- [ ] Task 1: Directory structure created
- [ ] Task 2: requirements.txt created
- [ ] Task 3: README.md created

### Phase 2: Genie Tool Functions
- [ ] Task 4: customer_behavior.py implemented (UC Function)
- [ ] Task 5: inventory.py implemented (UC Function)
- [ ] Task 6: genie_client.py utility created

### Phase 3: Agent Configuration
- [ ] Task 7: agent_config.py with domains defined
- [ ] Task 8: prompts.py with system prompt
- [ ] Task 9: domain_relationships.py created

### Phase 4: Agent Definition
- [ ] Task 10: 01-setup-agent.ipynb created (UC Functions + UCFunctionToolkit)
- [ ] Task 11: Conversation management added
- [ ] Task 12: MLflow registration implemented

### Phase 5: Testing Notebooks
- [ ] Task 13: 02-test-agent.ipynb created
- [ ] Task 14: Single-domain test implemented
- [ ] Task 15: Multi-domain test implemented
- [ ] Task 16: Conversation context test implemented
- [ ] Task 17: Proactive suggestions test implemented

### Phase 6: Unit Tests
- [ ] Task 18: test_tools.py created
- [ ] Task 19: Test fixtures created
- [ ] Task 20: test_agent.py created
- [ ] Task 21: Acceptance scenarios mapped

### Phase 7: MLflow Evaluation
- [ ] Task 22: eval_dataset.json created
- [ ] Task 23: eval_config.yaml created
- [ ] Task 24: 04-evaluate-agent.ipynb created
- [ ] Task 25: FR-012 and FR-015 validated

### Phase 8: Deployment
- [ ] Task 26: 03-deploy-agent.ipynb created
- [ ] Task 27: Endpoint testing implemented
- [ ] Task 28: Deployment docs added to README

---

## Notes

### Critical Reminders
1. **Use Unity Catalog Functions** - NOT Agent Code Tools (research.md:107-206)
2. **All code in 30-mosaic-tool-calling-agent/** - NOT 20-agent-brick/ or src/fashion_retail/
3. **UCFunctionToolkit for tool discovery** - NOT manual tool lists
4. **Type hints + Google-style docstrings** - Required for UC Functions
5. **Imports inside function bodies** - UC Function requirement

### Dependencies Overview
- unitycatalog-ai>=0.1.0
- databricks-langchain>=0.1.0
- databricks-sdk>=0.20.0
- mlflow>=2.10.0
- langchain>=0.1.0

### Reference Documents
- Feature Spec: `specs/002-multi-tool-calling/spec.md`
- Implementation Plan: `specs/002-multi-tool-calling/plan.md`
- Research: `specs/002-multi-tool-calling/research.md`
- Data Model: `specs/002-multi-tool-calling/data-model.md`
- Contracts: `specs/002-multi-tool-calling/contracts/`
- Quickstart: `specs/002-multi-tool-calling/quickstart.md`

---

**Ready for implementation with `/implement` command**
