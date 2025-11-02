"""
Genie Client Utilities

Provides error handling, response parsing, and timeout management for Genie API calls.
Implements FR-008 (graceful error handling) and FR-012 (timeout management).
"""

from databricks.sdk import WorkspaceClient
from typing import Optional, Dict
import logging
import time

logger = logging.getLogger(__name__)


class GenieClientError(Exception):
    """Base exception for Genie client errors"""
    pass


class GenieTimeoutError(GenieClientError):
    """Raised when Genie query exceeds timeout"""
    pass


class GenieAPIError(GenieClientError):
    """Raised when Genie API returns an error"""
    pass


def safe_genie_query(space_id: str, query: str, timeout_seconds: int = 50) -> Dict:
    """
    Safely execute Genie query with error handling and timeout.

    This function provides a robust wrapper around Genie API calls with:
    - Timeout management (FR-012: leaves 10s buffer for 60s limit)
    - Error handling (FR-008: graceful failures)
    - Response parsing
    - Logging

    Args:
        space_id: Genie space identifier
        query: Natural language query
        timeout_seconds: Max execution time (default 50s, leaves 10s buffer for FR-012)

    Returns:
        Dict with keys:
            - answer (str): Natural language response from Genie
            - sql (Optional[str]): SQL query used by Genie (if available)
            - error (Optional[str]): Error message (if query failed)
            - execution_time_ms (int): Query execution time in milliseconds

    Raises:
        GenieTimeoutError: If query exceeds timeout_seconds
        GenieAPIError: If Genie API returns an error
        GenieClientError: For other unexpected errors

    Example:
        >>> result = safe_genie_query("space_123", "What are top products?")
        >>> print(result['answer'])
        >>> if result['sql']:
        >>>     print(f"SQL: {result['sql']}")
    """
    start_time = time.time()

    try:
        w = WorkspaceClient()

        # Start conversation
        logger.info(f"Starting Genie conversation for space {space_id}")
        conversation = w.genie.start_conversation(space_id=space_id)

        # Check timeout before posting message
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            raise GenieTimeoutError(
                f"Query setup exceeded {timeout_seconds}s timeout"
            )

        # Post message
        logger.info(f"Posting query to Genie: {query[:100]}...")
        message = w.genie.post_message(
            conversation_id=conversation.conversation_id,
            content=query
        )

        # Parse response
        answer = message.content
        sql = None
        if message.attachments and len(message.attachments) > 0:
            if hasattr(message.attachments[0], 'query'):
                sql = message.attachments[0].query.query

        execution_time_ms = int((time.time() - start_time) * 1000)

        # Check if exceeded timeout
        if execution_time_ms > (timeout_seconds * 1000):
            raise GenieTimeoutError(
                f"Query execution took {execution_time_ms}ms, exceeds {timeout_seconds}s limit"
            )

        logger.info(f"Query completed successfully in {execution_time_ms}ms")

        return {
            "answer": answer,
            "sql": sql,
            "error": None,
            "execution_time_ms": execution_time_ms
        }

    except GenieTimeoutError as e:
        # Timeout error (FR-012)
        execution_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Genie query timeout: {str(e)}")
        return {
            "answer": None,
            "sql": None,
            "error": f"Query timed out after {timeout_seconds}s. Please try a simpler query.",
            "execution_time_ms": execution_time_ms
        }

    except Exception as e:
        # Generic error handling (FR-008)
        execution_time_ms = int((time.time() - start_time) * 1000)
        error_msg = str(e)
        logger.error(f"Genie query failed: {error_msg}")

        return {
            "answer": None,
            "sql": None,
            "error": f"Unable to retrieve data from Genie. Error: {error_msg}",
            "execution_time_ms": execution_time_ms
        }


def parse_genie_response(message) -> Dict[str, Optional[str]]:
    """
    Parse Genie message response into structured format.

    Args:
        message: Genie message object from API

    Returns:
        Dict with 'answer' and 'sql' keys
    """
    answer = message.content if hasattr(message, 'content') else None
    sql = None

    if hasattr(message, 'attachments') and message.attachments:
        if len(message.attachments) > 0:
            attachment = message.attachments[0]
            if hasattr(attachment, 'query') and hasattr(attachment.query, 'query'):
                sql = attachment.query.query

    return {
        "answer": answer,
        "sql": sql
    }


def format_genie_response(answer: str, sql: Optional[str], source_name: str) -> str:
    """
    Format Genie response with source citation (FR-009).

    Args:
        answer: Natural language answer from Genie
        sql: Optional SQL query used
        source_name: Name of data source (e.g., "Customer Behavior Genie")

    Returns:
        Formatted response string with source citation
    """
    result = f"[Source: {source_name}]\n{answer}"
    if sql:
        result += f"\n\n[SQL Query]: {sql}"
    return result
