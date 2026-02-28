"""
app/routers/shares.py
─────────────────────
Post sharing endpoints.

Endpoints:
  POST /posts/{post_id}/share  — Share a post; returns 201 with ShareResponse.
  GET  /posts/{post_id}/shares — List all shares for a post.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Union

from fastapi import APIRouter, HTTPException

from app.models import (
    ShareRequest,
    ShareResponse,
    blocks,
    post_shares,
    posts_db,
    shares_db,
    users_db,
)

router = APIRouter(prefix="/posts", tags=["shares"])


def _share_to_response(share: dict) -> ShareResponse:
    return ShareResponse(
        id=share["id"],
        user_id=share["user_id"],
        original_post_id=share["original_post_id"],
        created_at=share["created_at"],
    )


@router.post("/{post_id}/share", response_model=ShareResponse, status_code=201)
def share_post(post_id: str, body: ShareRequest) -> ShareResponse:
    post = posts_db.get(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if body.user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    # Block enforcement: 403 if post owner has blocked this user
    post_owner = post["user_id"]
    if body.user_id in blocks.get(post_owner, set()):
        raise HTTPException(status_code=403, detail="Cannot share post — you are blocked by the post owner")

    share_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()

    share_dict: dict = {
        "id": share_id,
        "user_id": body.user_id,
        "original_post_id": post_id,
        "created_at": created_at,
    }

    shares_db[share_id] = share_dict
    post_shares.setdefault(post_id, []).append(share_id)
    post["share_count"] = len(post_shares[post_id])

    return _share_to_response(share_dict)


@router.get("/{post_id}/shares", status_code=200)
def get_shares(post_id: str) -> Dict[str, Union[str, int, List[dict]]]:
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")

    share_ids = post_shares.get(post_id, [])
    share_list = [
        _share_to_response(shares_db[sid]).model_dump()
        for sid in share_ids
        if sid in shares_db
    ]

    return {
        "post_id": post_id,
        "share_count": len(share_list),
        "shares": share_list,
    }
