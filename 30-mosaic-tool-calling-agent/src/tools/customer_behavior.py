"""
Customer Behavior Genie Tool

Unity Catalog Function for querying the Customer Behavior Genie space.
Implements FR-003: Query customer behavior data via Genie API.
"""

from unitycatalog.ai.core.databricks import DatabricksFunctionClient


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
        "What is the average cart abandonment rate by product category?"
    """
    from databricks.sdk import WorkspaceClient

    # Import inside function body (UC Function requirement)
    w = WorkspaceClient()

    # TODO: Load space_id from config (for now using placeholder)
    # In production, load from environment variable or config file
    space_id = "01f0b7572b3a185d9f69cd89bc4c7579"

    try:
        # Start conversation with Genie space (FR-003)
        conversation = w.genie.start_conversation(space_id=space_id)

        # Post query to Genie (FR-001: natural language question)
        message = w.genie.post_message(
            conversation_id=conversation.conversation_id,
            content=query
        )

        # Extract answer and SQL (if available)
        answer = message.content
        sql = None
        if message.attachments and len(message.attachments) > 0:
            if hasattr(message.attachments[0], 'query'):
                sql = message.attachments[0].query.query

        # Format response with source citation (FR-009)
        result = f"[Source: Customer Behavior Genie]\n{answer}"
        if sql:
            result += f"\n\n[SQL Query]: {sql}"

        return result

    except Exception as e:
        # Graceful error handling (FR-008)
        error_message = f"[Source: Customer Behavior Genie]\n[Error]: Unable to retrieve data. {str(e)}\n\nPlease try rephrasing your question or check data availability."
        return error_message


def register_customer_behavior_tool(catalog: str = "main", schema: str = "default") -> str:
    """Register customer behavior tool as Unity Catalog Function.

    Args:
        catalog (str): Unity Catalog catalog name (default: "main")
        schema (str): Unity Catalog schema name (default: "default")

    Returns:
        str: Full UC Function name (e.g., "juan_dev.genai.query_customer_behavior_genie")

    Raises:
        Exception: If registration fails
    """
    client = DatabricksFunctionClient()

    try:
        func = client.create_python_function(
            func=query_customer_behavior_genie,
            catalog=catalog,
            schema=schema,
            replace=True
        )

        function_name = f"{catalog}.{schema}.query_customer_behavior_genie"
        print(f"✅ Registered UC Function: {function_name}")
        return function_name

    except Exception as e:
        print(f"❌ Failed to register UC Function: {str(e)}")
        raise
