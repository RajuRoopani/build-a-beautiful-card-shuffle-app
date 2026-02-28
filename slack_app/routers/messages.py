"""
Direct Messages router — send and retrieve one-on-one messages.
"""
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException, Query, status

from slack_app import storage
from slack_app.models import Message, MessageCreate

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("", response_model=Message, status_code=status.HTTP_201_CREATED)
def send_message(payload: MessageCreate) -> Message:
    """Send a direct message from one user to another.

    Returns 404 if either the sender or receiver does not exist.
    """
    if payload.sender_id not in storage.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sender '{payload.sender_id}' not found.",
        )
    if payload.receiver_id not in storage.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receiver '{payload.receiver_id}' not found.",
        )

    message_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    message_dict = {
        "message_id": message_id,
        "sender_id": payload.sender_id,
        "receiver_id": payload.receiver_id,
        "content": payload.content,
        "timestamp": now,
    }

    storage.messages.append(message_dict)
    return Message(**message_dict)


@router.get("", response_model=List[Message])
def get_conversation(
    user1: str = Query(..., description="First user ID"),
    user2: str = Query(..., description="Second user ID"),
) -> List[Message]:
    """Return the full conversation between two users, sorted chronologically.

    Matches messages in both directions:
      sender=user1 & receiver=user2  OR  sender=user2 & receiver=user1
    """
    conversation = [
        Message(**msg)
        for msg in storage.messages
        if (
            (msg["sender_id"] == user1 and msg["receiver_id"] == user2)
            or (msg["sender_id"] == user2 and msg["receiver_id"] == user1)
        )
    ]
    # Sort chronologically by ISO timestamp (lexicographic sort is safe for UTC)
    conversation.sort(key=lambda m: m.timestamp)
    return conversation
