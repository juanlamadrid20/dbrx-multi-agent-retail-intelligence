"""
Agent Interface Contract

Defines the public API for the Multi-Tool Calling Agent.
This contract specifies the interface that clients will use to interact with the agent.

Based on Functional Requirements:
- FR-001: Accept natural language questions
- FR-005: Support multi-domain queries
- FR-011: Maintain conversation history
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class QueryRequest:
    """
    User query input to the agent.

    Corresponds to FR-001: System MUST accept natural language questions
    """
    query: str  # Natural language question
    session_id: Optional[str] = None  # For conversation continuity (FR-011)
    context: Optional[Dict] = None  # Additional context (user preferences, etc.)

    def validate(self) -> None:
        """Validate query request"""
        if not self.query or not self.query.strip():
            raise ValueError("Query must be a non-empty string")
        if self.session_id and not isinstance(self.session_id, str):
            raise ValueError("session_id must be a string (UUID)")


@dataclass
class QueryResponse:
    """
    Agent response to a user query.

    Corresponds to:
    - FR-006: Synthesize information from multiple domains
    - FR-007: Provide clear, actionable answers
    - FR-009: Indicate data sources used
    - FR-013: Proactively suggest related insights
    """
    answer: str  # Natural language response (FR-007)
    session_id: str  # Conversation identifier (FR-011)
    sources: List[str]  # Data sources cited (FR-009)
    suggestions: List[str]  # Proactive suggestions (FR-013)
    confidence: str  # "high" | "medium" | "low"
    execution_time_ms: int  # Must be < 60000 (FR-012)
    partial_results: bool  # True if some data unavailable (FR-008)
    error_details: Optional[str] = None  # Error information (FR-008)

    def validate(self) -> None:
        """Validate response"""
        if not self.answer:
            raise ValueError("answer must be non-empty")
        if self.execution_time_ms > 60000:
            raise ValueError(f"Execution time {self.execution_time_ms}ms exceeds 60s limit (FR-012)")
        if self.confidence not in ["high", "medium", "low"]:
            raise ValueError(f"confidence must be high/medium/low, got {self.confidence}")
        if len(self.suggestions) > 3:
            raise ValueError(f"Too many suggestions: {len(self.suggestions)} (max 3)")


class AgentInterface:
    """
    Main interface for the Multi-Tool Calling Agent.

    Contract compliance:
    - All methods must respect Unity Catalog permissions (FR-014)
    - No result caching allowed (FR-015)
    - Must complete within 60 seconds (FR-012)
    """

    def query(self, request: QueryRequest) -> QueryResponse:
        """
        Process a user query and return synthesized response.

        Contract:
        - Input: QueryRequest with natural language query
        - Output: QueryResponse with answer, sources, suggestions
        - Timeout: Must complete within 60 seconds
        - Error Handling: Returns partial results if possible, never raises on data issues
        - Caching: Results NOT cached (always fetch fresh data)

        Functional Requirements Satisfied:
        - FR-001: Accept natural language questions
        - FR-002: Identify relevant domains
        - FR-003, FR-004: Query customer behavior and inventory data
        - FR-005: Support multi-domain queries
        - FR-006: Synthesize coherent responses
        - FR-007: Provide clear answers in natural language
        - FR-008: Handle failures gracefully
        - FR-009: Indicate data sources
        - FR-010: Support simple and complex queries
        - FR-011: Maintain conversation history (via session_id)
        - FR-012: Respond within 60 seconds
        - FR-013: Proactive suggestions
        - FR-014: Respect Unity Catalog permissions
        - FR-015: No caching

        Raises:
        - ValueError: If request validation fails
        - TimeoutError: If query exceeds 60 seconds (exceptional case)
        """
        raise NotImplementedError("Must be implemented by concrete agent class")

    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """
        Retrieve conversation history for a session.

        Contract:
        - Input: session_id (UUID string)
        - Output: List of messages in chronological order
        - Each message: {"role": "user"|"assistant", "content": str, "timestamp": str}

        Functional Requirements Satisfied:
        - FR-011: Maintain full conversation history

        Raises:
        - ValueError: If session_id not found
        """
        raise NotImplementedError("Must be implemented by concrete agent class")

    def start_new_conversation(self) -> str:
        """
        Start a new conversation session.

        Contract:
        - Input: None
        - Output: New session_id (UUID string)
        - Side Effect: Creates empty conversation in history store

        Functional Requirements Satisfied:
        - FR-011: Conversation management
        """
        raise NotImplementedError("Must be implemented by concrete agent class")

    def get_available_domains(self) -> List[Dict]:
        """
        List available data domains for querying.

        Contract:
        - Input: None
        - Output: List of domain metadata
        - Each domain: {"name": str, "display_name": str, "description": str, "capabilities": List[str]}

        Note: Actual data access still subject to Unity Catalog permissions (FR-014)
        """
        raise NotImplementedError("Must be implemented by concrete agent class")


# Type aliases for clarity
SessionId = str
DomainName = str
ToolName = str
