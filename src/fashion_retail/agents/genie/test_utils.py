"""
Genie Testing Utilities

Provides reusable functions for testing Databricks Genie space access and responses.
"""

import time
from datetime import timedelta
from typing import Dict, Optional, Tuple
from databricks.sdk import WorkspaceClient


def test_genie_space(
    space_id: str,
    query: str,
    space_name: str = "Genie Space",
    max_wait_seconds: int = 90,
    verbose: bool = True
) -> Tuple[bool, Optional[str], Optional[str], Optional[dict]]:
    """
    Test access to a Genie space by sending a query and waiting for response.

    Args:
        space_id: Genie space ID
        query: Natural language query to send
        space_name: Display name for the space (for logging)
        max_wait_seconds: Maximum seconds to wait for response
        verbose: Print progress messages

    Returns:
        Tuple of (success, response_content, sql_query, query_result)
        - success: True if query completed successfully
        - response_content: Natural language response from Genie
        - sql_query: Generated SQL query (if available)
        - query_result: Query execution results data (if available)
    """
    w = WorkspaceClient()

    if verbose:
        print(f"Testing {space_name} (space_id: {space_id})...")
        print(f"  Query: '{query}'")

    try:
        # Start conversation
        conversation = w.genie.start_conversation(
            space_id=space_id,
            content=query
        )

        # Wait for response using SDK's built-in waiter
        if verbose:
            print(f"  Waiting for response...", end="", flush=True)

        # Use SDK's wait method with timeout
        try:
            message = w.genie.wait_get_message_genie_completed(
                space_id=space_id,
                conversation_id=conversation.conversation_id,
                message_id=conversation.message_id,
                timeout=timedelta(seconds=max_wait_seconds)
            )

            if verbose:
                print(" Done!")

            # Extract response content
            response_content = message.content if message.content else ""

            # Extract SQL query and results if available
            sql_query = None
            query_result = None
            if message.attachments:
                for attachment in message.attachments:
                    if hasattr(attachment, 'query') and attachment.query:
                        sql_query = attachment.query.query
                        # Get query results if available
                        if hasattr(attachment.query, 'query_result') and attachment.query.query_result:
                            query_result = attachment.query.query_result

            return True, response_content, sql_query, query_result

        except TimeoutError:
            if verbose:
                print(" Timeout!")
                print(f"  Response did not complete within {max_wait_seconds} seconds")
            return False, None, None, None
        except Exception as e:
            if verbose:
                print(" Failed!")
                print(f"  Query failed: {str(e)}")
            return False, None, None, None

    except Exception as e:
        if verbose:
            print(f"\n  Error: {str(e)}")
        return False, None, None, None


def test_all_genie_spaces(
    domains: Dict,
    test_queries: Dict[str, str],
    max_wait_seconds: int = 90,
    verbose: bool = True
) -> bool:
    """
    Test access to all configured Genie spaces.

    Args:
        domains: Dictionary of domain configurations (from agent_config.DOMAINS)
        test_queries: Dictionary mapping domain names to test queries
        max_wait_seconds: Maximum seconds to wait for each response
        verbose: Print progress messages

    Returns:
        True if all spaces are accessible and return valid responses
    """
    if verbose:
        print("Testing Genie Space access...\n")

    all_passed = True

    for domain_name, domain in domains.items():
        test_query = test_queries.get(domain_name, "What data is available?")

        success, response, sql, result = test_genie_space(
            space_id=domain.genie_space_id,
            query=test_query,
            space_name=domain.display_name,
            max_wait_seconds=max_wait_seconds,
            verbose=verbose
        )

        if success:
            if verbose:
                print(f"  ✅ Access granted and response received!")
                if response:
                    preview = response[:300] + "..." if len(response) > 300 else response
                    print(f"  Response: {preview}")
                if sql:
                    sql_preview = sql[:200] + "..." if len(sql) > 200 else sql
                    print(f"  SQL: {sql_preview}")
                if result:
                    print(f"  Query Result: {result}")
                print()
        else:
            if verbose:
                print(f"  ❌ Test failed for {domain.display_name}")
                print(f"     Check permissions or Genie space availability\n")
            all_passed = False

    if verbose:
        if all_passed:
            print("✅ All Genie space tests passed!")
        else:
            print("⚠️  Some Genie space tests failed. Check permissions and try again.")

    return all_passed

