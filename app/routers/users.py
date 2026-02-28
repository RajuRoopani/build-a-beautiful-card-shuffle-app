"""Users router — implements user registration and profile management.

Endpoints:
  POST /users             — Register a new user (username, email, password, display_name).
                            Returns 201 + UserResponse on success.
                            Returns 400 if username is already taken.
  GET  /users/{user_id}  — Return full UserProfileResponse with computed social counts.
                            Returns 404 if user not found.
  PUT  /users/{user_id}  — Update bio and/or display_name.
                            Returns updated UserResponse. Returns 404 if not found.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.models import (
    UserCreate,
    UserProfileResponse,
    UserResponse,
    UserUpdate,
    followers,
    follows,
    hash_password,
    posts_db,
    users_db,
)

router = APIRouter(tags=["Users"])


@router.post("/users", response_model=UserResponse, status_code=201)
def register_user(body: UserCreate) -> UserResponse:
    """Register a new user account.

    Hashes the provided password before storage. Returns 400 if the username
    is already taken.

    Args:
        body: Registration payload containing username, email, password, display_name.

    Returns:
        UserResponse with the newly created user's public profile.

    Raises:
        HTTPException 400: If the username already exists.
    """
    # Reject duplicate usernames (case-sensitive)
    for existing in users_db.values():
        if existing["username"] == body.username:
            raise HTTPException(status_code=400, detail="Username already exists")

    user_id = str(uuid.uuid4())
    user_dict: dict = {
        "id": user_id,
        "username": body.username,
        "email": body.email,
        "password_hash": hash_password(body.password),
        "display_name": body.display_name,
        "bio": None,
        "created_at": datetime.utcnow().isoformat(),
    }
    users_db[user_id] = user_dict
    return UserResponse(
        id=user_id,
        username=user_dict["username"],
        email=user_dict["email"],
        display_name=user_dict["display_name"],
        bio=user_dict["bio"],
    )


@router.get("/users/{user_id}", response_model=UserProfileResponse)
def get_user(user_id: str) -> UserProfileResponse:
    """Retrieve a user's public profile with computed social statistics.

    Follower count, following count, and post count are computed dynamically
    from the in-memory data stores so they always reflect the current state.

    Args:
        user_id: The UUID of the target user.

    Returns:
        UserProfileResponse with social counts populated.

    Raises:
        HTTPException 404: If the user does not exist.
    """
    user = users_db.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # follows is Dict[str, Set[str]]: user_id -> set of IDs they follow
    # followers is Dict[str, Set[str]]: user_id -> set of IDs who follow them
    follower_count = len(followers.get(user_id, set()))
    following_count = len(follows.get(user_id, set()))
    post_count = sum(1 for p in posts_db.values() if p["user_id"] == user_id)

    return UserProfileResponse(
        id=user["id"],
        username=user["username"],
        display_name=user["display_name"],
        bio=user.get("bio"),
        follower_count=follower_count,
        following_count=following_count,
        post_count=post_count,
    )


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: str, body: UserUpdate) -> UserResponse:
    """Update a user's bio and/or display_name.

    Only fields explicitly provided in the request body are updated; omitted
    fields retain their current values.

    Args:
        user_id: The UUID of the user to update.
        body: Update payload. Both fields are optional.

    Returns:
        UserResponse reflecting the updated profile.

    Raises:
        HTTPException 404: If the user does not exist.
    """
    user = users_db.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if body.bio is not None:
        user["bio"] = body.bio
    if body.display_name is not None:
        user["display_name"] = body.display_name

    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        display_name=user["display_name"],
        bio=user.get("bio"),
    )
