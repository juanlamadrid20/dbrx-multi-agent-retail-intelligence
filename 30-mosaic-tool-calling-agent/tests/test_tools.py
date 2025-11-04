"""
Unit Tests for Genie Tools

Tests UC Functions with mocked Genie API responses.
Validates FR-003, FR-004, FR-008 (error handling).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
sys.path.append('../../src')

from fashion_retail.agents.tools.customer_behavior import query_customer_behavior_genie
from fashion_retail.agents.tools.inventory import query_inventory_genie
from fixtures.genie_responses import mock_genie_message, mock_genie_conversation, mock_genie_error


class TestCustomerBehaviorTool:
    """Tests for customer behavior Genie tool (FR-003)"""

    @patch('fashion_retail.agents.tools.customer_behavior.WorkspaceClient')
    def test_successful_query(self, mock_client_class):
        """Test successful Genie query returns formatted response"""
        # Setup mocks
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_conv = mock_genie_conversation()
        mock_client.genie.start_conversation.return_value = mock_conv

        mock_message = mock_genie_message("cart_abandonment", "customer_behavior")
        mock_client.genie.post_message.return_value = mock_message

        # Execute
        result = query_customer_behavior_genie("What are top abandoned products?")

        # Verify
        assert "[Source: Customer Behavior Genie]" in result
        assert "Product A" in result
        assert "15%" in result
        print("✅ test_successful_query PASSED")

    @patch('fashion_retail.agents.tools.customer_behavior.WorkspaceClient')
    def test_query_with_sql(self, mock_client_class):
        """Test that SQL query is included in response when available"""
        # Setup mocks
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_conv = mock_genie_conversation()
        mock_client.genie.start_conversation.return_value = mock_conv

        mock_message = mock_genie_message("cart_abandonment", "customer_behavior")
        mock_client.genie.post_message.return_value = mock_message

        # Execute
        result = query_customer_behavior_genie("Show cart abandonment")

        # Verify SQL is included
        assert "[SQL Query]:" in result
        assert "SELECT" in result
        print("✅ test_query_with_sql PASSED")

    @patch('fashion_retail.agents.tools.customer_behavior.WorkspaceClient')
    def test_error_handling(self, mock_client_class):
        """Test graceful error handling (FR-008)"""
        # Setup mock to raise error
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.genie.start_conversation.side_effect = mock_genie_error()

        # Execute
        result = query_customer_behavior_genie("Test query")

        # Verify graceful error response
        assert "[Error]" in result
        assert "Unable to retrieve data" in result
        assert not result.startswith("Traceback")  # No raw exception
        print("✅ test_error_handling PASSED")


class TestInventoryTool:
    """Tests for inventory Genie tool (FR-004)"""

    @patch('fashion_retail.agents.tools.inventory.WorkspaceClient')
    def test_successful_query(self, mock_client_class):
        """Test successful inventory query"""
        # Setup mocks
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_conv = mock_genie_conversation()
        mock_client.genie.start_conversation.return_value = mock_conv

        mock_message = mock_genie_message("stock_levels", "inventory")
        mock_client.genie.post_message.return_value = mock_message

        # Execute
        result = query_inventory_genie("What is current stock status?")

        # Verify
        assert "[Source: Inventory Genie]" in result
        assert "45 products" in result
        assert "low stock" in result
        print("✅ test_successful_query PASSED")

    @patch('fashion_retail.agents.tools.inventory.WorkspaceClient')
    def test_error_handling(self, mock_client_class):
        """Test graceful error handling for inventory tool (FR-008)"""
        # Setup mock to raise error
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.genie.start_conversation.side_effect = Exception("Network error")

        # Execute
        result = query_inventory_genie("Test query")

        # Verify graceful error response
        assert "[Error]" in result
        assert "Unable to retrieve data" in result
        print("✅ test_error_handling PASSED")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
