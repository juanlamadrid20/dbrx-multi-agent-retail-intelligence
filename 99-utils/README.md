# Utilities

This folder contains utility scripts for managing and maintaining the Fashion Retail Intelligence demo.

## Scripts

### `bulk_delete_genie_conversations.py`

Bulk delete conversations from Databricks Genie spaces. Useful for:
- Cleaning up chat history during development/testing
- Privacy maintenance
- Resetting demo environments
- Removing conversations matching specific patterns

#### Usage

```bash
# List all available Genie spaces
python bulk_delete_genie_conversations.py --list-spaces

# Preview what would be deleted (dry run)
python bulk_delete_genie_conversations.py --space-id <space_id> --dry-run

# Delete YOUR conversations from a space
python bulk_delete_genie_conversations.py --space-id <space_id>

# Delete ALL users' conversations (requires CAN MANAGE permission)
python bulk_delete_genie_conversations.py --space-id <space_id> --all-users

# Delete from multiple spaces
python bulk_delete_genie_conversations.py --space-id <id1> --space-id <id2>

# Skip confirmation prompt
python bulk_delete_genie_conversations.py --space-id <space_id> --yes
```

#### Filtering by Title

You can filter which conversations to delete based on their title:

```bash
# Delete conversations with titles starting with specific text
python bulk_delete_genie_conversations.py --space-id <id> \
  --title-prefix "I will provide you a chat"

# Delete conversations containing specific text (case-insensitive)
python bulk_delete_genie_conversations.py --space-id <id> \
  --title-contains "test"

# Delete conversations matching a regex pattern
python bulk_delete_genie_conversations.py --space-id <id> \
  --title-regex "^debug.*session$"

# Combine filters (AND logic)
python bulk_delete_genie_conversations.py --space-id <id> \
  --title-prefix "Test" --title-contains "debug"

# Preview filtered deletions first
python bulk_delete_genie_conversations.py --space-id <id> \
  --title-prefix "I will provide" --dry-run
```

#### Requirements

- `databricks-sdk` package
- Valid Databricks authentication (profile, environment variables, or running on Databricks)
- For `--all-users`: CAN MANAGE permission on the Genie space

#### Permissions

| Action | Required Permission |
|--------|---------------------|
| Delete your own conversations | CAN USE on Genie space |
| Delete all users' conversations | CAN MANAGE on Genie space |
| List spaces | Workspace access |

#### Options Reference

| Option | Description |
|--------|-------------|
| `--space-id <id>` | Genie space ID (can be repeated for multiple spaces) |
| `--all-users` | Include all users' conversations (requires CAN MANAGE) |
| `--dry-run` | Preview deletions without actually deleting |
| `--list-spaces` | List all available Genie spaces and exit |
| `--yes`, `-y` | Skip confirmation prompt |
| `--title-prefix <text>` | Only delete conversations with titles starting with this text |
| `--title-contains <text>` | Only delete conversations containing this text (case-insensitive) |
| `--title-regex <pattern>` | Only delete conversations matching this regex pattern |
