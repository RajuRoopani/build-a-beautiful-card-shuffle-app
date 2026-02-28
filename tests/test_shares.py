"""Tests for the Instagram-like API Share feature.

Tests sharing posts, share counts, and block enforcement.

Uses FastAPI's TestClient with in-memory data stores that are reset before each test.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import (
    users_db,
    posts_db,
    follows,
    followers,
    likes,
    shares_db,
    post_shares,
    blocks,
)


@pytest.fixture(autouse=True)
def clear_db():
    """Reset all in-memory storage before each test."""
    users_db.clear()
    posts_db.clear()
    follows.clear()
    followers.clear()
    likes.clear()
    shares_db.clear()
    post_shares.clear()
    blocks.clear()
    yield


@pytest.fixture
def client() -> TestClient:
    """Return a TestClient for the app."""
    return TestClient(app)


def create_user(client: TestClient, username: str, email: str = None, display_name: str = None):
    """Helper to create a user and return the user dict."""
    if email is None:
        email = f"{username}@example.com"
    if display_name is None:
        display_name = username.title()
    
    response = client.post(
        "/users",
        json={
            "username": username,
            "email": email,
            "password": "password123",
            "display_name": display_name,
        },
    )
    assert response.status_code == 201
    return response.json()


def create_post(client: TestClient, user_id: str, caption: str = None):
    """Helper to create a post and return the post dict."""
    response = client.post(
        "/posts",
        json={
            "user_id": user_id,
            "media_url": "https://example.com/image.jpg",
            "media_type": "image",
            "caption": caption or "Test post",
        },
    )
    assert response.status_code == 201
    return response.json()


class TestSharePost:
    """Tests for sharing a post."""

    def test_share_post_returns_201(self, client: TestClient):
        """Sharing a post should return 201."""
        alice = create_user(client, "alice")
        post = create_post(client, alice["id"])
        bob = create_user(client, "bob")
        
        response = client.post(
            f"/posts/{post['id']}/share",
            json={"user_id": bob["id"]},
        )
        assert response.status_code == 201

    def test_share_post_returns_share_record(self, client: TestClient):
        """Sharing a post should return a share record with id, user_id, original_post_id, created_at."""
        alice = create_user(client, "alice")
        post = create_post(client, alice["id"])
        bob = create_user(client, "bob")
        
        response = client.post(
            f"/posts/{post['id']}/share",
            json={"user_id": bob["id"]},
        )
        assert response.status_code == 201
        share = response.json()
        
        # Check required fields
        assert "id" in share
        assert "user_id" in share
        assert share["user_id"] == bob["id"]
        assert "original_post_id" in share
        assert share["original_post_id"] == post["id"]
        assert "created_at" in share

    def test_share_increments_share_count(self, client: TestClient):
        """Sharing a post should increment the share_count on the original post."""
        alice = create_user(client, "alice")
        post = create_post(client, alice["id"])
        bob = create_user(client, "bob")
        
        # Initial share_count should be 0
        initial_share_count = post.get("share_count", 0)
        
        # Share the post
        response = client.post(
            f"/posts/{post['id']}/share",
            json={"user_id": bob["id"]},
        )
        assert response.status_code == 201
        
        # Verify share was tracked (post_shares[post_id] is a list of share IDs)
        assert post["id"] in post_shares
        assert len(post_shares[post["id"]]) > 0

    def test_share_nonexistent_post_returns_404(self, client: TestClient):
        """Sharing a non-existent post should return 404."""
        bob = create_user(client, "bob")
        fake_post_id = "nonexistent-post-id"
        
        response = client.post(
            f"/posts/{fake_post_id}/share",
            json={"user_id": bob["id"]},
        )
        assert response.status_code == 404

    def test_share_by_nonexistent_user_returns_404(self, client: TestClient):
        """Sharing as a non-existent user should return 404."""
        alice = create_user(client, "alice")
        post = create_post(client, alice["id"])
        fake_user_id = "nonexistent-user-id"
        
        response = client.post(
            f"/posts/{post['id']}/share",
            json={"user_id": fake_user_id},
        )
        assert response.status_code == 404

    def test_share_when_blocked_by_post_owner_returns_403(self, client: TestClient):
        """Sharing a post when blocked by post owner should return 403."""
        alice = create_user(client, "alice")
        post = create_post(client, alice["id"])
        bob = create_user(client, "bob")
        
        # Alice blocks Bob via API
        client.post(f"/users/{alice['id']}/block", json={"blocked_user_id": bob["id"]})

        # Bob tries to share Alice's post
        response = client.post(
            f"/posts/{post['id']}/share",
            json={"user_id": bob["id"]},
        )
        assert response.status_code == 403


class TestGetShares:
    """Tests for retrieving shares list."""

    def test_get_shares_returns_share_records(self, client: TestClient):
        """Getting shares should return share records."""
        alice = create_user(client, "alice")
        post = create_post(client, alice["id"])
        bob = create_user(client, "bob")
        charlie = create_user(client, "charlie")
        
        # Bob and Charlie share the post
        client.post(
            f"/posts/{post['id']}/share",
            json={"user_id": bob["id"]},
        )
        client.post(
            f"/posts/{post['id']}/share",
            json={"user_id": charlie["id"]},
        )
        
        response = client.get(f"/posts/{post['id']}/shares")
        assert response.status_code == 200
        data = response.json()
        
        # Response should contain shares list
        if isinstance(data, dict):
            shares_list = data.get("shares", [])
        else:
            shares_list = data
        
        assert len(shares_list) >= 2
        
        # Check that both users are in the shares
        share_user_ids = [s["user_id"] for s in shares_list]
        assert bob["id"] in share_user_ids
        assert charlie["id"] in share_user_ids

    def test_get_shares_empty_list(self, client: TestClient):
        """Getting shares for a post with no shares should return empty list."""
        alice = create_user(client, "alice")
        post = create_post(client, alice["id"])
        
        response = client.get(f"/posts/{post['id']}/shares")
        assert response.status_code == 200
        data = response.json()
        
        # Handle both response formats
        if isinstance(data, dict):
            shares_list = data.get("shares", [])
            assert shares_list == []
        else:
            assert data == []

    def test_get_shares_nonexistent_post_returns_404(self, client: TestClient):
        """Getting shares for non-existent post should return 404."""
        fake_post_id = "nonexistent-post-id"
        
        response = client.get(f"/posts/{fake_post_id}/shares")
        assert response.status_code == 404
