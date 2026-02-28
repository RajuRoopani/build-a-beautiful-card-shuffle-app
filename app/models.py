"""
app/models.py
─────────────
Pydantic request/response models and in-memory data stores for the
Instagram-like API.  All persistence lives here so routers stay thin.

Data stores are module-level singletons — they act as the in-memory
database for this prototype.
"""

from __future__ import annotations

import hashlib
from typing import Dict, List, Optional, Set

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ALLOWED_MEDIA_TYPES: frozenset = frozenset({"image", "video"})
"""Valid values for PostCreate.media_type."""


def hash_password(plain: str) -> str:
    """Return a hex-encoded SHA-256 digest of *plain*.

    This is a simple deterministic hash suitable for in-memory demos.
    Production code should use bcrypt / argon2 with a per-user salt.
    """
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# In-memory data stores
# ---------------------------------------------------------------------------

users_db: Dict[str, dict] = {}
"""Keyed by user_id (UUID string).  Each value is a raw user dict."""

posts_db: Dict[str, dict] = {}
"""Keyed by post_id (UUID string).  Each value is a raw post dict."""

follows: Dict[str, Set[str]] = {}
"""user_id → set of user_ids that *user_id* is following."""

followers: Dict[str, Set[str]] = {}
"""user_id → set of user_ids who follow *user_id*."""

likes: Dict[str, Set[str]] = {}
"""post_id → set of user_ids who have liked the post."""

shares_db: Dict[str, dict] = {}
"""share_id → share record dict."""

post_shares: Dict[str, List[str]] = {}
"""post_id → ordered list of share_ids for that post."""

blocks: Dict[str, Set[str]] = {}
"""user_id → set of user_ids that *user_id* has blocked."""


def reset_storage() -> None:
    """Clear all in-memory data stores. Intended for use in tests only."""
    users_db.clear()
    posts_db.clear()
    follows.clear()
    followers.clear()
    likes.clear()
    shares_db.clear()
    post_shares.clear()
    blocks.clear()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    """Payload for creating a new user account."""

    username: str = Field(..., min_length=1, max_length=30)
    email: str = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, description="Plain-text password (hashed server-side)")
    display_name: str = Field(..., min_length=1, max_length=60)


class UserUpdate(BaseModel):
    """Payload for updating an existing user's profile."""

    bio: Optional[str] = Field(None, max_length=150)
    display_name: Optional[str] = Field(None, min_length=1, max_length=60)


class PostCreate(BaseModel):
    """Payload for creating a new post."""

    user_id: str = Field(..., description="UUID of the authoring user")
    caption: Optional[str] = Field(None, max_length=2200)
    media_url: str = Field(..., description="URL of the uploaded media asset")
    media_type: str = Field(
        ...,
        pattern=r"^(image|video)$",
        description="Must be 'image' or 'video'",
    )


class FollowRequest(BaseModel):
    """Payload for following a user."""

    follower_id: str = Field(..., description="UUID of the user who wants to follow")


class LikeRequest(BaseModel):
    """Payload for liking a post."""

    user_id: str = Field(..., description="UUID of the user liking the post")


class ShareRequest(BaseModel):
    """Payload for sharing a post."""

    user_id: str = Field(..., description="UUID of the user sharing the post")


class BlockRequest(BaseModel):
    """Payload for blocking another user."""

    blocked_user_id: str = Field(..., description="UUID of the user to be blocked")


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class UserResponse(BaseModel):
    """Slim user representation returned on create / update."""

    id: str
    username: str
    email: str
    display_name: str
    bio: Optional[str] = None


class UserProfileResponse(BaseModel):
    """Full public profile view including social counts."""

    id: str
    username: str
    display_name: str
    bio: Optional[str] = None
    follower_count: int = 0
    following_count: int = 0
    post_count: int = 0


class PostResponse(BaseModel):
    """Post representation returned to API consumers."""

    id: str
    user_id: str
    caption: Optional[str] = None
    media_url: str
    media_type: str
    created_at: str  # ISO-8601 string
    like_count: int = 0
    share_count: int = 0


class ShareResponse(BaseModel):
    """Share record returned to API consumers."""

    id: str
    user_id: str
    original_post_id: str
    created_at: str  # ISO-8601 string
