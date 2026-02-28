"""
In-memory storage for the Slack-style messaging app.

All data is stored in module-level dicts/lists so they act as a shared
singleton across the lifetime of the process (or test session when reset).
"""
from typing import Any, Dict, List

# Keyed by user_id -> dict representation of User
users: Dict[str, Dict[str, Any]] = {}

# All direct messages as a flat list of dicts
messages: List[Dict[str, Any]] = []

# Keyed by group_id -> dict representation of Group
groups: Dict[str, Dict[str, Any]] = {}

# Keyed by group_id -> list of group message dicts
# Stored as a dict-of-lists so messages can be fetched per group efficiently.
group_messages: Dict[str, List[Dict[str, Any]]] = {}


def reset_storage() -> None:
    """Clear all in-memory data. Primarily used in tests to ensure isolation."""
    users.clear()
    messages.clear()
    groups.clear()
    group_messages.clear()
