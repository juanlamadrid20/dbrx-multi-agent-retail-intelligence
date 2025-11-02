# Research: Multi-Tool Calling Agent

**Feature**: 002-multi-tool-calling
**Date**: 2025-11-02
**Status**: Complete

## Research Questions

### 1. Agent Framework for Multi-Tool Orchestration

**Decision**: Use Databricks Mosaic AI Agent Framework with function calling capabilities

**Rationale**:
- **Native Databricks Integration**: Seamless Unity Catalog permissions, MLflow tracking, Model Serving
- **Agent Evaluation Built-in**: MLflow-based evaluation and monitoring
- **Production Ready**: Databricks-managed deployment, scaling, and governance
- **Function Calling Support**: Native tool/function calling via Agent Framework
- **Genie Integration**: Direct integration with Databricks Genie spaces as tools
- **Simplified Development**: Agent Framework handles orchestration, we focus on tools and business logic

**Alternatives Considered**:
- Anthropic SDK directly: Lacks Databricks-native features (Unity Catalog, MLflow, deployment)
- LangChain: More complexity than needed, less Databricks integration
- Custom orchestration: Would require reimplementing agent lifecycle management
- AutoGen: External framework, doesn't leverage Databricks platform capabilities

**Implementation Notes**:
- Use Databricks Agent Framework `agents.Agent` for agent creation
- Define tools/functions using `@agents.tool` decorator
- Use MLflow for tracking conversation history and performance
- Deploy as Databricks Model Serving endpoint for production
- Create new tool functions that call Genie spaces (Customer Behavior, Inventory)

---

### 2. Conversation History Management

**Decision**: MLflow-based conversation tracking with Agent Framework state management

**Rationale**:
- Requirement: Full conversation history for context-aware follow-ups
- Constraint: No caching of query results (but conversation != query results)
- **Databricks Agent Framework**: Built-in conversation state management via MLflow
- **Traceability**: Automatic logging of all agent interactions, tool calls, and responses
- **Persistence**: MLflow provides durable storage without custom implementation
- Trade-off: Conversation context needed for understanding vs. fresh data requirement

**Alternatives Considered**:
- In-memory storage: Lost on restart, no observability
- Database storage: Over-engineering when MLflow provides this
- Stateless (no history): Violates FR-011 requirement
- File-based: Unnecessary complexity for session management

**Implementation Notes**:
- Use MLflow's conversation tracking via `mlflow.start_run()` for each session
- Agent Framework maintains conversation state automatically
- Structure: Messages logged with `mlflow.log_param()` and `mlflow.log_metric()`
- Include metadata: tool calls made, domains accessed, execution times
- Use MLflow traces for debugging and conversation replay
- Implement conversation summary for very long histories (edge case handling)

---

### 3. Domain Identification & Routing

**Decision**: LLM-based semantic routing with explicit domain registry

**Rationale**:
- Flexible: Handles ambiguous queries and multi-domain needs
- Extensible: Easy to add new domains without changing routing logic
- Accurate: Claude excels at semantic understanding and classification
- Transparent: Can explain which domains were selected and why

**Alternatives Considered**:
- Keyword matching: Too rigid, misses semantic relationships
- Embedding-based similarity: Adds latency and complexity
- Rule-based classifier: Brittle, hard to maintain as domains grow

**Implementation Notes**:
- Maintain domain registry: `{domain_name: {description, capabilities, tool_names}}`
- Include domain selection as first step in agent reasoning
- Use system prompt to guide domain identification
- Log domain selection decisions for observability

---

### 4. Genie Integration via Custom Tools

**Decision**: Create Unity Catalog Functions (UC Functions) that wrap Genie API calls

**Reference**: [Multi-Agent Genie Documentation](https://docs.databricks.com/aws/en/generative-ai/agent-framework/multi-agent-genie)

**Rationale**:
- **Official Pattern**: Databricks recommends UC Functions for custom tool creation
- **Governance**: UC Functions provide centralized registry and access control
- **Existing Genie Spaces**: Customer Behavior and Inventory Genie rooms already set up (see `10-genie-rooms/`)
- **Agent Framework Integration**: UC Functions automatically work with UCFunctionToolkit
- **MLflow Tracing**: Automatic observability for Genie calls
- **On-Behalf-Of Authorization**: Genie queries respect end user's permissions

**Alternatives Considered**:
- **Python functions only** (Agent Code Tools): No centralized governance, harder to manage
- **MCP tools**: Additional abstraction layer, not needed with UC Functions
- **Direct SQL**: Bypasses Genie's natural language understanding
- **Vector Search**: Genie already provides structured data access, no need for vector search

**Implementation Notes** (based on [Create Custom Tool docs](https://docs.databricks.com/aws/en/generative-ai/agent-framework/create-custom-tool)):

```python
from unitycatalog.ai.core.databricks import DatabricksFunctionClient
from databricks.sdk import WorkspaceClient

client = DatabricksFunctionClient()

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
        str: Natural language answer from Genie, may include SQL query details

    Examples:
        "What are the top 10 products by cart abandonment rate?"
        "Show me customer segments with highest lifetime value"
    """
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient()

    # Start Genie conversation
    conversation = w.genie.start_conversation(
        space_id="<customer_behavior_space_id>"  # From 10-genie-rooms/
    )

    # Post query to Genie
    message = w.genie.post_message(
        conversation_id=conversation.conversation_id,
        content=query
    )

    # Extract answer and optional SQL
    answer = message.content
    sql = message.attachments[0].query.query if message.attachments else None

    result = f"{answer}"
    if sql:
        result += f"\n\n(Query: {sql})"

    return result

# Register as UC Function
function_info = client.create_python_function(
    func=query_customer_behavior_genie,
    catalog="main",
    schema="default",
    replace=True
)

# Similarly for inventory
def query_inventory_genie(query: str) -> str:
    """Query inventory data using Genie natural language interface.

    This tool accesses the Inventory Genie space to answer questions about:
    - Real-time inventory positions across 13 locations
    - Stock movements and transfers
    - Stockout events and lost revenue impact
    - Demand forecasts and accuracy metrics

    Args:
        query (str): Natural language question about inventory

    Returns:
        str: Natural language answer from Genie
    """
    # Similar implementation
    ...

client.create_python_function(
    func=query_inventory_genie,
    catalog="main",
    schema="default",
    replace=True
)
```

**Key Requirements** (from custom tool docs):
- ✅ Type hints required for all parameters and return values
- ✅ Google-style docstrings with Args, Returns, Examples
- ✅ Import libraries within function body (not at module level)
- ✅ No `*args` or `**kwargs` allowed
- ✅ Only Spark-compatible data types

**Conversation Management**:
- Each Genie tool call creates a new conversation (stateless per tool call)
- Agent conversation history is separate from Genie conversation history
- Agent manages multi-turn context, Genie handles individual queries

---

### 5. Response Synthesis Strategy

**Decision**: LLM-based synthesis with structured prompting

**Rationale**:
- Requirement: Synthesize insights from multiple domains coherently
- Requirement: Provide citations to data sources (FR-009)
- LLM excels at narrative generation and information integration
- Flexible formatting based on query complexity

**Alternatives Considered**:
- Template-based: Too rigid for diverse query types
- Separate responses: Violates coherent synthesis requirement (FR-006)
- Custom NLG engine: Over-engineering, reinventing LLM capabilities

**Implementation Notes**:
- Collect all tool results before synthesis
- Structure synthesis prompt with:
  - Original user question
  - Tool results with source attribution
  - Instruction to synthesize coherently
  - Instruction to cite sources
- Include confidence indicators when data is incomplete

---

### 6. Proactive Suggestion Generation

**Decision**: Post-processing step using domain relationship graph

**Rationale**:
- Requirement: Always suggest related insights (FR-013)
- Strategy: Analyze query domain(s), identify related but unused domains
- Generate suggestions based on domain relationships and query context

**Alternatives Considered**:
- Random suggestions: Not contextual or valuable
- Hardcoded rules: Inflexible, hard to maintain
- No suggestions: Violates FR-013

**Implementation Notes**:
- Define domain relationship graph:
  ```
  Customer Behavior <-> Inventory (product stockouts affect purchases)
  Customer Behavior <-> [Future: Marketing, Pricing]
  Inventory <-> [Future: Supply Chain, Replenishment]
  ```
- For each query:
  1. Identify primary domain(s) used
  2. Find related domains not queried
  3. Generate suggestion query for related domain
  4. Append to response as "You might also want to know..."
- Limit suggestions to top 2-3 to avoid overwhelming user

---

### 7. Error Handling & Graceful Degradation

**Decision**: Multi-level error handling with partial response capability

**Rationale**:
- Requirement: Graceful handling when tools fail (FR-008)
- Reality: Genie queries can timeout, Unity Catalog may deny access
- User experience: Partial answer better than complete failure

**Implementation Notes**:
- Error categories:
  1. **Permission denied**: Inform user, suggest accessible alternative
  2. **Tool timeout**: Explain delay, offer to simplify query
  3. **No results**: Confirm understanding, suggest query refinement
  4. **Partial failure**: Return successful results, note what failed
- Include error details in response but frame constructively
- Log all errors for debugging and improvement

---

### 8. Performance Optimization (60-second constraint)

**Decision**: Parallel tool calling with timeout management

**Rationale**:
- Constraint: <60 seconds for complex multi-domain queries (FR-012)
- Strategy: Execute independent tool calls in parallel
- Fallback: Timeout and return partial results if approaching limit

**Implementation Notes**:
- Use `asyncio` for parallel tool execution
- Set per-tool timeout: 50 seconds (leaves buffer for synthesis)
- For sequential dependencies: Chain with timeout tracking
- Monitor total elapsed time, abort if >55 seconds
- Return partial results with explanation if timeout occurs

---

### 9. Testing Strategy

**Decision**: Three-layer testing approach (unit, contract, integration)

**Rationale**:
- Unit tests: Individual component logic (conversation, routing, synthesis)
- Contract tests: MCP tool interface compliance
- Integration tests: End-to-end user scenarios from spec

**Implementation Notes**:
- **Contract tests**: Mock MCP tool responses, verify request/response schemas
- **Integration tests**: Map directly to acceptance scenarios in spec
  - Scenario 1: Multi-domain query (cart abandonment + inventory)
  - Scenario 2: Single domain with suggestions
  - Scenario 3: Sequential multi-part query
  - Scenario 4: Error handling
  - Scenario 5: Follow-up with context
- **Unit tests**: Conversation management, domain routing logic, suggestion generation
- Use `pytest` with fixtures for Genie mock responses
- Integration tests can run against real Genie (optional) or mocks

---

### 10. Unity Catalog Permission Enforcement

**Decision**: Rely on Genie MCP tools for permission enforcement

**Rationale**:
- Genie tools already integrate with Unity Catalog
- Permission errors surface as tool execution errors
- No need to duplicate permission checks in agent layer

**Implementation Notes**:
- Catch permission-related error responses from Genie
- Parse error messages to identify permission issues
- Provide helpful user feedback: "You don't have access to [table/catalog]"
- Log permission denials for audit trail
- FR-014 satisfied through Genie/Unity Catalog integration

---

## Technical Debt & Future Enhancements

### Identified for Later
1. **Conversation persistence**: Current in-memory design doesn't survive restarts
   - Future: Add database or file-based persistence
2. **Conversation summarization**: Long conversations (50+ exchanges) may hit token limits
   - Future: Implement sliding window or summarization strategy
3. **Suggestion intelligence**: Current relationship graph is static
   - Future: Learn from query patterns to improve suggestions
4. **Performance telemetry**: Need to track actual query times and bottlenecks
   - Future: Add OpenTelemetry instrumentation
5. **Multi-user sessions**: Current design assumes single user per session
   - Future: Add user context and multi-tenancy support

### Explicitly Out of Scope
- Custom natural language understanding (use Claude's capabilities)
- Result caching (explicitly prohibited by FR-015)
- Custom authentication (handled by Unity Catalog)
- Query optimization (handled by Genie/Spark)

---

## Mosaic AI Agent Framework Architecture

**Reference**: [Databricks Agent Framework Tools Documentation](https://docs.databricks.com/aws/en/generative-ai/agent-framework/agent-tool)

### Tool Definition Approaches

Databricks Agent Framework supports **three methods** for defining tools:

1. **Unity Catalog Functions** (UC UDFs)
   - Managed in Unity Catalog as central registry
   - Built-in governance and access control
   - Best for: Data transformations on large datasets
   - **Not used in this implementation** (Genie API is better suited)

2. **Agent Code Tools** (Python functions)
   - Implemented directly in agent code
   - Low-latency operations
   - Best for: REST API calls, external integrations
   - **✅ Our choice for Genie integration**

3. **Model Context Protocol (MCP) Tools**
   - Standards-compliant external tools
   - Reusable across agent frameworks
   - **Not needed** (Agent Code Tools simpler for Genie)

### Agent Definition Pattern

Based on [Databricks logging documentation](https://docs.databricks.com/aws/en/generative-ai/agent-framework/log-agent.html):

```python
# File: 30-mosaic-tool-calling-agent/notebooks/01-setup-agent.ipynb

import mlflow
from databricks.sdk import WorkspaceClient
from typing import Dict

# ============================================================================
# 1. Define and Register UC Functions (Unity Catalog Functions approach)
# ============================================================================

from unitycatalog.ai.core.databricks import DatabricksFunctionClient

client = DatabricksFunctionClient()

def query_customer_behavior_genie(query: str) -> str:
    """Query customer behavior data including cart abandonment, purchase patterns, segments.

    This tool accesses the Customer Behavior Genie space to answer questions about:
    - Customer purchasing patterns and lifecycle
    - Cart abandonment rates and products
    - Customer segmentation (RFM analysis)
    - Product affinity and basket analysis

    Args:
        query: Natural language question about customer behavior

    Returns:
        str: Natural language answer from Genie with optional SQL query

    Examples:
        "What are the top 10 products by cart abandonment rate?"
        "Show me customer segments with highest lifetime value"
    """
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient()

    # Start Genie conversation (stateless per call)
    conversation = w.genie.start_conversation(
        space_id="<customer_behavior_space_id>"  # From 10-genie-rooms/
    )

    # Post query to Genie
    message = w.genie.post_message(
        conversation_id=conversation.conversation_id,
        content=query
    )

    # Format response with source citation
    answer = message.content
    sql = message.attachments[0].query.query if message.attachments else None

    result = f"[Source: Customer Behavior Genie]\n{answer}"
    if sql:
        result += f"\n\n[SQL Query]: {sql}"

    return result


def query_inventory_genie(query: str) -> str:
    """Query inventory data using Genie natural language interface.

    This tool accesses the Inventory Genie space to answer questions about:
    - Real-time inventory positions across 13 locations
    - Stock movements and transfers
    - Stockout events and lost revenue impact
    - Demand forecasts and accuracy metrics

    Args:
        query (str): Natural language question about inventory

    Returns:
        str: Natural language answer from Genie with optional SQL query

    Examples:
        "What products are currently out of stock?"
        "Show me stockout events from last month"
    """
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient()

    conversation = w.genie.start_conversation(
        space_id="<inventory_space_id>"
    )

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


# Register both functions as UC Functions
customer_func = client.create_python_function(
    func=query_customer_behavior_genie,
    catalog="main",
    schema="default",
    replace=True
)

inventory_func = client.create_python_function(
    func=query_inventory_genie,
    catalog="main",
    schema="default",
    replace=True
)

# ============================================================================
# 2. Create Agent with UCFunctionToolkit (recommended by Databricks)
# ============================================================================

from databricks_langchain import UCFunctionToolkit, ChatDatabricks
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

# Create toolkit from registered UC Functions
toolkit = UCFunctionToolkit(
    function_names=[
        "main.default.query_customer_behavior_genie",
        "main.default.query_inventory_genie"
    ]
)

# Define system prompt (from prompts.py)
system_prompt = """You are a retail intelligence agent that helps answer questions about customer behavior and inventory.

Your capabilities:
- Query customer behavior data: purchasing patterns, cart abandonment, customer segments
- Query inventory data: stock levels, stockouts, replenishment
- Synthesize insights across both domains
- Provide proactive suggestions for related analyses

Instructions:
1. For multi-domain questions, call BOTH tools in parallel when possible
2. Always cite data sources in your response (e.g., "According to customer behavior data...")
3. After answering, suggest 1-2 related questions the user might want to explore
4. Keep responses clear and actionable
5. If data is unavailable, explain what information is missing

Format:
- Start with direct answer
- Include relevant metrics and numbers
- End with "You might also want to know:" + suggestions
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

# Create agent
llm = ChatDatabricks(endpoint="databricks-meta-llama-3-1-70b-instruct")

agent = create_tool_calling_agent(llm, toolkit.tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=toolkit.tools,  # UC Functions automatically available as tools
    verbose=True,
    return_intermediate_steps=True
)

# ============================================================================
# 3. Log Agent to MLflow
# ============================================================================

# Set registry to Unity Catalog
mlflow.set_registry_uri("databricks-uc")

# Input example for signature inference
input_example = {
    "messages": [
        {
            "role": "user",
            "content": "What products have the highest cart abandonment rates?"
        }
    ]
}

# Log model
with mlflow.start_run():
    logged_agent = mlflow.langchain.log_model(
        lc_model=agent_executor,
        artifact_path="agent",
        input_example=input_example,
        example_no_conversion=True,  # Use input_example as-is
    )

# Register to Unity Catalog
mlflow.register_model(
    model_uri=logged_agent.model_uri,
    name="main.default.retail_intelligence_agent"  # catalog.schema.model_name
)
```

### Deployment Pattern

```python
# File: 30-mosaic-tool-calling-agent/notebooks/03-deploy-agent.ipynb

from databricks import agents
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Deploy registered model to Model Serving endpoint
deployment = w.serving_endpoints.create(
    name="retail-intelligence-agent",
    config={
        "served_entities": [{
            "entity_name": "main.default.retail_intelligence_agent",
            "entity_version": "1",
            "workload_size": "Small",
            "scale_to_zero_enabled": True
        }]
    }
)

# Wait for endpoint to be ready
w.serving_endpoints.wait_get_serving_endpoint_not_updating(
    name="retail-intelligence-agent"
)

# Query the deployed agent
response = w.serving_endpoints.query(
    name="retail-intelligence-agent",
    inputs={
        "messages": [
            {"role": "user", "content": "What products have high cart abandonment?"}
        ]
    }
)

print(response.predictions[0])
```

### Standalone Deployment

This is a **standalone agent**, not integrated with any supervisor pattern. It can be:

1. **Deployed as Model Serving Endpoint**:
   - Users/applications call the endpoint directly
   - RESTful API for external integrations

2. **Used via Notebook**:
   - Interactive development and testing
   - Ad-hoc analysis workflows

3. **Future Integration** (optional):
   - Could be integrated into a multi-agent system later
   - For now: standalone, focused agent for multi-domain queries

---

## Dependencies & Prerequisites

### Required Python Packages

```txt
# 30-mosaic-tool-calling-agent/requirements.txt

# Databricks Platform
databricks-sdk>=0.18.0
mlflow>=2.9.0

# Unity Catalog AI (for UC Functions)
unitycatalog-ai>=0.1.0

# Databricks LangChain (includes UCFunctionToolkit)
databricks-langchain>=0.1.0

# LangChain (required dependencies)
langchain>=0.1.0
langchain-community>=0.0.13
langchain-core>=0.1.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0

# Utilities
python-dotenv>=1.0.0
pydantic>=2.0.0
```

### Databricks Resources Required

1. **Genie Spaces** (already configured in `10-genie-rooms/`)
   - Customer Behavior Genie space
   - Inventory Genie space
   - Space IDs needed for tool configuration

2. **Unity Catalog** (for model registration)
   - Catalog: `main` (or configured catalog)
   - Schema: `default` (or configured schema)
   - Permissions: CREATE MODEL, USE CATALOG, USE SCHEMA

3. **Model Serving** (optional, for production)
   - Serving endpoint creation permissions
   - Small workload size recommended for development

4. **Foundation Model Access**
   - Databricks Foundation Model API access
   - Recommended: `databricks-meta-llama-3-1-70b-instruct`
   - Alternative: Any Databricks-hosted LLM endpoint

### Development Environment

- **Databricks Workspace**: Required (agents are Databricks-native)
- **Databricks Runtime**: 14.3 LTS ML or higher
- **Python**: 3.10+ (Databricks Runtime compatible)
- **Local Development**: Optional (can develop entirely in notebooks)

---

## Success Criteria

Based on functional requirements from spec:
1. ✅ Accept natural language questions (FR-001)
2. ✅ Identify relevant domains (FR-002)
3. ✅ Query customer behavior data (FR-003)
4. ✅ Query inventory data (FR-004)
5. ✅ Support multi-domain queries (FR-005)
6. ✅ Synthesize coherent responses (FR-006)
7. ✅ Provide natural language answers (FR-007)
8. ✅ Handle failures gracefully (FR-008)
9. ✅ Indicate data sources (FR-009)
10. ✅ Support simple and complex queries (FR-010)
11. ✅ Maintain conversation history (FR-011)
12. ✅ Respond within 60 seconds (FR-012)
13. ✅ Proactive suggestions (FR-013)
14. ✅ Respect Unity Catalog permissions (FR-014)
15. ✅ No caching (FR-015)

All requirements have clear implementation paths based on research decisions above.

---

---

## Implementation Summary: Databricks-Native Approach

### Key Decisions Based on Official Documentation

**Tool Pattern**: **Unity Catalog Functions** (UC Functions)
- Recommended by Databricks for custom tool creation
- Centralized registry and governance via Unity Catalog
- Automatic integration with UCFunctionToolkit
- MLflow tracing built-in for observability

**Agent Framework**: **LangChain + UCFunctionToolkit + ChatDatabricks**
- Recommended by Databricks for agent development
- Native integration with MLflow logging (`mlflow.langchain.log_model`)
- Automatic signature inference for Databricks deployment
- Built-in conversation history via `chat_history` placeholder

**Logging Pattern**: **MLflow LangChain Logging**
```python
mlflow.langchain.log_model(
    lc_model=agent_executor,
    artifact_path="agent",
    input_example={"messages": [...]},
    example_no_conversion=True
)
```

**Deployment**: **Unity Catalog + Model Serving**
- Register to UC: `mlflow.register_model(name="catalog.schema.agent")`
- Deploy via Serving Endpoints API
- Auto-scaling with `scale_to_zero_enabled=True`

### Differences from Initial Research

| Aspect | Initial Plan | Updated (Official Docs) |
|--------|-------------|-------------------------|
| Tool Definition | `@agents.tool` decorator | **UC Functions via `DatabricksFunctionClient`** |
| Tool Integration | Manual registration | **UCFunctionToolkit** (automatic discovery) |
| Agent Creation | `agents.Agent()` | `create_tool_calling_agent()` + `AgentExecutor` |
| Genie Integration | MCP tools | **UC Functions wrapping Databricks SDK Genie API** |
| Logging | Generic approach | `mlflow.langchain.log_model()` with input example |
| Model Signature | Manual definition | Automatic inference from input_example |
| Governance | None | **Unity Catalog** (centralized tool registry) |

### Architecture Alignment

**✅ Aligns with Databricks best practices**:
1. LangChain for agent orchestration
2. MLflow for model lifecycle management
3. Unity Catalog for governance
4. Databricks SDK for Genie API access
5. Model Serving for production deployment

**📚 Documentation References**:
- ⭐ [Agent Tools Overview](https://docs.databricks.com/aws/en/generative-ai/agent-framework/agent-tool)
- ⭐ [Create Custom Tools (UC Functions)](https://docs.databricks.com/aws/en/generative-ai/agent-framework/create-custom-tool)
- ⭐ [Multi-Agent with Genie](https://docs.databricks.com/aws/en/generative-ai/agent-framework/multi-agent-genie)
- [Unstructured Retrieval Tools](https://docs.databricks.com/aws/en/generative-ai/agent-framework/unstructured-retrieval-tools)
- [Create Agent](https://docs.databricks.com/aws/en/generative-ai/agent-framework/create-agent.html)
- [Log Agent](https://docs.databricks.com/aws/en/generative-ai/agent-framework/log-agent.html)

---

**Research Status**: ✅ Complete - Updated with official Databricks patterns
**Ready for**: Phase 1 (Design & Contracts)
