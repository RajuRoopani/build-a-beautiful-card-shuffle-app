"""
Users router — CRUD for user accounts.
"""
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException, status

from slack_app import storage
from slack_app.models import User, UserCreate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate) -> User:
    """Register a new user."""
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    user_dict = {
        "user_id": user_id,
        "username": payload.username,
        "display_name": payload.display_name,
        "created_at": now,
    }

    storage.users[user_id] = user_dict
    return User(**user_dict)


@router.get("", response_model=List[User])
def list_users() -> List[User]:
    """Return all registered users."""
    return [User(**u) for u in storage.users.values()]


@router.get("/{user_id}", response_model=User)
def get_user(user_id: str) -> User:
    """Return a single user by ID, or 404 if not found."""
    user_dict = storage.users.get(user_id)
    if user_dict is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found.",
        )
    return User(**user_dict)
