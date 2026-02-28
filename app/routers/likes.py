"""
app/routers/likes.py
────────────────────
Like / unlike endpoints and like-count retrieval.

Endpoints:
  POST   /posts/{post_id}/like  — Like a post.
  DELETE /posts/{post_id}/like  — Unlike a post.
  GET    /posts/{post_id}/likes — Get like count and list of liking user IDs.
"""

from typing import Dict, List, Union

from fastapi import APIRouter, HTTPException

from app.models import (
    LikeRequest,
    blocks,
    likes,
    posts_db,
    users_db,
)

router = APIRouter(prefix="/posts", tags=["likes"])


@router.post("/{post_id}/like", status_code=200)
def like_post(post_id: str, body: LikeRequest) -> Dict[str, Union[str, int]]:
    post = posts_db.get(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if body.user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    # Block enforcement: 403 if post owner has blocked this user
    post_owner = post["user_id"]
    if body.user_id in blocks.get(post_owner, set()):
        raise HTTPException(status_code=403, detail="Cannot like post — you are blocked by the post owner")

    # Prevent double-like
    if body.user_id in likes.get(post_id, set()):
        raise HTTPException(status_code=400, detail="Already liked this post")

    likes.setdefault(post_id, set()).add(body.user_id)
    post["like_count"] = len(likes[post_id])

    return {"post_id": post_id, "like_count": post["like_count"]}


@router.delete("/{post_id}/like", status_code=200)
def unlike_post(post_id: str, body: LikeRequest) -> Dict[str, Union[str, int]]:
    post = posts_db.get(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    # Return 400 if not liked
    if body.user_id not in likes.get(post_id, set()):
        raise HTTPException(status_code=400, detail="Not liked this post")

    likes.setdefault(post_id, set()).discard(body.user_id)
    post["like_count"] = len(likes[post_id])

    return {"post_id": post_id, "like_count": post["like_count"]}


@router.get("/{post_id}/likes", status_code=200)
def get_likes(post_id: str) -> Dict[str, Union[str, int, List[str]]]:
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")

    user_ids: List[str] = list(likes.get(post_id, set()))
    return {
        "post_id": post_id,
        "like_count": len(user_ids),
        "user_ids": user_ids,
    }
