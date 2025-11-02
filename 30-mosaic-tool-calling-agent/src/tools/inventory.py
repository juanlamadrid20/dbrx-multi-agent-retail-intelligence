"""
Inventory Management Genie Tool

Unity Catalog Function for querying the Inventory Management Genie space.
Implements FR-004: Query inventory data via Genie API.
"""

from unitycatalog.ai.core.databricks import DatabricksFunctionClient


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
        "Which products have the highest inventory turnover?"
    """
    from databricks.sdk import WorkspaceClient

    # Import inside function body (UC Function requirement)
    w = WorkspaceClient()

    # TODO: Load space_id from config (for now using placeholder)
    # In production, load from environment variable or config file
    space_id = "01f09cdef66116e5940de4b384623be9"

    try:
        # Start conversation with Genie space (FR-004)
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
        result = f"[Source: Inventory Genie]\n{answer}"
        if sql:
            result += f"\n\n[SQL Query]: {sql}"

        return result

    except Exception as e:
        # Graceful error handling (FR-008)
        error_message = f"[Source: Inventory Genie]\n[Error]: Unable to retrieve data. {str(e)}\n\nPlease try rephrasing your question or check data availability."
        return error_message


def register_inventory_tool(catalog: str = "main", schema: str = "default") -> str:
    """Register inventory tool as Unity Catalog Function.

    Args:
        catalog (str): Unity Catalog catalog name (default: "main")
        schema (str): Unity Catalog schema name (default: "default")

    Returns:
        str: Full UC Function name (e.g., "juan_dev.genai.query_inventory_genie")

    Raises:
        Exception: If registration fails
    """
    client = DatabricksFunctionClient()

    try:
        func = client.create_python_function(
            func=query_inventory_genie,
            catalog=catalog,
            schema=schema,
            replace=True
        )

        function_name = f"{catalog}.{schema}.query_inventory_genie"
        print(f"✅ Registered UC Function: {function_name}")
        return function_name

    except Exception as e:
        print(f"❌ Failed to register UC Function: {str(e)}")
        raise
