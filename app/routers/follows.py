"""
app/routers/follows.py
──────────────────────
Follow / unfollow and social-graph listing endpoints.

Endpoints:
  POST   /users/{user_id}/follow    — Follow user_id as body.follower_id.
  DELETE /users/{user_id}/follow    — Unfollow user_id as body.follower_id.
  GET    /users/{user_id}/followers — List all users who follow user_id.
  GET    /users/{user_id}/following — List all users that user_id follows.
"""

from typing import List

from fastapi import APIRouter, HTTPException

from app.models import (
    FollowRequest,
    UserResponse,
    blocks,
    followers,
    follows,
    users_db,
)

router = APIRouter(prefix="/users", tags=["follows"])


def _user_to_response(user: dict) -> UserResponse:
    """Convert an internal user dict to a UserResponse."""
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        display_name=user["display_name"],
        bio=user.get("bio"),
    )


@router.post("/{user_id}/follow", status_code=200)
def follow_user(user_id: str, body: FollowRequest) -> dict:
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    if body.follower_id not in users_db:
        raise HTTPException(status_code=404, detail="Follower user not found")

    if body.follower_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    # Block check — 403 when blocked
    if user_id in blocks.get(body.follower_id, set()):
        raise HTTPException(status_code=403, detail="Cannot follow a user you have blocked")
    if body.follower_id in blocks.get(user_id, set()):
        raise HTTPException(status_code=403, detail="Cannot follow a user who has blocked you")

    # Prevent double-follow
    if user_id in follows.get(body.follower_id, set()):
        raise HTTPException(status_code=400, detail="Already following this user")

    follows.setdefault(body.follower_id, set()).add(user_id)
    followers.setdefault(user_id, set()).add(body.follower_id)

    return {"detail": f"User {body.follower_id} is now following {user_id}"}


@router.delete("/{user_id}/follow", status_code=200)
def unfollow_user(user_id: str, body: FollowRequest) -> dict:
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    if body.follower_id not in users_db:
        raise HTTPException(status_code=404, detail="Follower user not found")

    # Return 400 if not following
    if user_id not in follows.get(body.follower_id, set()):
        raise HTTPException(status_code=400, detail="Not following this user")

    follows.setdefault(body.follower_id, set()).discard(user_id)
    followers.setdefault(user_id, set()).discard(body.follower_id)

    return {"detail": f"User {body.follower_id} has unfollowed {user_id}"}


@router.get("/{user_id}/followers", response_model=List[UserResponse])
def get_followers(user_id: str) -> List[UserResponse]:
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    follower_ids = followers.get(user_id, set())
    result: List[UserResponse] = []
    for fid in follower_ids:
        user = users_db.get(fid)
        if user is not None:
            result.append(_user_to_response(user))
    return result


@router.get("/{user_id}/following", response_model=List[UserResponse])
def get_following(user_id: str) -> List[UserResponse]:
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    following_ids = follows.get(user_id, set())
    result: List[UserResponse] = []
    for fid in following_ids:
        user = users_db.get(fid)
        if user is not None:
            result.append(_user_to_response(user))
    return result
