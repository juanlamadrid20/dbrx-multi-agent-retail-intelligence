"""
Genie Client Utilities

Provides error handling, response parsing, and timeout management for Genie API calls.
Implements FR-008 (graceful error handling) and FR-012 (timeout management).
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import (
    NotFound, PermissionDenied, ResourceDoesNotExist,
    BadRequest, InternalError, ServiceException
)
from typing import Optional, Dict, Any
import logging
import time

from ...constants import GENIE_QUERY_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


class GenieClientError(Exception):
    """Base exception for Genie client errors."""
    pass


class GenieTimeoutError(GenieClientError):
    """Raised when Genie query exceeds timeout."""
    pass


class GenieAPIError(GenieClientError):
    """Raised when Genie API returns an error."""
    pass


class GenieAuthenticationError(GenieClientError):
    """Raised when authentication with Genie fails."""
    pass


class GenieSpaceNotFoundError(GenieClientError):
    """Raised when the specified Genie space is not found."""
    pass


def safe_genie_query(
    space_id: str,
    query: str,
    timeout_seconds: int = GENIE_QUERY_TIMEOUT_SECONDS
) -> Dict[str, Any]:
    """
    Safely execute Genie query with error handling and timeout.

    This function provides a robust wrapper around Genie API calls with:
    - Timeout management (FR-012: leaves 10s buffer for 60s limit)
    - Specific error handling for known API errors (FR-008: graceful failures)
    - Response parsing
    - Logging

    Args:
        space_id: Genie space identifier
        query: Natural language query
        timeout_seconds: Max execution time (default from constants, leaves 10s buffer)

    Returns:
        Dict with keys:
            - answer (Optional[str]): Natural language response from Genie
            - sql (Optional[str]): SQL query used by Genie (if available)
            - error (Optional[str]): Error message (if query failed)
            - execution_time_ms (int): Query execution time in milliseconds
            - error_type (Optional[str]): Type of error for programmatic handling

    Example:
        >>> result = safe_genie_query("space_123", "What are top products?")
        >>> print(result['answer'])
        >>> if result['sql']:
        >>>     print(f"SQL: {result['sql']}")
    """
    start_time = time.time()

    def _build_error_response(
        error_msg: str,
        error_type: str = "unknown"
    ) -> Dict[str, Any]:
        """Helper to build consistent error responses."""
        return {
            "answer": None,
            "sql": None,
            "error": error_msg,
            "error_type": error_type,
            "execution_time_ms": int((time.time() - start_time) * 1000)
        }

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
            "error_type": None,
            "execution_time_ms": execution_time_ms
        }

    except GenieTimeoutError as e:
        logger.error(f"Genie query timeout: {str(e)}")
        return _build_error_response(
            f"Query timed out after {timeout_seconds}s. Please try a simpler query.",
            error_type="timeout"
        )

    except NotFound as e:
        logger.error(f"Genie space not found: {space_id}")
        return _build_error_response(
            f"Genie space '{space_id}' not found. Please check the space ID.",
            error_type="not_found"
        )

    except PermissionDenied as e:
        logger.error(f"Permission denied for Genie space: {space_id}")
        return _build_error_response(
            "You don't have permission to access this Genie space. Please check your access rights.",
            error_type="permission_denied"
        )

    except ResourceDoesNotExist as e:
        logger.error(f"Genie resource does not exist: {str(e)}")
        return _build_error_response(
            f"The requested Genie resource does not exist: {str(e)}",
            error_type="resource_not_found"
        )

    except BadRequest as e:
        logger.error(f"Bad request to Genie API: {str(e)}")
        return _build_error_response(
            f"Invalid query format. Please rephrase your question. Details: {str(e)}",
            error_type="bad_request"
        )

    except (InternalError, ServiceException) as e:
        logger.error(f"Genie service error: {str(e)}")
        return _build_error_response(
            "Genie service is temporarily unavailable. Please try again later.",
            error_type="service_error"
        )

    except Exception as e:
        # Log unexpected errors with full traceback for debugging
        logger.exception(f"Unexpected error in Genie query: {str(e)}")
        return _build_error_response(
            f"An unexpected error occurred: {str(e)}",
            error_type="unexpected"
        )


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

