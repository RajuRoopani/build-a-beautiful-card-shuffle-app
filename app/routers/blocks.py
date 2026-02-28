"""
app/routers/blocks.py
─────────────────────
User blocking / unblocking and blocked-list retrieval.

Endpoints:
  POST   /users/{user_id}/block   — Block another user; removes any follow links.
  DELETE /users/{user_id}/block   — Unblock a user.
  GET    /users/{user_id}/blocked — List all users blocked by user_id.
"""

from typing import List

from fastapi import APIRouter, HTTPException

from app.models import (
    BlockRequest,
    UserResponse,
    blocks,
    followers,
    follows,
    users_db,
)

router = APIRouter(prefix="/users", tags=["blocks"])


def _user_to_response(user: dict) -> UserResponse:
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        display_name=user["display_name"],
        bio=user.get("bio"),
    )


@router.post("/{user_id}/block", status_code=200)
def block_user(user_id: str, body: BlockRequest) -> dict:
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    if body.blocked_user_id not in users_db:
        raise HTTPException(status_code=404, detail="Target user not found")

    if user_id == body.blocked_user_id:
        raise HTTPException(status_code=400, detail="Cannot block yourself")

    # Prevent double-block
    if body.blocked_user_id in blocks.get(user_id, set()):
        raise HTTPException(status_code=400, detail="Already blocked this user")

    blocks.setdefault(user_id, set()).add(body.blocked_user_id)

    # Remove follow in both directions
    follows.setdefault(user_id, set()).discard(body.blocked_user_id)
    followers.setdefault(body.blocked_user_id, set()).discard(user_id)
    follows.setdefault(body.blocked_user_id, set()).discard(user_id)
    followers.setdefault(user_id, set()).discard(body.blocked_user_id)

    return {"detail": f"User {user_id} has blocked {body.blocked_user_id}"}


@router.delete("/{user_id}/block", status_code=200)
def unblock_user(user_id: str, body: BlockRequest) -> dict:
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    # Return 400 if not blocked
    if body.blocked_user_id not in blocks.get(user_id, set()):
        raise HTTPException(status_code=400, detail="Not blocking this user")

    blocks.setdefault(user_id, set()).discard(body.blocked_user_id)

    return {"detail": f"User {user_id} has unblocked {body.blocked_user_id}"}


@router.get("/{user_id}/blocked", response_model=List[UserResponse])
def get_blocked(user_id: str) -> List[UserResponse]:
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    blocked_ids = blocks.get(user_id, set())
    result: List[UserResponse] = []
    for bid in blocked_ids:
        user = users_db.get(bid)
        if user is not None:
            result.append(_user_to_response(user))
    return result
