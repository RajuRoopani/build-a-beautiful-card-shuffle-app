"""
app/main.py
───────────
FastAPI application entry-point.

Start the development server with:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI

from app.routers import blocks, feed, follows, likes, posts, shares, users

app = FastAPI(
    title="Instagram-like API",
    description="A social media REST API supporting posts, follows, likes, shares and more.",
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------

app.include_router(users.router)
app.include_router(posts.router)
app.include_router(follows.router)
app.include_router(feed.router)
app.include_router(likes.router)
app.include_router(shares.router)
app.include_router(blocks.router)


@app.get("/", tags=["health"])
def health_check():
    """Simple liveness probe."""
    return {"status": "ok", "service": "instagram-like-api"}
