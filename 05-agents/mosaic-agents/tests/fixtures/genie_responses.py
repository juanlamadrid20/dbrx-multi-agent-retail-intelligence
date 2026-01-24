"""
Test Fixtures for Genie API Responses

Provides mock responses for testing Genie tools without actual API calls.
"""

from typing import Dict
from unittest.mock import Mock


# Mock Genie responses for Customer Behavior domain
CUSTOMER_BEHAVIOR_RESPONSES = {
    "cart_abandonment": {
        "content": "The top 5 cart abandonment products are: Product A (15%), Product B (12%), Product C (10%), Product D (8%), Product E (7%). The main reasons include high prices and checkout complexity.",
        "sql": "SELECT product_id, product_name, COUNT(*) as abandonment_count, COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as abandonment_rate FROM cart_abandonment GROUP BY product_id, product_name ORDER BY abandonment_count DESC LIMIT 5"
    },
    "customer_segments": {
        "content": "Customer segmentation analysis shows 3 primary segments: High-Value (25%, avg $500/month), Medium-Value (45%, avg $150/month), Low-Value (30%, avg $50/month).",
        "sql": "SELECT segment_name, COUNT(DISTINCT customer_id) as customer_count, AVG(monthly_spend) as avg_spend FROM customer_segments GROUP BY segment_name"
    },
    "purchase_patterns": {
        "content": "Top selling products this month: Electronics (40% of sales), Clothing (30%), Home & Garden (20%), Other (10%).",
        "sql": "SELECT category, SUM(quantity) as total_sold, SUM(revenue) as total_revenue FROM sales WHERE month = CURRENT_MONTH() GROUP BY category ORDER BY total_revenue DESC"
    }
}

# Mock Genie responses for Inventory domain
INVENTORY_RESPONSES = {
    "stock_levels": {
        "content": "Current inventory status: 45 products have low stock (< 10 units), 12 products are out of stock, 234 products have healthy inventory levels.",
        "sql": "SELECT product_id, current_stock, status FROM inventory WHERE status IN ('low', 'out') ORDER BY current_stock ASC"
    },
    "stockout_events": {
        "content": "In the last 30 days: 28 stockout events occurred, affecting 15 unique products. Top affected products: Product A (5 events), Product B (4 events), Product C (3 events).",
        "sql": "SELECT product_id, product_name, COUNT(*) as stockout_count FROM stockout_events WHERE event_date >= CURRENT_DATE - INTERVAL 30 DAYS GROUP BY product_id, product_name ORDER BY stockout_count DESC"
    },
    "inventory_turnover": {
        "content": "Average inventory turnover rate is 6.5x per year. Fast-moving items: Electronics (12x), Fashion (8x). Slow-moving: Furniture (2x).",
        "sql": "SELECT category, AVG(turnover_rate) as avg_turnover FROM inventory_metrics GROUP BY category ORDER BY avg_turnover DESC"
    }
}


def mock_genie_message(response_key: str, domain: str = "customer_behavior") -> Mock:
    """
    Create mock Genie message object for testing.

    Args:
        response_key: Key identifying which response to use (e.g., "cart_abandonment")
        domain: Domain name ("customer_behavior" or "inventory")

    Returns:
        Mock Genie message object with content and attachments
    """
    # Select appropriate response set
    if domain == "customer_behavior":
        responses = CUSTOMER_BEHAVIOR_RESPONSES
    elif domain == "inventory":
        responses = INVENTORY_RESPONSES
    else:
        raise ValueError(f"Unknown domain: {domain}")

    # Get response data
    response_data = responses.get(response_key, {
        "content": "Mock response for testing",
        "sql": None
    })

    # Create mock message
    mock_message = Mock()
    mock_message.content = response_data["content"]

    # Create mock attachment with SQL query if available
    if response_data["sql"]:
        mock_attachment = Mock()
        mock_attachment.query = Mock()
        mock_attachment.query.query = response_data["sql"]
        mock_message.attachments = [mock_attachment]
    else:
        mock_message.attachments = []

    return mock_message


def mock_genie_conversation() -> Mock:
    """Create mock Genie conversation object"""
    mock_conv = Mock()
    mock_conv.conversation_id = "test-conversation-123"
    return mock_conv


def mock_genie_error() -> Exception:
    """Create mock Genie API error for testing error handling"""
    return Exception("Genie API error: Service temporarily unavailable")
