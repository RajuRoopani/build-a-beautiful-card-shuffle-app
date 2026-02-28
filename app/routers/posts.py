"""Posts router — implements CRUD for Instagram-style posts.

Endpoints:
  POST   /posts                    — Create a post (requires media_url + media_type).
                                     Returns 201. 400 for invalid input, 404 if user missing.
  GET    /posts/{post_id}          — Retrieve a single post. 404 if not found.
  DELETE /posts/{post_id}          — Delete a post. 404 if not found.
  GET    /users/{user_id}/posts    — List all posts by a user, newest first.
                                     404 if user not found.
"""

import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException

from app.models import (
    ALLOWED_MEDIA_TYPES,
    PostCreate,
    PostResponse,
    posts_db,
    users_db,
)

router = APIRouter(tags=["Posts"])


def _post_to_response(post: dict) -> PostResponse:
    """Convert an internal post dict to a PostResponse schema.

    Args:
        post: Raw post dictionary from posts_db.

    Returns:
        Validated PostResponse instance.
    """
    return PostResponse(
        id=post["id"],
        user_id=post["user_id"],
        media_url=post["media_url"],
        media_type=post["media_type"],
        caption=post.get("caption"),
        created_at=post["created_at"],
        like_count=post.get("like_count", 0),
        share_count=post.get("share_count", 0),
    )


@router.post("/posts", response_model=PostResponse, status_code=201)
def create_post(body: PostCreate) -> PostResponse:
    """Create a new Instagram-style post.

    Requires a valid media_url and a media_type of either 'image' or 'video'.
    The optional caption is capped at 2200 characters (enforced by the schema).

    Args:
        body: Post creation payload.

    Returns:
        PostResponse for the newly created post.

    Raises:
        HTTPException 400: If media_url is empty or media_type is not 'image'/'video'.
        HTTPException 404: If the specified user_id does not exist.
    """
    # Validate user exists
    if body.user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate media_url is non-empty (Pydantic min_length=1 covers this, but be explicit)
    if not body.media_url or not body.media_url.strip():
        raise HTTPException(status_code=400, detail="media_url is required")

    # Validate media_type
    if body.media_type not in ALLOWED_MEDIA_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"media_type must be one of: {sorted(ALLOWED_MEDIA_TYPES)}",
        )

    post_id = str(uuid.uuid4())
    post_dict: dict = {
        "id": post_id,
        "user_id": body.user_id,
        "media_url": body.media_url,
        "media_type": body.media_type,
        "caption": body.caption,
        "created_at": datetime.utcnow().isoformat(),
        "like_count": 0,
        "share_count": 0,
    }
    posts_db[post_id] = post_dict
    return _post_to_response(post_dict)


@router.get("/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: str) -> PostResponse:
    """Retrieve a single post by its ID.

    Args:
        post_id: UUID of the post.

    Returns:
        PostResponse with current like_count and share_count.

    Raises:
        HTTPException 404: If the post does not exist.
    """
    post = posts_db.get(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return _post_to_response(post)


@router.delete("/posts/{post_id}", status_code=200)
def delete_post(post_id: str) -> dict:
    """Delete a post by its ID.

    Args:
        post_id: UUID of the post to delete.

    Returns:
        Confirmation message dict.

    Raises:
        HTTPException 404: If the post does not exist.
    """
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    del posts_db[post_id]
    return {"detail": "Post deleted"}


@router.get("/users/{user_id}/posts", response_model=List[PostResponse])
def get_user_posts(user_id: str) -> List[PostResponse]:
    """Return all posts authored by a specific user, newest first.

    Args:
        user_id: UUID of the user whose posts to retrieve.

    Returns:
        List of PostResponse objects sorted by created_at descending.

    Raises:
        HTTPException 404: If the user does not exist.
    """
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    user_posts = [p for p in posts_db.values() if p["user_id"] == user_id]
    # Sort newest first — created_at is an ISO-8601 string; lexicographic sort is correct
    user_posts.sort(key=lambda p: p["created_at"], reverse=True)
    return [_post_to_response(p) for p in user_posts]
