"""Pydantic request/response schemas for the Slack App."""

from typing import List, Optional
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# User models
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    """Payload for creating a new user."""
    username: str
    display_name: str


class User(BaseModel):
    """Returned user object."""
    user_id: str
    username: str
    display_name: str
    created_at: str


# ---------------------------------------------------------------------------
# Direct message models
# ---------------------------------------------------------------------------

class MessageCreate(BaseModel):
    """Payload for sending a direct message."""
    sender_id: str
    receiver_id: str
    content: str


class Message(BaseModel):
    """Returned message object."""
    message_id: str
    sender_id: str
    receiver_id: str
    content: str
    timestamp: str


# ---------------------------------------------------------------------------
# Group models
# ---------------------------------------------------------------------------

class GroupCreate(BaseModel):
    """Payload for creating a group chat.

    `creator_id` is required. `member_ids` is optional — the creator is
    always automatically added as the first member.
    """
    name: str
    creator_id: str
    member_ids: List[str] = []


class Group(BaseModel):
    """Returned group object — matches the confirmed API contract."""
    id: str
    name: str
    creator_id: str
    members: List[str]
    created_at: str


class GroupMessageCreate(BaseModel):
    """Payload for sending a message to a group."""
    sender_id: str
    content: str


class GroupMessage(BaseModel):
    """Returned group message object."""
    id: str
    group_id: str
    sender_id: str
    content: str
    created_at: str


class AddMember(BaseModel):
    """Payload for adding a member to a group."""
    user_id: str
