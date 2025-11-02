# Multi-Tool Calling Agent

A conversational AI agent that answers natural language questions across multiple retail data domains using Databricks Mosaic AI Agent Framework and Genie spaces.

## Purpose

This agent provides intelligent insights by:
- Answering natural language questions about customer behavior and inventory management
- Orchestrating queries across multiple Genie data spaces
- Synthesizing information from different domains into coherent responses
- Maintaining conversation context for follow-up questions
- Proactively suggesting related insights from other domains

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Natural Language Query               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│             Multi-Tool Calling Agent (LangChain)             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ChatDatabricks LLM (Llama 3.1 70B)                  │   │
│  │  + System Prompt (FR-006, FR-007, FR-009, FR-013)    │   │
│  │  + Conversation Manager (FR-011)                     │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         UCFunctionToolkit (Unity Catalog Functions)          │
│  ┌─────────────────────┐    ┌──────────────────────────┐   │
│  │ customer_behavior   │    │ inventory_genie          │   │
│  │ _genie              │    │                          │   │
│  │ (UC Function)       │    │ (UC Function)            │   │
│  └──────────┬──────────┘    └───────────┬──────────────┘   │
└─────────────┼──────────────────────────┼───────────────────┘
              │                          │
              ▼                          ▼
┌─────────────────────────┐  ┌──────────────────────────────┐
│ Customer Behavior       │  │ Inventory Management         │
│ Genie Space             │  │ Genie Space                  │
│ (Unity Catalog data)    │  │ (Unity Catalog data)         │
└─────────────────────────┘  └──────────────────────────────┘
```

### Key Components

1. **Unity Catalog Functions (UC Functions)**: Custom tool definitions registered in Unity Catalog
2. **UCFunctionToolkit**: Automatic tool discovery and integration
3. **Agent Executor**: LangChain orchestration with ChatDatabricks LLM
4. **Conversation Manager**: In-memory conversation history tracking (FR-011)
5. **MLflow**: Model logging, tracking, deployment, and evaluation

## Data Domains

### 1. Customer Behavior
- **Genie Space**: Customer Behavior Genie (see `10-genie-rooms/README.genie.customer-behavior.md`)
- **Capabilities**:
  - Cart abandonment analysis
  - Customer segmentation (RFM)
  - Product affinity
  - Purchase patterns
- **UC Function**: `main.default.query_customer_behavior_genie`

### 2. Inventory Management
- **Genie Space**: Inventory Genie (see `10-genie-rooms/README.genie.inventory.md`)
- **Capabilities**:
  - Inventory status
  - Stockout events
  - Inventory constraints
  - Replenishment tracking
- **UC Function**: `main.default.query_inventory_genie`

## Installation

### Prerequisites
- Python 3.12+
- Databricks workspace access
- Unity Catalog permissions for retail datasets
- Databricks Genie MCP tools configured

### Setup

1. Install dependencies:
   ```bash
   cd 30-mosaic-tool-calling-agent
   pip install -r requirements.txt
   ```

2. Configure environment variables:
   ```bash
   # Create .env file
   cat > .env << EOF
   ANTHROPIC_API_KEY=your_api_key_here
   DATABRICKS_HOST=your_workspace_url
   DATABRICKS_TOKEN=your_token_here
   MCP_SERVER_CONFIG_PATH=~/.config/claude/mcp_servers.json
   EOF
   ```

3. Register Unity Catalog Functions:
   ```python
   # Run notebook: notebooks/01-setup-agent.ipynb
   # This will register UC Functions for Genie tools
   ```

## Quick Start

### 1. Setup Agent
Open and run `notebooks/01-setup-agent.ipynb` to:
- Register UC Functions for Genie tools
- Create agent with UCFunctionToolkit
- Configure system prompt and conversation management
- Log agent to MLflow

### 2. Test Agent
Open `notebooks/02-test-agent.ipynb` for interactive testing:

```python
# Simple query
response = query_agent("What are the top cart abandonment products?")
print(response['answer'])

# Multi-domain query
response = query_agent(
    "What products are frequently abandoned in carts and do we have inventory issues?"
)
print(response['answer'])

# Context-aware follow-up
session_id = conversation_manager.start_conversation()
response1 = query_agent("What are the top cart abandonment products?", session_id)
response2 = query_agent("What about their demographics?", session_id)  # Uses context
```

### 3. Evaluate Agent
Open `notebooks/04-evaluate-agent.ipynb` to:
- Run MLflow evaluation with test dataset
- Validate functional requirements (FR-009, FR-012, FR-013, FR-015)
- Check performance and quality metrics

### 4. Deploy Agent
Open `notebooks/03-deploy-agent.ipynb` to:
- Deploy agent to Databricks Model Serving
- Test deployed endpoint
- Monitor performance

## Notebook Execution Order

1. **01-setup-agent.ipynb** - Agent definition and UC Function registration
2. **02-test-agent.ipynb** - Interactive testing and validation
3. **04-evaluate-agent.ipynb** - MLflow evaluation and metrics
4. **03-deploy-agent.ipynb** - Model Serving deployment

## Unity Catalog Function Registration

UC Functions are the official Databricks pattern for custom agent tools:

```python
from unitycatalog.ai.core.databricks import DatabricksFunctionClient

client = DatabricksFunctionClient()

# Register customer behavior tool
from tools.customer_behavior import query_customer_behavior_genie
customer_func = client.create_python_function(
    func=query_customer_behavior_genie,
    catalog="main",
    schema="default",
    replace=True
)
```

**Key Requirements**:
- Type hints on all parameters and returns
- Google-style docstrings with Args, Returns, Examples
- Imports inside function body (not at module level)
- Error handling for graceful failures

## Functional Requirements

This agent implements all functional requirements from [spec.md](../specs/002-multi-tool-calling/spec.md):

- **FR-001**: Accept natural language questions
- **FR-002**: Identify relevant domains
- **FR-003, FR-004**: Query customer behavior and inventory data via Genie
- **FR-005**: Support multi-domain queries
- **FR-006**: Synthesize coherent responses
- **FR-007**: Provide clear, actionable answers
- **FR-008**: Handle failures gracefully
- **FR-009**: Indicate data sources (citations required)
- **FR-011**: Maintain conversation history
- **FR-012**: Respond within 60 seconds
- **FR-013**: Proactive suggestions (1-3 per response)
- **FR-014**: Respect Unity Catalog permissions
- **FR-015**: No result caching (always fetch fresh data)

## Testing

Run unit tests:
```bash
cd tests
pytest test_tools.py -v
pytest test_agent.py -v
pytest test_acceptance_scenarios.py -v
```

Run with coverage:
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## Project Structure

```
30-mosaic-tool-calling-agent/
├── notebooks/
│   ├── 01-setup-agent.ipynb           # Agent definition and UC Functions
│   ├── 02-test-agent.ipynb            # Interactive testing
│   ├── 03-deploy-agent.ipynb          # Model Serving deployment
│   └── 04-evaluate-agent.ipynb        # MLflow evaluation
├── src/
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── customer_behavior.py       # Genie tool for customer behavior
│   │   └── inventory.py               # Genie tool for inventory
│   ├── config/
│   │   ├── __init__.py
│   │   ├── agent_config.py            # Agent and domain configuration
│   │   ├── prompts.py                 # System prompts
│   │   └── domain_relationships.py    # Suggestion graph
│   └── utils/
│       ├── __init__.py
│       └── genie_client.py            # Genie API wrapper utilities
├── tests/
│   ├── fixtures/
│   │   └── genie_responses.py         # Mock Genie responses
│   ├── test_tools.py                  # Unit tests for tools
│   ├── test_agent.py                  # Agent integration tests
│   └── test_acceptance_scenarios.py   # Spec acceptance tests
├── evaluation/
│   ├── eval_dataset.json              # MLflow evaluation dataset
│   └── eval_config.yaml               # Evaluation metrics config
├── requirements.txt                    # Python dependencies
└── README.md                           # This file
```

## Related Documentation

- **Feature Specification**: [../specs/002-multi-tool-calling/spec.md](../specs/002-multi-tool-calling/spec.md)
- **Implementation Plan**: [../specs/002-multi-tool-calling/plan.md](../specs/002-multi-tool-calling/plan.md)
- **Research & Technical Decisions**: [../specs/002-multi-tool-calling/research.md](../specs/002-multi-tool-calling/research.md)
- **Data Model**: [../specs/002-multi-tool-calling/data-model.md](../specs/002-multi-tool-calling/data-model.md)
- **Quickstart Guide**: [../specs/002-multi-tool-calling/quickstart.md](../specs/002-multi-tool-calling/quickstart.md)
- **Customer Behavior Genie**: [../10-genie-rooms/README.genie.customer-behavior.md](../10-genie-rooms/README.genie.customer-behavior.md)
- **Inventory Genie**: [../10-genie-rooms/README.genie.inventory.md](../10-genie-rooms/README.genie.inventory.md)

## Important Notes

- **Standalone Implementation**: This agent is completely separate from `20-agent-brick/` (which is documentation only)
- **No Caching**: All queries fetch fresh data from Genie spaces (FR-015)
- **Unity Catalog Permissions**: All data access respects user's Unity Catalog permissions (FR-014)
- **Performance**: Complex multi-domain queries complete within 60 seconds (FR-012)

## Troubleshooting

### Genie MCP tools not available
```bash
# Verify MCP configuration
cat ~/.config/claude/mcp_servers.json
# Should list: mcp__few-genie-customer-behavior__* tools
```

### Permission denied errors
```bash
# Verify Databricks authentication
databricks auth login
# Test Genie access via web interface
```

### Import errors
```bash
# Ensure correct working directory
cd 30-mosaic-tool-calling-agent
# Check sys.path in notebooks includes ../src
```

## License

See project root for license information.
