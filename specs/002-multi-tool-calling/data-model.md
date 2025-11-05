# Data Model: Multi-Tool Calling Agent

**Feature**: 002-multi-tool-calling
**Date**: 2025-11-02
**Status**: Complete

## Entity Definitions

### 1. Message

Represents a single message in a conversation (user query or agent response).

**Attributes**:
- `role`: str - Either "user" or "assistant"
- `content`: str - The message text
- `timestamp`: datetime - When the message was created
- `tool_calls`: List[ToolCall] | None - Tools invoked (assistant messages only)
- `metadata`: dict - Additional context (domain accessed, execution time, etc.)

**Validation Rules**:
- `role` must be in ["user", "assistant"]
- `content` must be non-empty string
- `timestamp` must be valid ISO 8601 datetime
- `tool_calls` only present when `role == "assistant"`

**State Transitions**: Immutable once created

**Example**:
```python
{
    "role": "user",
    "content": "What products are frequently abandoned in carts?",
    "timestamp": "2025-11-02T10:30:00Z",
    "tool_calls": None,
    "metadata": {}
}
```

---

### 2. Conversation

Represents a complete conversation session with full history.

**Attributes**:
- `session_id`: str (UUID) - Unique conversation identifier
- `messages`: List[Message] - Ordered list of all messages
- `created_at`: datetime - When conversation started
- `last_updated`: datetime - Most recent message timestamp
- `metadata`: dict - Session-level metadata (user_id, context, etc.)

**Validation Rules**:
- `session_id` must be valid UUID
- `messages` must maintain alternating user/assistant pattern (relaxed: assistant can have multiple tool calls)
- `created_at <= last_updated`
- First message must have `role == "user"`

**State Transitions**:
- Created: New conversation with first user message
- Active: Contains >= 1 message, last message < 1 hour old
- Idle: Last message > 1 hour old (may be resumed)

**Relationships**:
- Has many: Messages
- References: Domain contexts (via message metadata)

**Example**:
```python
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "messages": [/* list of Message objects */],
    "created_at": "2025-11-02T10:30:00Z",
    "last_updated": "2025-11-02T10:35:00Z",
    "metadata": {
        "user_id": "user@example.com",
        "domains_accessed": ["customer_behavior", "inventory"]
    }
}
```

---

### 3. ToolCall

Represents an invocation of a data domain tool (Genie MCP).

**Attributes**:
- `tool_id`: str - Unique identifier for this tool execution
- `tool_name`: str - Name of the MCP tool (e.g., "query_space_01f09cdbacf01b5fa7ff7c237365502c")
- `domain`: str - Data domain (e.g., "customer_behavior", "inventory")
- `input_params`: dict - Parameters passed to the tool
- `status`: str - "pending" | "in_progress" | "completed" | "failed" | "timeout"
- `result`: dict | None - Tool execution result (None while pending)
- `error`: str | None - Error message if failed
- `started_at`: datetime - When tool was invoked
- `completed_at`: datetime | None - When tool finished
- `execution_time_ms`: int | None - Duration in milliseconds

**Validation Rules**:
- `tool_name` must be a registered MCP tool
- `domain` must be in registered domain list
- `status` transitions: pending → in_progress → (completed | failed | timeout)
- `result` and `error` are mutually exclusive (only one can be non-None)
- `execution_time_ms = completed_at - started_at` (when completed)

**State Transitions**:
- Pending: Tool call queued
- In Progress: Executing (may include polling for long queries)
- Completed: Successful execution with result
- Failed: Execution error
- Timeout: Exceeded time limit (50s per tool)

**Example**:
```python
{
    "tool_id": "tc_123456",
    "tool_name": "query_space_01f09cdbacf01b5fa7ff7c237365502c",
    "domain": "customer_behavior",
    "input_params": {
        "query": "What are the top 10 products by cart abandonment rate?",
        "conversation_id": "genie_conv_789"
    },
    "status": "completed",
    "result": {
        "answer": "Top abandoned products: Product A (25%), Product B (22%)...",
        "sql_query": "SELECT product_id, COUNT(*) as abandonments FROM ...",
        "conversation_id": "genie_conv_789",
        "message_id": "msg_456"
    },
    "error": None,
    "started_at": "2025-11-02T10:30:05Z",
    "completed_at": "2025-11-02T10:30:12Z",
    "execution_time_ms": 7000
}
```

---

### 4. Domain

Represents a data domain available for querying.

**Attributes**:
- `name`: str - Domain identifier (e.g., "customer_behavior")
- `display_name`: str - Human-readable name ("Customer Behavior")
- `description`: str - What data/insights this domain provides
- `capabilities`: List[str] - Types of questions it can answer
- `mcp_tools`: List[str] - Associated MCP tool names
- `related_domains`: List[str] - Other domains for suggestions
- `enabled`: bool - Whether domain is currently available

**Validation Rules**:
- `name` must be unique, lowercase, snake_case
- `mcp_tools` must reference valid MCP tool registrations
- `related_domains` must reference other registered domain names

**State Transitions**: Static configuration (loaded at startup)

**Relationships**:
- Referenced by: ToolCall (via `domain` field)
- Related to: Other domains (for suggestion generation)

**Example**:
```python
{
    "name": "customer_behavior",
    "display_name": "Customer Behavior",
    "description": "Customer purchasing patterns, cart abandonment, segmentation",
    "capabilities": [
        "Cart abandonment analysis",
        "Purchase pattern identification",
        "Customer segmentation",
        "Product affinity analysis"
    ],
    "mcp_tools": [
        "query_space_01f09cdbacf01b5fa7ff7c237365502c",
        "poll_response_01f09cdbacf01b5fa7ff7c237365502c"
    ],
    "related_domains": ["inventory", "pricing", "marketing"],
    "enabled": True
}
```

---

### 5. AgentResponse

Represents the final synthesized response from the agent.

**Attributes**:
- `answer`: str - Natural language response to user query
- `sources`: List[str] - Data sources cited (e.g., ["customer_behavior.genie", "inventory.genie"])
- `tool_calls_made`: List[ToolCall] - All tool invocations for this response
- `suggestions`: List[str] - Proactive suggestions for related insights
- `confidence`: str - "high" | "medium" | "low" (based on data completeness)
- `total_execution_time_ms`: int - Total time to generate response
- `partial_results`: bool - True if some tool calls failed but response generated

**Validation Rules**:
- `answer` must be non-empty
- `sources` must include at least one source if answer based on data
- `tool_calls_made` must align with sources
- `suggestions` should have 0-3 items (per research decision)
- `total_execution_time_ms < 60000` (60-second constraint)

**Example**:
```python
{
    "answer": "The top products by cart abandonment rate are:\n1. Product A - 25% abandonment\n2. Product B - 22% abandonment\n\nRegarding inventory: Product A currently has low stock (50 units), which may be contributing to customer hesitation.",
    "sources": ["customer_behavior.genie", "inventory.genie"],
    "tool_calls_made": [/* ToolCall objects */],
    "suggestions": [
        "Would you like to see demographic data for customers abandoning these products?",
        "I can analyze historical replenishment times for Product A."
    ],
    "confidence": "high",
    "total_execution_time_ms": 12500,
    "partial_results": False
}
```

---

### 6. DomainRoutingDecision

Represents the agent's decision about which domains to query.

**Attributes**:
- `user_query`: str - Original user question
- `identified_domains`: List[str] - Domains determined to be relevant
- `reasoning`: str - Why these domains were chosen
- `confidence`: float - 0.0-1.0 confidence in routing decision
- `ambiguity_detected`: bool - True if query could map to multiple domains
- `clarification_needed`: bool - True if query is unclear

**Validation Rules**:
- `identified_domains` must be non-empty for non-clarification cases
- `confidence` must be in range [0.0, 1.0]
- If `ambiguity_detected == True`, reasoning should explain alternatives

**Example**:
```python
{
    "user_query": "Why are customers not buying our top products?",
    "identified_domains": ["customer_behavior", "inventory"],
    "reasoning": "Question involves customer purchasing patterns (customer_behavior) and may relate to stock availability (inventory). Multi-domain query recommended.",
    "confidence": 0.85,
    "ambiguity_detected": False,
    "clarification_needed": False
}
```

---

## Data Flow

```
User Query
    ↓
[Domain Routing Decision]
    ↓
[ToolCall(s)] → Execute in parallel/sequence → Results
    ↓
[AgentResponse Synthesis]
    ↓
[Suggestion Generation] → Related domains
    ↓
Final Response to User
    ↓
[Conversation Update] → Append Message with response
```

---

## Persistence Strategy

### In-Memory (Current Phase)
- **Conversation**: Store in Python dict, keyed by session_id
- **Domain Registry**: Load from configuration at startup
- **ToolCalls**: Embedded in Message metadata, no separate storage

### Future Enhancement
- **Conversation**: Persist to database or file system
- **ToolCalls**: Log to observability system for analytics
- **Audit Trail**: Log all permission denials and errors

---

## Validation & Constraints Summary

| Entity | Key Constraint | Enforcement |
|--------|---------------|-------------|
| Message | Role must be user/assistant | Type validation |
| Conversation | First message must be user | Creation logic |
| ToolCall | Execution time < 50s | Timeout mechanism |
| Domain | Names must be unique | Configuration validation |
| AgentResponse | Total time < 60s | Orchestrator timeout |
| Routing Decision | At least one domain (if not clarifying) | Routing logic |

---

## Schema Versioning

**Current Version**: 1.0.0
**Compatibility**: Changes to entity attributes require migration strategy
**Extension Points**: `metadata` fields in Message/Conversation for forward compatibility

---

**Data Model Status**: ✅ Complete
**Ready for**: Contract generation
