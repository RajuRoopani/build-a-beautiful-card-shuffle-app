"""Reposts router — implements repost (retweet) functionality.

⚠️  DEAD CODE — NOT WIRED INTO main.py ⚠️
This router is NOT registered with the FastAPI app and is not part of the
current acceptance criteria. Do NOT import or test it until it is explicitly
added to main.py. The models it references (reposts_db, generate_id, now_utc,
RepostRequest, RepostResponse) do not exist in app/models.py.

AC5:  POST /posts/{post_id}/repost — repost (201, 404, 400 if already reposted)
      GET /posts/{post_id}/reposts  — list reposts for a post
      Reposting creates a new entry in posts_db with original_post_id set.
      Repost count is incremented on the original post.
"""

from fastapi import APIRouter, HTTPException

from app.models import (
    posts_db,
    users_db,
    reposts_db,
    generate_id,
    now_utc,
    RepostRequest,
    RepostResponse,
    PostResponse,
)

router = APIRouter(tags=["Reposts"])


@router.post("/posts/{post_id}/repost", status_code=201)
def repost_post(post_id: str, body: RepostRequest) -> dict:
    """Repost a post. Creates a new post entry referencing the original."""
    # Validate original post exists
    original_post = posts_db.get(post_id)
    if original_post is None:
        raise HTTPException(status_code=404, detail=f"Post '{post_id}' not found")

    # Validate user exists
    user = users_db.get(body.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User '{body.user_id}' not found")

    # Prevent duplicate reposts by same user
    already_reposted = any(
        entry["user_id"] == body.user_id and entry["post_id"] == post_id
        for entry in reposts_db
    )
    if already_reposted:
        raise HTTPException(
            status_code=400, detail="User has already reposted this post"
        )

    # Create the new repost entry in posts_db
    new_post_id = generate_id()
    created_at = now_utc()

    new_post: dict = {
        "id": new_post_id,
        "user_id": body.user_id,
        "content": original_post.get("content", ""),
        "created_at": created_at,
        "like_count": 0,
        "repost_count": 0,
        "media_url": original_post.get("media_url"),
        "original_post_id": post_id,  # marks this as a repost
    }
    posts_db[new_post_id] = new_post

    # Track repost relationship
    reposts_db.append(
        {
            "user_id": body.user_id,
            "post_id": post_id,
            "repost_id": new_post_id,
            "created_at": created_at,
        }
    )

    # Increment repost_count on the original post
    original_post["repost_count"] = original_post.get("repost_count", 0) + 1

    repost_response = RepostResponse(
        id=new_post_id,
        user_id=body.user_id,
        post_id=post_id,
        created_at=created_at,
    )
    return repost_response.model_dump()


@router.get("/posts/{post_id}/reposts")
def get_post_reposts(post_id: str) -> dict:
    """Return the list of reposts for a post."""
    # Validate original post exists
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail=f"Post '{post_id}' not found")

    repost_entries = [
        entry for entry in reposts_db if entry["post_id"] == post_id
    ]

    # Build RepostResponse objects from reposts_db entries
    reposts = [
        RepostResponse(
            id=entry["repost_id"],
            user_id=entry["user_id"],
            post_id=entry["post_id"],
            created_at=entry["created_at"],
        ).model_dump()
        for entry in repost_entries
    ]

    return {
        "post_id": post_id,
        "repost_count": posts_db[post_id].get("repost_count", 0),
        "reposts": reposts,
    }
