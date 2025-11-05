"""
Contract Tests for Multi-Tool Calling Agent

These tests verify that the agent implementation adheres to the defined contract.
All tests should FAIL initially (TDD approach) until implementation is complete.

Run with: pytest specs/002-multi-tool-calling/contracts/test_agent_contract.py
"""

import pytest
from datetime import datetime
from typing import Dict, List
import time

# Import will fail until implementation exists - this is expected (TDD)
try:
    from fashion_retail.agent.orchestrator import MultiToolAgent
    from fashion_retail.agent.conversation import ConversationManager
except ImportError:
    pytest.skip("Implementation not yet available", allow_module_level=True)

from .agent_interface import (
    AgentInterface,
    QueryRequest,
    QueryResponse,
    SessionId,
)


class TestAgentInterfaceContract:
    """Test suite for AgentInterface contract compliance"""

    @pytest.fixture
    def agent(self) -> AgentInterface:
        """Fixture providing agent instance for testing"""
        # This will fail until MultiToolAgent is implemented
        return MultiToolAgent()

    @pytest.fixture
    def sample_query_request(self) -> QueryRequest:
        """Sample valid query request"""
        return QueryRequest(
            query="What are the top cart abandonment products?",
            session_id=None,  # New conversation
            context={}
        )

    # -------------------------------------------------------------------------
    # FR-001: Accept natural language questions
    # -------------------------------------------------------------------------

    def test_accepts_natural_language_query(self, agent: AgentInterface, sample_query_request: QueryRequest):
        """
        Contract: Agent must accept and process natural language queries
        FR-001: System MUST accept natural language questions from users
        """
        response = agent.query(sample_query_request)
        assert isinstance(response, QueryResponse)
        assert response.answer  # Non-empty answer

    def test_rejects_empty_query(self, agent: AgentInterface):
        """
        Contract: Empty queries must be rejected
        """
        with pytest.raises(ValueError, match="non-empty"):
            request = QueryRequest(query="", session_id=None)
            request.validate()

    def test_rejects_whitespace_only_query(self, agent: AgentInterface):
        """
        Contract: Whitespace-only queries must be rejected
        """
        with pytest.raises(ValueError, match="non-empty"):
            request = QueryRequest(query="   \n\t  ", session_id=None)
            request.validate()

    # -------------------------------------------------------------------------
    # FR-005: Support multi-domain queries
    # -------------------------------------------------------------------------

    def test_handles_multi_domain_query(self, agent: AgentInterface):
        """
        Contract: Agent must handle queries spanning multiple domains
        FR-005: System MUST support querying multiple data domains within a single user request
        """
        request = QueryRequest(
            query="What products are frequently abandoned in carts and do we have inventory issues?",
            session_id=None
        )
        response = agent.query(request)

        # Response should indicate multiple domains accessed
        assert len(response.sources) >= 2, "Multi-domain query should access multiple sources"
        assert "customer" in str(response.sources).lower() or "behavior" in str(response.sources).lower()
        assert "inventory" in str(response.sources).lower()

    # -------------------------------------------------------------------------
    # FR-006: Synthesize information from multiple domains
    # -------------------------------------------------------------------------

    def test_synthesizes_coherent_response(self, agent: AgentInterface):
        """
        Contract: Multi-domain responses must be coherent and unified
        FR-006: System MUST synthesize information from multiple domains into a coherent, unified response
        """
        request = QueryRequest(
            query="Show me cart abandonment rates and current stock levels for top products",
            session_id=None
        )
        response = agent.query(request)

        # Response should be a single coherent answer, not separate responses
        assert isinstance(response.answer, str)
        assert len(response.answer) > 50  # Substantial synthesized content
        # Should not contain markers like "Response from domain 1:..." (should be unified)
        assert "Response from" not in response.answer

    # -------------------------------------------------------------------------
    # FR-007: Provide clear, actionable answers
    # -------------------------------------------------------------------------

    def test_provides_natural_language_answer(self, agent: AgentInterface, sample_query_request: QueryRequest):
        """
        Contract: Responses must be in clear natural language
        FR-007: System MUST provide clear, actionable answers in natural language format
        """
        response = agent.query(sample_query_request)

        assert isinstance(response.answer, str)
        assert len(response.answer) > 20  # Substantial answer
        # Should not be raw JSON/SQL (basic check)
        assert not response.answer.strip().startswith("{")
        assert not response.answer.strip().upper().startswith("SELECT")

    # -------------------------------------------------------------------------
    # FR-008: Handle failures gracefully
    # -------------------------------------------------------------------------

    def test_handles_tool_failure_gracefully(self, agent: AgentInterface, monkeypatch):
        """
        Contract: Agent must handle tool failures without crashing
        FR-008: System MUST handle cases where data is unavailable or tools fail gracefully
        """
        # This test requires mocking tool failures - implementation-specific
        # For now, verify response structure supports error handling
        request = QueryRequest(query="Test query", session_id=None)
        response = agent.query(request)

        # Response should have error handling fields
        assert hasattr(response, 'partial_results')
        assert hasattr(response, 'error_details')

    # -------------------------------------------------------------------------
    # FR-009: Indicate data sources
    # -------------------------------------------------------------------------

    def test_indicates_data_sources(self, agent: AgentInterface, sample_query_request: QueryRequest):
        """
        Contract: Responses must cite data sources used
        FR-009: System MUST indicate which data sources were used to generate each answer
        """
        response = agent.query(sample_query_request)

        assert isinstance(response.sources, list)
        assert len(response.sources) > 0, "At least one source must be cited"
        # Sources should be meaningful identifiers
        for source in response.sources:
            assert isinstance(source, str)
            assert len(source) > 0

    # -------------------------------------------------------------------------
    # FR-011: Maintain conversation history
    # -------------------------------------------------------------------------

    def test_maintains_conversation_history(self, agent: AgentInterface):
        """
        Contract: Agent must maintain full conversation history
        FR-011: System MUST maintain full conversation history
        """
        # Start new conversation
        session_id = agent.start_new_conversation()
        assert isinstance(session_id, str)

        # Make first query
        request1 = QueryRequest(
            query="What are the top selling products?",
            session_id=session_id
        )
        response1 = agent.query(request1)

        # Check history
        history = agent.get_conversation_history(session_id)
        assert len(history) >= 2  # At least user query + assistant response
        assert history[0]["role"] == "user"
        assert history[0]["content"] == request1.query

    def test_handles_context_aware_followup(self, agent: AgentInterface):
        """
        Contract: Agent must understand context from previous messages
        FR-011: Enable context-aware follow-up questions
        Acceptance Scenario 5 from spec
        """
        # Start conversation
        session_id = agent.start_new_conversation()

        # First query
        request1 = QueryRequest(
            query="What are the top cart abandonment products?",
            session_id=session_id
        )
        response1 = agent.query(request1)

        # Follow-up with pronoun reference
        request2 = QueryRequest(
            query="What about their demographics?",  # "their" = customers from previous query
            session_id=session_id
        )
        response2 = agent.query(request2)

        # Agent should have understood context
        assert response2.answer  # Should have meaningful response
        assert "demographic" in response2.answer.lower() or "customer" in response2.answer.lower()

    # -------------------------------------------------------------------------
    # FR-012: Response time constraint
    # -------------------------------------------------------------------------

    def test_responds_within_60_seconds(self, agent: AgentInterface):
        """
        Contract: Complex multi-domain queries must complete within 60 seconds
        FR-012: System MUST respond to complex multi-domain queries within 60 seconds
        """
        request = QueryRequest(
            query="Complex multi-domain query about cart abandonment, inventory, and customer segments",
            session_id=None
        )

        start_time = time.time()
        response = agent.query(request)
        elapsed_time_ms = (time.time() - start_time) * 1000

        assert elapsed_time_ms < 60000, f"Query took {elapsed_time_ms}ms, exceeds 60s limit"
        assert response.execution_time_ms < 60000

    # -------------------------------------------------------------------------
    # FR-013: Proactive suggestions
    # -------------------------------------------------------------------------

    def test_provides_proactive_suggestions(self, agent: AgentInterface):
        """
        Contract: Agent must always suggest related insights from other domains
        FR-013: System MUST proactively suggest related insights
        """
        request = QueryRequest(
            query="What are the top selling products this month?",
            session_id=None
        )
        response = agent.query(request)

        assert isinstance(response.suggestions, list)
        assert len(response.suggestions) > 0, "Agent must provide at least one suggestion (FR-013)"
        assert len(response.suggestions) <= 3, "Limit suggestions to 3 (per research.md)"

        # Suggestions should be meaningful strings
        for suggestion in response.suggestions:
            assert isinstance(suggestion, str)
            assert len(suggestion) > 10  # Non-trivial suggestion

    # -------------------------------------------------------------------------
    # FR-014: Unity Catalog permissions
    # -------------------------------------------------------------------------

    def test_respects_unity_catalog_permissions(self, agent: AgentInterface):
        """
        Contract: Agent must respect Unity Catalog permissions (enforced by Genie tools)
        FR-014: System MUST respect data access permissions as defined in Unity Catalog
        """
        # This is primarily enforced by Genie MCP tools, but agent should handle permission errors
        # For contract test, verify error handling structure exists
        request = QueryRequest(query="Query requiring data access", session_id=None)
        response = agent.query(request)

        # Response should support permission error reporting
        assert hasattr(response, 'error_details')
        assert hasattr(response, 'partial_results')

    # -------------------------------------------------------------------------
    # FR-015: No caching
    # -------------------------------------------------------------------------

    def test_no_result_caching(self, agent: AgentInterface):
        """
        Contract: Query results must NOT be cached (always fresh data)
        FR-015: System MUST NOT cache query results
        """
        request = QueryRequest(
            query="What is the current inventory status?",
            session_id=None
        )

        # Make same query twice
        response1 = agent.query(request)
        time.sleep(0.1)  # Brief pause
        response2 = agent.query(request)

        # Both should have executed (not cached)
        # We can't directly verify no caching, but execution times should both be > 0
        assert response1.execution_time_ms > 0
        assert response2.execution_time_ms > 0
        # Ideally would verify tool calls were actually made both times (implementation-specific)

    # -------------------------------------------------------------------------
    # Response Structure Validation
    # -------------------------------------------------------------------------

    def test_response_structure_compliance(self, agent: AgentInterface, sample_query_request: QueryRequest):
        """
        Contract: All responses must conform to QueryResponse schema
        """
        response = agent.query(sample_query_request)

        # Required fields
        assert hasattr(response, 'answer')
        assert hasattr(response, 'session_id')
        assert hasattr(response, 'sources')
        assert hasattr(response, 'suggestions')
        assert hasattr(response, 'confidence')
        assert hasattr(response, 'execution_time_ms')
        assert hasattr(response, 'partial_results')

        # Validate response
        response.validate()

    def test_confidence_levels(self, agent: AgentInterface, sample_query_request: QueryRequest):
        """
        Contract: Confidence must be one of: high, medium, low
        """
        response = agent.query(sample_query_request)
        assert response.confidence in ["high", "medium", "low"]

    # -------------------------------------------------------------------------
    # Domain Registry
    # -------------------------------------------------------------------------

    def test_provides_domain_information(self, agent: AgentInterface):
        """
        Contract: Agent must provide information about available domains
        """
        domains = agent.get_available_domains()

        assert isinstance(domains, list)
        assert len(domains) >= 2, "Should have at least Customer Behavior and Inventory domains"

        # Each domain should have required fields
        for domain in domains:
            assert "name" in domain
            assert "display_name" in domain
            assert "description" in domain
            assert "capabilities" in domain


class TestConversationManagement:
    """Tests for conversation lifecycle management"""

    @pytest.fixture
    def agent(self) -> AgentInterface:
        """Agent instance"""
        return MultiToolAgent()

    def test_start_new_conversation_returns_uuid(self, agent: AgentInterface):
        """New conversations must have unique session IDs"""
        session_id1 = agent.start_new_conversation()
        session_id2 = agent.start_new_conversation()

        assert isinstance(session_id1, str)
        assert isinstance(session_id2, str)
        assert session_id1 != session_id2  # Must be unique

    def test_get_conversation_history_empty_session(self, agent: AgentInterface):
        """New conversation should have empty history"""
        session_id = agent.start_new_conversation()
        history = agent.get_conversation_history(session_id)

        assert isinstance(history, list)
        assert len(history) == 0  # No messages yet

    def test_get_conversation_history_invalid_session(self, agent: AgentInterface):
        """Requesting history for non-existent session should raise error"""
        with pytest.raises(ValueError, match="not found"):
            agent.get_conversation_history("invalid-session-id-12345")

    def test_conversation_history_order(self, agent: AgentInterface):
        """Conversation history must be in chronological order"""
        session_id = agent.start_new_conversation()

        # Make multiple queries
        for i in range(3):
            request = QueryRequest(
                query=f"Query number {i+1}",
                session_id=session_id
            )
            agent.query(request)

        history = agent.get_conversation_history(session_id)

        # History should be ordered chronologically
        timestamps = [msg.get("timestamp") for msg in history if "timestamp" in msg]
        assert timestamps == sorted(timestamps), "History must be in chronological order"


# -------------------------------------------------------------------------
# Integration Test Scenarios (from spec acceptance scenarios)
# -------------------------------------------------------------------------

class TestAcceptanceScenarios:
    """
    Integration tests mapping to acceptance scenarios in spec.md
    These test complete user journeys end-to-end.
    """

    @pytest.fixture
    def agent(self) -> AgentInterface:
        return MultiToolAgent()

    def test_scenario_1_multi_domain_cart_and_inventory(self, agent: AgentInterface):
        """
        Acceptance Scenario 1 from spec:
        User asks about cart abandonment + inventory issues for products
        """
        request = QueryRequest(
            query="What products are frequently abandoned in carts and do we have inventory issues with those items?",
            session_id=None
        )
        response = agent.query(request)

        # Must query both domains
        assert len(response.sources) >= 2
        # Should mention both cart abandonment and inventory
        assert ("abandon" in response.answer.lower() or "cart" in response.answer.lower())
        assert ("inventory" in response.answer.lower() or "stock" in response.answer.lower())

    def test_scenario_2_single_domain_with_suggestions(self, agent: AgentInterface):
        """
        Acceptance Scenario 2 from spec:
        User asks about single domain, agent suggests related insights
        """
        request = QueryRequest(
            query="What are the top selling products this month?",
            session_id=None
        )
        response = agent.query(request)

        # Should query customer behavior/sales
        assert any("customer" in s.lower() or "behavior" in s.lower() or "sales" in s.lower()
                   for s in response.sources)
        # Must provide suggestions (FR-013)
        assert len(response.suggestions) > 0

    def test_scenario_3_sequential_multi_part_query(self, agent: AgentInterface):
        """
        Acceptance Scenario 3 from spec:
        Complex query requiring sequential tool calls
        """
        request = QueryRequest(
            query="Find customers who abandoned carts, then check if those products had stockout events",
            session_id=None
        )
        response = agent.query(request)

        # Should access both customer behavior and inventory
        assert len(response.sources) >= 2
        # Should complete within timeout
        assert response.execution_time_ms < 60000

    def test_scenario_4_error_handling(self, agent: AgentInterface):
        """
        Acceptance Scenario 4 from spec:
        Tool error should result in meaningful partial response
        """
        # This would require mocking tool failures in real implementation
        # For contract test, verify response supports error scenarios
        request = QueryRequest(query="Any valid query", session_id=None)
        response = agent.query(request)

        assert hasattr(response, 'partial_results')
        assert hasattr(response, 'error_details')

    def test_scenario_5_context_aware_followup(self, agent: AgentInterface):
        """
        Acceptance Scenario 5 from spec:
        Follow-up question referencing previous context
        """
        session_id = agent.start_new_conversation()

        # Initial query
        request1 = QueryRequest(
            query="What are the top cart abandonment products?",
            session_id=session_id
        )
        response1 = agent.query(request1)

        # Follow-up with context reference
        request2 = QueryRequest(
            query="What about their demographics?",
            session_id=session_id
        )
        response2 = agent.query(request2)

        # Should understand "their" refers to customers from first query
        assert response2.answer
        assert len(response2.answer) > 20  # Meaningful response
