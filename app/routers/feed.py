"""Feed router — returns a personalised timeline for a user.

Endpoints:
  GET /users/{user_id}/feed — Posts from users that user_id follows, newest first.
                               Excludes posts from any user that user_id has blocked.
                               Returns 404 if user_id not found.
                               Returns an empty list if the user follows nobody.
"""

from typing import List

from fastapi import APIRouter, HTTPException

from app.models import (
    PostResponse,
    blocks,
    follows,
    posts_db,
    users_db,
)

router = APIRouter(tags=["Feed"])


@router.get("/users/{user_id}/feed", response_model=List[PostResponse])
def get_feed(user_id: str) -> List[PostResponse]:
    """Return the personalised timeline feed for a user.

    The feed contains posts from every user that *user_id* follows, sorted
    newest-first by created_at.  Posts authored by any user that *user_id*
    has blocked are silently excluded.

    Args:
        user_id: UUID of the user requesting their feed.

    Returns:
        List of PostResponse objects sorted by created_at descending.
        Returns an empty list when the user follows nobody.

    Raises:
        HTTPException 404: If user_id does not exist.
    """
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    # follows is Dict[str, Set[str]]: user_id -> set of following_ids
    following_ids: set[str] = follows.get(user_id, set())

    if not following_ids:
        return []

    # blocks is Dict[str, Set[str]]: user_id -> set of blocked_ids
    blocked_ids: set[str] = blocks.get(user_id, set())

    # Gather eligible posts: authored by a followed user AND not from a blocked user
    feed_posts = [
        post
        for post in posts_db.values()
        if post["user_id"] in following_ids and post["user_id"] not in blocked_ids
    ]

    # Sort newest first — ISO-8601 strings are lexicographically sortable
    feed_posts.sort(key=lambda p: p["created_at"], reverse=True)

    return [
        PostResponse(
            id=post["id"],
            user_id=post["user_id"],
            media_url=post["media_url"],
            media_type=post["media_type"],
            caption=post.get("caption"),
            created_at=post["created_at"],
            like_count=post.get("like_count", 0),
            share_count=post.get("share_count", 0),
        )
        for post in feed_posts
    ]
