#!/usr/bin/env python3
"""
Bulk Delete Genie Room Conversations

This utility script allows you to bulk delete conversations from Databricks Genie spaces.
Useful for cleaning up chat history during development/testing or for privacy/maintenance.

Usage:
    # Delete all YOUR conversations from a specific space
    python bulk_delete_genie_conversations.py --space-id <space_id>
    
    # Delete ALL users' conversations (requires CAN MANAGE permission)
    python bulk_delete_genie_conversations.py --space-id <space_id> --all-users
    
    # Dry run (preview what would be deleted)
    python bulk_delete_genie_conversations.py --space-id <space_id> --dry-run
    
    # Delete from multiple spaces
    python bulk_delete_genie_conversations.py --space-id <id1> --space-id <id2>
    
    # List all available Genie spaces
    python bulk_delete_genie_conversations.py --list-spaces
    
    # Delete only conversations with titles starting with a specific prefix
    python bulk_delete_genie_conversations.py --space-id <space_id> --title-prefix "I will provide"
    
    # Delete only conversations containing specific text in title
    python bulk_delete_genie_conversations.py --space-id <space_id> --title-contains "test"

Requirements:
    - databricks-sdk
    - Configured Databricks authentication (profile, env vars, or running on Databricks)
"""

import argparse
import re
import sys
from datetime import datetime
from typing import Optional

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import GenieConversation


def get_workspace_client() -> WorkspaceClient:
    """Initialize and return Databricks workspace client."""
    return WorkspaceClient()


def list_genie_spaces(client: WorkspaceClient) -> None:
    """List all available Genie spaces."""
    print("\n📊 Available Genie Spaces:")
    print("-" * 80)
    
    page_token = None
    total_spaces = 0
    
    while True:
        response = client.genie.list_spaces(page_size=50, page_token=page_token)
        
        for space in response.spaces or []:
            total_spaces += 1
            print(f"  ID: {space.space_id}")
            print(f"  Title: {space.title or 'Untitled'}")
            print(f"  Description: {space.description or 'No description'}")
            print("-" * 80)
        
        page_token = response.next_page_token
        if not page_token:
            break
    
    print(f"\nTotal spaces found: {total_spaces}")


def filter_conversations(
    conversations: list[GenieConversation],
    title_prefix: Optional[str] = None,
    title_contains: Optional[str] = None,
    title_regex: Optional[str] = None
) -> list[GenieConversation]:
    """
    Filter conversations by title criteria.
    
    Args:
        conversations: List of conversations to filter
        title_prefix: Only include conversations with titles starting with this string
        title_contains: Only include conversations with titles containing this string
        title_regex: Only include conversations with titles matching this regex pattern
    
    Returns:
        Filtered list of conversations
    """
    filtered = conversations
    
    if title_prefix:
        filtered = [
            c for c in filtered
            if c.title and c.title.startswith(title_prefix)
        ]
    
    if title_contains:
        filtered = [
            c for c in filtered
            if c.title and title_contains.lower() in c.title.lower()
        ]
    
    if title_regex:
        pattern = re.compile(title_regex, re.IGNORECASE)
        filtered = [
            c for c in filtered
            if c.title and pattern.search(c.title)
        ]
    
    return filtered


def list_conversations(
    client: WorkspaceClient,
    space_id: str,
    include_all: bool = False,
    title_prefix: Optional[str] = None,
    title_contains: Optional[str] = None,
    title_regex: Optional[str] = None
) -> list[GenieConversation]:
    """
    List conversations in a Genie space with optional filtering.
    
    Args:
        client: Databricks workspace client
        space_id: Genie space ID
        include_all: If True, include all users' conversations (requires CAN MANAGE)
        title_prefix: Only include conversations with titles starting with this string
        title_contains: Only include conversations with titles containing this string
        title_regex: Only include conversations with titles matching this regex pattern
    
    Returns:
        List of conversation objects (filtered if criteria provided)
    """
    conversations = []
    page_token = None
    
    while True:
        response = client.genie.list_conversations(
            space_id=space_id,
            include_all=include_all,
            page_size=100,
            page_token=page_token
        )
        
        conversations.extend(response.conversations or [])
        
        page_token = response.next_page_token
        if not page_token:
            break
    
    # Apply filters if any are specified
    if title_prefix or title_contains or title_regex:
        conversations = filter_conversations(
            conversations,
            title_prefix=title_prefix,
            title_contains=title_contains,
            title_regex=title_regex
        )
    
    return conversations


def delete_conversations(
    client: WorkspaceClient,
    space_id: str,
    conversations: list[GenieConversation],
    dry_run: bool = False
) -> tuple[int, int]:
    """
    Delete conversations from a Genie space.
    
    Args:
        client: Databricks workspace client
        space_id: Genie space ID
        conversations: List of conversations to delete
        dry_run: If True, only preview deletions
    
    Returns:
        Tuple of (successful_deletes, failed_deletes)
    """
    success_count = 0
    fail_count = 0
    
    for conv in conversations:
        conv_id = conv.conversation_id
        title = conv.title if hasattr(conv, 'title') and conv.title else 'Untitled'
        
        if dry_run:
            print(f"  [DRY RUN] Would delete: {conv_id} ({title})")
            success_count += 1
        else:
            try:
                client.genie.delete_conversation(
                    space_id=space_id,
                    conversation_id=conv_id
                )
                print(f"  ✓ Deleted: {conv_id} ({title})")
                success_count += 1
            except Exception as e:
                print(f"  ✗ Failed to delete {conv_id}: {e}")
                fail_count += 1
    
    return success_count, fail_count


def bulk_delete_genie_conversations(
    space_ids: list[str],
    include_all_users: bool = False,
    dry_run: bool = False,
    title_prefix: Optional[str] = None,
    title_contains: Optional[str] = None,
    title_regex: Optional[str] = None
) -> dict:
    """
    Bulk delete conversations from one or more Genie spaces.
    
    Args:
        space_ids: List of Genie space IDs to clean
        include_all_users: If True, delete all users' conversations (requires CAN MANAGE)
        dry_run: If True, only preview deletions without actually deleting
        title_prefix: Only delete conversations with titles starting with this string
        title_contains: Only delete conversations with titles containing this string
        title_regex: Only delete conversations with titles matching this regex pattern
    
    Returns:
        Summary dictionary with deletion statistics
    """
    client = get_workspace_client()
    
    summary = {
        "spaces_processed": 0,
        "total_conversations": 0,
        "successful_deletes": 0,
        "failed_deletes": 0,
        "dry_run": dry_run
    }
    
    print("\n" + "=" * 80)
    print("🧹 Genie Conversation Bulk Delete Utility")
    print("=" * 80)
    
    if dry_run:
        print("\n⚠️  DRY RUN MODE - No conversations will be deleted\n")
    
    if include_all_users:
        print("📢 Including ALL users' conversations (requires CAN MANAGE permission)\n")
    else:
        print("👤 Deleting only YOUR conversations\n")
    
    # Print filter info
    if title_prefix or title_contains or title_regex:
        print("🔍 Filters applied:")
        if title_prefix:
            print(f"   - Title starts with: \"{title_prefix}\"")
        if title_contains:
            print(f"   - Title contains: \"{title_contains}\"")
        if title_regex:
            print(f"   - Title matches regex: \"{title_regex}\"")
        print()
    
    for space_id in space_ids:
        print(f"\n📁 Processing Space: {space_id}")
        print("-" * 60)
        
        try:
            # Get space details
            space = client.genie.get_space(space_id=space_id)
            print(f"   Space Title: {space.title or 'Untitled'}")
        except Exception as e:
            print(f"   ⚠️  Could not get space details: {e}")
        
        # List conversations (with filters)
        conversations = list_conversations(
            client=client,
            space_id=space_id,
            include_all=include_all_users,
            title_prefix=title_prefix,
            title_contains=title_contains,
            title_regex=title_regex
        )
        
        conv_count = len(conversations)
        print(f"   Found {conv_count} matching conversation(s)")
        
        if conv_count == 0:
            print("   Nothing to delete.")
            summary["spaces_processed"] += 1
            continue
        
        # Delete conversations
        success, fail = delete_conversations(
            client=client,
            space_id=space_id,
            conversations=conversations,
            dry_run=dry_run
        )
        
        summary["spaces_processed"] += 1
        summary["total_conversations"] += conv_count
        summary["successful_deletes"] += success
        summary["failed_deletes"] += fail
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 Summary")
    print("=" * 80)
    print(f"   Spaces processed:     {summary['spaces_processed']}")
    print(f"   Total conversations:  {summary['total_conversations']}")
    if dry_run:
        print(f"   Would delete:         {summary['successful_deletes']}")
    else:
        print(f"   Successfully deleted: {summary['successful_deletes']}")
        print(f"   Failed deletions:     {summary['failed_deletes']}")
    print("=" * 80 + "\n")
    
    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Bulk delete Genie room conversations from Databricks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Delete your conversations from a space
  %(prog)s --space-id 01234567890abcdef
  
  # Delete ALL users' conversations (admin)
  %(prog)s --space-id 01234567890abcdef --all-users
  
  # Preview what would be deleted
  %(prog)s --space-id 01234567890abcdef --dry-run
  
  # List available spaces
  %(prog)s --list-spaces
  
  # Delete conversations starting with specific text
  %(prog)s --space-id <id> --title-prefix "I will provide you a chat"
  
  # Delete conversations containing specific text (case-insensitive)
  %(prog)s --space-id <id> --title-contains "test"
  
  # Delete conversations matching a regex pattern
  %(prog)s --space-id <id> --title-regex "^test.*debug$"
        """
    )
    
    parser.add_argument(
        "--space-id",
        action="append",
        dest="space_ids",
        help="Genie space ID (can be specified multiple times)"
    )
    
    parser.add_argument(
        "--all-users",
        action="store_true",
        help="Delete all users' conversations (requires CAN MANAGE permission)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview deletions without actually deleting"
    )
    
    parser.add_argument(
        "--list-spaces",
        action="store_true",
        help="List all available Genie spaces and exit"
    )
    
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt"
    )
    
    # Title filter arguments
    filter_group = parser.add_argument_group('title filters', 'Filter conversations by title (can be combined)')
    
    filter_group.add_argument(
        "--title-prefix",
        help="Only delete conversations with titles starting with this text"
    )
    
    filter_group.add_argument(
        "--title-contains",
        help="Only delete conversations with titles containing this text (case-insensitive)"
    )
    
    filter_group.add_argument(
        "--title-regex",
        help="Only delete conversations with titles matching this regex pattern"
    )
    
    args = parser.parse_args()
    
    # Initialize client
    try:
        client = get_workspace_client()
    except Exception as e:
        print(f"❌ Failed to initialize Databricks client: {e}")
        print("   Ensure you have valid authentication configured.")
        sys.exit(1)
    
    # List spaces mode
    if args.list_spaces:
        list_genie_spaces(client)
        sys.exit(0)
    
    # Validate space IDs
    if not args.space_ids:
        parser.error("--space-id is required (or use --list-spaces to see available spaces)")
    
    # Confirmation prompt
    if not args.dry_run and not args.yes:
        print("\n⚠️  WARNING: This will permanently delete conversations!")
        if args.all_users:
            print("   You are deleting ALL users' conversations.")
        print(f"   Space IDs: {', '.join(args.space_ids)}")
        if args.title_prefix:
            print(f"   Filter: titles starting with \"{args.title_prefix}\"")
        if args.title_contains:
            print(f"   Filter: titles containing \"{args.title_contains}\"")
        if args.title_regex:
            print(f"   Filter: titles matching regex \"{args.title_regex}\"")
        
        response = input("\nAre you sure you want to continue? [y/N]: ")
        if response.lower() not in ['y', 'yes']:
            print("Aborted.")
            sys.exit(0)
    
    # Execute bulk delete
    summary = bulk_delete_genie_conversations(
        space_ids=args.space_ids,
        include_all_users=args.all_users,
        dry_run=args.dry_run,
        title_prefix=args.title_prefix,
        title_contains=args.title_contains,
        title_regex=args.title_regex
    )
    
    # Exit with appropriate code
    if summary["failed_deletes"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
