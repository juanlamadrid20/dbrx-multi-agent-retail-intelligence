"""
Genie Testing Utilities

Provides reusable functions for testing Databricks Genie space access and responses.
"""

import time
from datetime import timedelta
from typing import Dict, List, Optional, Tuple
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


# ============================================================================
# Response Validation Functions
# ============================================================================

def detect_multi_domain(response: str) -> bool:
    """
    Check if response indicates multi-domain query requiring redirection.
    
    Args:
        response: Genie response text
        
    Returns:
        True if response indicates multi-domain detection
    """
    if not response:
        return False
    
    response_lower = response.lower()
    multi_domain_keywords = [
        "multi-domain", "multiple domains", "inventory", 
        "out of scope", "focuses exclusively", "customer behavior genie",
        "multi-domain agent", "redirect", "use the multi-domain"
    ]
    
    return any(kw in response_lower for kw in multi_domain_keywords)


def is_natural_language(response: str) -> bool:
    """
    Validate response is natural language (not raw SQL).
    
    Args:
        response: Genie response text
        
    Returns:
        True if response appears to be natural language
    """
    if not response:
        return False
    
    # Natural language responses should be longer than 50 chars and not start with SELECT
    return len(response) > 50 and not response.strip().startswith("SELECT")


def has_recommendations(response: str) -> bool:
    """
    Check for actionable recommendations in response.
    
    Args:
        response: Genie response text
        
    Returns:
        True if response contains recommendations
    """
    if not response:
        return False
    
    response_lower = response.lower()
    recommendation_keywords = [
        "recommend", "recommendation", "suggest", "suggestion", 
        "action", "should", "try", "consider", "implement"
    ]
    
    return any(kw in response_lower for kw in recommendation_keywords)


def has_insights(response: str) -> bool:
    """
    Check for data insights/patterns in response.
    
    Args:
        response: Genie response text
        
    Returns:
        True if response contains insights
    """
    if not response:
        return False
    
    response_lower = response.lower()
    insight_keywords = [
        "insight", "indicates", "suggests", "pattern", "trend",
        "shows", "reveals", "means", "implies"
    ]
    
    return any(kw in response_lower for kw in insight_keywords)


def has_redirect_message(response: str) -> bool:
    """
    Check for redirect guidance in multi-domain responses.
    
    Args:
        response: Genie response text
        
    Returns:
        True if response contains redirect message
    """
    if not response:
        return False
    
    response_lower = response.lower()
    redirect_keywords = [
        "multi-domain agent", "use", "instead", "suggested query",
        "redirect", "to answer this question"
    ]
    
    return any(kw in response_lower for kw in redirect_keywords)


def has_explanation(response: str) -> bool:
    """
    Check for scope explanation in multi-domain responses.
    
    Args:
        response: Genie response text
        
    Returns:
        True if response contains explanation
    """
    if not response:
        return False
    
    response_lower = response.lower()
    explanation_keywords = [
        "out of scope", "focuses exclusively", "customer behavior",
        "requires data from multiple domains"
    ]
    
    return any(kw in response_lower for kw in explanation_keywords)


def validate_response(response: str, category: str = "") -> Dict:
    """
    Comprehensive response validation returning all checks.
    
    Args:
        response: Genie response text
        category: Optional category for context (unused but kept for API consistency)
        
    Returns:
        Dictionary with validation results:
        {
            "is_natural_language": bool,
            "is_multi_domain": bool,
            "has_recommendations": Optional[bool],
            "has_insights": Optional[bool],
            "has_redirect_message": Optional[bool],
            "has_explanation": Optional[bool]
        }
    """
    is_multi = detect_multi_domain(response)
    is_natural = is_natural_language(response)
    
    result = {
        "is_natural_language": is_natural,
        "is_multi_domain": is_multi
    }
    
    if is_multi:
        # Multi-domain specific validations
        result["has_redirect_message"] = has_redirect_message(response)
        result["has_explanation"] = has_explanation(response)
        result["has_recommendations"] = None  # N/A for redirects
        result["has_insights"] = None  # N/A for redirects
    else:
        # Normal query validations
        result["has_recommendations"] = has_recommendations(response)
        result["has_insights"] = has_insights(response)
        result["has_redirect_message"] = None
        result["has_explanation"] = None
    
    return result


# ============================================================================
# Test Execution Functions
# ============================================================================

def get_default_configuration_test_queries() -> List[Tuple[str, str]]:
    """
    Return default test queries from configuration notebook.
    
    Returns:
        List of (query, category) tuples
    """
    return [
        # Simple queries (<10s target)
        ("What are the key customer segments?", "Simple - Customer Segmentation"),
        ("What products are trending?", "Simple - Trending Products"),
        ("What is the rate of cart abandonment?", "Simple - Cart Abandonment"),
        
        # Medium complexity queries (<30s target)
        ("What are the key customer segments, and how do their lifetime values differ?", "Medium - Segmentation & CLTV"),
        ("Which customers are at risk of churning, and which are the most loyal?", "Medium - RFM Analysis"),
        ("What is the rate of cart abandonment, and how effective are recovery campaigns?", "Medium - Abandonment & Recovery"),
        
        # Error handling queries
        ("Show me customer data", "Error Handling - Ambiguous Query"),
        
        # Multi-domain detection queries
        ("Which products are frequently abandoned in carts and do we have inventory issues with those items?", "Multi-Domain Detection")
    ]


def format_response_preview(response: str, max_length: int = 400) -> str:
    """
    Helper to truncate responses for display.
    
    Args:
        response: Full response text
        max_length: Maximum length for preview
        
    Returns:
        Truncated response with "..." if needed
    """
    if not response:
        return ""
    
    if len(response) > max_length:
        return response[:max_length] + "..."
    return response


def run_configuration_tests(
    space_id: str,
    space_name: str,
    test_queries: List[Tuple[str, str]],
    max_wait_seconds: int = 90,
    verbose: bool = True
) -> List[Dict]:
    """
    Execute test queries with validation, return results list.
    
    Args:
        space_id: Genie space ID
        space_name: Display name for the space
        test_queries: List of (query, category) tuples
        max_wait_seconds: Maximum seconds to wait for each response
        verbose: Print progress messages
        
    Returns:
        List of result dictionaries with validation results
    """
    results = []
    
    for query, category in test_queries:
        if verbose:
            print(f"\n{'='*60}")
            print(f"Testing: {category}")
            print(f"Query: {query}")
            print(f"{'='*60}")
        
        start_time = time.time()
        success, response, sql, result = test_genie_space(
            space_id=space_id,
            query=query,
            space_name=space_name,
            max_wait_seconds=max_wait_seconds,
            verbose=False
        )
        elapsed_time = time.time() - start_time
        
        if success and response:
            # Validate response
            validation = validate_response(response, category)
            
            # Build result data
            result_data = {
                "category": category,
                "query": query,
                "success": True,
                "elapsed_time": elapsed_time,
                "response_length": len(response),
                **validation
            }
            
            # Print validation results
            if verbose:
                print(f"✅ Response received ({elapsed_time:.2f}s)")
                print(f"   Natural Language: {'✅' if validation['is_natural_language'] else '❌'}")
                
                if validation['is_multi_domain']:
                    print(f"   Multi-Domain Detected: ✅")
                    print(f"   Has Redirect Message: {'✅' if validation['has_redirect_message'] else '❌'}")
                    print(f"   Has Explanation: {'✅' if validation['has_explanation'] else '❌'}")
                    print(f"   Recommendations/Insights: N/A (redirect message)")
                else:
                    print(f"   Has Recommendations: {'✅' if validation['has_recommendations'] else '❌'}")
                    print(f"   Has Insights: {'✅' if validation['has_insights'] else '❌'}")
                
                preview = format_response_preview(response)
                print(f"\n   Response Preview:\n   {preview}")
            
            results.append(result_data)
        else:
            if verbose:
                print(f"❌ Query failed or no response")
            
            results.append({
                "category": category,
                "query": query,
                "success": False,
                "elapsed_time": elapsed_time
            })
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Test Summary: {sum(1 for r in results if r['success'])}/{len(results)} passed")
        print(f"{'='*60}")
    
    return results


def print_test_results(results: List[Dict], verbose: bool = True) -> None:
    """
    Format and print test results summary.
    
    Args:
        results: List of test result dictionaries
        verbose: Print detailed summary
    """
    if not results:
        if verbose:
            print("No test results to display.")
        return
    
    if verbose:
        print(f"\n{'='*60}")
        print("Test Results Summary")
        print(f"{'='*60}")
        
        passed = sum(1 for r in results if r.get('success', False))
        total = len(results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        # Performance summary
        successful_results = [r for r in results if r.get('success', False)]
        if successful_results:
            avg_time = sum(r.get('elapsed_time', 0) for r in successful_results) / len(successful_results)
            print(f"Average Response Time: {avg_time:.2f}s")
        
        # Validation summary
        validation_counts = {
            "natural_language": sum(1 for r in successful_results if r.get('is_natural_language', False)),
            "recommendations": sum(1 for r in successful_results if r.get('has_recommendations', False)),
            "insights": sum(1 for r in successful_results if r.get('has_insights', False)),
            "multi_domain": sum(1 for r in successful_results if r.get('is_multi_domain', False))
        }
        
        print(f"\nValidation Summary:")
        print(f"  Natural Language: {validation_counts['natural_language']}/{len(successful_results)}")
        print(f"  Has Recommendations: {validation_counts['recommendations']}/{len(successful_results)}")
        print(f"  Has Insights: {validation_counts['insights']}/{len(successful_results)}")
        print(f"  Multi-Domain Detected: {validation_counts['multi_domain']}/{len(successful_results)}")


# ============================================================================
# Helper Functions
# ============================================================================

def test_single_query(
    space_id: str,
    query: str,
    space_name: str,
    max_wait_seconds: int = 90,
    verbose: bool = True
) -> Dict:
    """
    Test single query with full response details.
    
    Args:
        space_id: Genie space ID
        query: Natural language query
        space_name: Display name for the space
        max_wait_seconds: Maximum seconds to wait for response
        verbose: Print progress messages
        
    Returns:
        Dictionary with test results:
        {
            "success": bool,
            "query": str,
            "response": Optional[str],
            "sql": Optional[str],
            "result": Optional[dict],
            "elapsed_time": float,
            "validation": Optional[Dict]
        }
    """
    start_time = time.time()
    success, response, sql, result = test_genie_space(
        space_id=space_id,
        query=query,
        space_name=space_name,
        max_wait_seconds=max_wait_seconds,
        verbose=verbose
    )
    elapsed_time = time.time() - start_time
    
    test_result = {
        "success": success,
        "query": query,
        "response": response,
        "sql": sql,
        "result": result,
        "elapsed_time": elapsed_time
    }
    
    if success and response:
        test_result["validation"] = validate_response(response)
    
    return test_result


def get_test_summary(results: List[Dict]) -> Dict:
    """
    Generate summary statistics from test results.
    
    Args:
        results: List of test result dictionaries
        
    Returns:
        Dictionary with summary statistics:
        {
            "total": int,
            "passed": int,
            "failed": int,
            "success_rate": float,
            "avg_response_time": Optional[float],
            "validation_summary": Dict
        }
    """
    if not results:
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "success_rate": 0.0,
            "avg_response_time": None,
            "validation_summary": {}
        }
    
    total = len(results)
    passed = sum(1 for r in results if r.get('success', False))
    failed = total - passed
    success_rate = (passed / total * 100) if total > 0 else 0.0
    
    successful_results = [r for r in results if r.get('success', False)]
    avg_response_time = None
    if successful_results:
        avg_response_time = sum(r.get('elapsed_time', 0) for r in successful_results) / len(successful_results)
    
    validation_summary = {}
    if successful_results:
        validation_summary = {
            "natural_language": sum(1 for r in successful_results if r.get('is_natural_language', False)),
            "recommendations": sum(1 for r in successful_results if r.get('has_recommendations', False)),
            "insights": sum(1 for r in successful_results if r.get('has_insights', False)),
            "multi_domain": sum(1 for r in successful_results if r.get('is_multi_domain', False))
        }
    
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "success_rate": success_rate,
        "avg_response_time": avg_response_time,
        "validation_summary": validation_summary
    }

