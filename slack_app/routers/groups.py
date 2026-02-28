"""Groups router — create group chats, manage members, and send/receive group messages.

API contract (confirmed):
  POST   /groups                         → 201 Group
  GET    /groups/{group_id}              → 200 Group | 404
  POST   /groups/{group_id}/messages     → 201 GroupMessage | 404 | 403
  GET    /groups/{group_id}/messages     → 200 List[GroupMessage] | 404
  POST   /groups/{group_id}/members      → 200 Group | 404 | 409
"""

from datetime import datetime, timezone
from typing import List
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from slack_app.models import AddMember, Group, GroupCreate, GroupMessage, GroupMessageCreate
from slack_app import storage

router = APIRouter(prefix="/groups", tags=["groups"])


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    """Return current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _group_to_response(group: dict) -> dict:
    """Translate internal storage dict to the public API response shape.

    Internal storage keys: group_id, name, creator_id, members, created_at
    Public API response keys: id, name, creator_id, members, created_at
    """
    return {
        "id": group["group_id"],
        "name": group["name"],
        "creator_id": group["creator_id"],
        "members": group["members"],
        "created_at": group["created_at"],
    }


def _message_to_response(msg: dict) -> dict:
    """Translate internal group-message dict to the public API response shape."""
    return {
        "id": msg["message_id"],
        "group_id": msg["group_id"],
        "sender_id": msg["sender_id"],
        "content": msg["content"],
        "created_at": msg["created_at"],
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED, response_model=Group)
def create_group(payload: GroupCreate) -> dict:
    """Create a new group chat.

    - Validates that the creator exists (404 if not).
    - Automatically includes the creator as the first member.
    - Deduplicates any extra `member_ids` supplied in the payload.
    - Returns the created group with `id`, `name`, `creator_id`, `members`, `created_at`.
    """
    if payload.creator_id not in storage.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{payload.creator_id}' not found.",
        )

    group_id = str(uuid4())

    # Build deduplicated member list, creator always first
    seen: set = set()
    members: List[str] = []
    for uid in [payload.creator_id] + list(payload.member_ids):
        if uid not in seen:
            seen.add(uid)
            members.append(uid)

    group: dict = {
        "group_id": group_id,
        "name": payload.name,
        "creator_id": payload.creator_id,
        "members": members,
        "created_at": _now_iso(),
    }

    storage.groups[group_id] = group
    return _group_to_response(group)


@router.get("/{group_id}", response_model=Group)
def get_group(group_id: str) -> dict:
    """Return group details by group_id.

    Returns 404 if the group does not exist.
    """
    group = storage.groups.get(group_id)
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group '{group_id}' not found.",
        )
    return _group_to_response(group)


@router.post("/{group_id}/messages", status_code=status.HTTP_201_CREATED, response_model=GroupMessage)
def send_group_message(group_id: str, payload: GroupMessageCreate) -> dict:
    """Send a message to a group chat.

    - Returns 404 if the group does not exist.
    - Returns 403 if the sender is not a member of the group.
    """
    group = storage.groups.get(group_id)
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group '{group_id}' not found.",
        )

    if payload.sender_id not in group["members"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sender is not a member of this group.",
        )

    message_id = str(uuid4())
    message: dict = {
        "message_id": message_id,
        "group_id": group_id,
        "sender_id": payload.sender_id,
        "content": payload.content,
        "created_at": _now_iso(),
    }

    storage.group_messages.setdefault(group_id, []).append(message)
    return _message_to_response(message)


@router.get("/{group_id}/messages", response_model=List[GroupMessage])
def get_group_messages(group_id: str) -> List[dict]:
    """Return all messages for a group in chronological order.

    Returns 404 if the group does not exist.
    """
    if group_id not in storage.groups:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group '{group_id}' not found.",
        )

    raw_messages = storage.group_messages.get(group_id, [])
    # ISO-8601 strings sort lexicographically in chronological order
    sorted_messages = sorted(raw_messages, key=lambda m: m["created_at"])
    return [_message_to_response(m) for m in sorted_messages]


@router.post("/{group_id}/members", status_code=status.HTTP_200_OK, response_model=Group)
def add_member(group_id: str, payload: AddMember) -> dict:
    """Add a user to a group.

    - Returns 404 if the group does not exist.
    - Returns 404 if the user does not exist.
    - Returns 409 if the user is already a member of the group.
    - Returns 200 with the updated group on success.
    """
    group = storage.groups.get(group_id)
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group '{group_id}' not found.",
        )

    if payload.user_id not in storage.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{payload.user_id}' not found.",
        )

    if payload.user_id in group["members"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User '{payload.user_id}' is already a member of this group.",
        )

    group["members"].append(payload.user_id)
    return _group_to_response(group)
