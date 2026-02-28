"""Tests for the Instagram-like API Like feature.

Tests liking/unliking posts, like counts, and block enforcement.

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


class TestLikePost:
    """Tests for liking a post."""

    def test_like_post_returns_200_or_201(self, client: TestClient):
        """Liking a post should return 200 or 201."""
        alice = create_user(client, "alice")
        post = create_post(client, alice["id"])
        bob = create_user(client, "bob")
        
        response = client.post(
            f"/posts/{post['id']}/like",
            json={"user_id": bob["id"]},
        )
        assert response.status_code in [200, 201]

    def test_like_post_increments_count(self, client: TestClient):
        """Liking a post should increment its like count."""
        alice = create_user(client, "alice")
        post = create_post(client, alice["id"])
        bob = create_user(client, "bob")
        
        # Like the post
        response = client.post(
            f"/posts/{post['id']}/like",
            json={"user_id": bob["id"]},
        )
        assert response.status_code in [200, 201]
        
        # Verify like was added
        assert bob["id"] in likes.get(post["id"], set())

    def test_like_already_liked_post_returns_400(self, client: TestClient):
        """Liking a post twice should return 400."""
        alice = create_user(client, "alice")
        post = create_post(client, alice["id"])
        bob = create_user(client, "bob")
        
        # Like the post
        response1 = client.post(
            f"/posts/{post['id']}/like",
            json={"user_id": bob["id"]},
        )
        assert response1.status_code in [200, 201]
        
        # Like again (should fail)
        response2 = client.post(
            f"/posts/{post['id']}/like",
            json={"user_id": bob["id"]},
        )
        assert response2.status_code == 400

    def test_like_nonexistent_post_returns_404(self, client: TestClient):
        """Liking a non-existent post should return 404."""
        bob = create_user(client, "bob")
        fake_post_id = "nonexistent-post-id"
        
        response = client.post(
            f"/posts/{fake_post_id}/like",
            json={"user_id": bob["id"]},
        )
        assert response.status_code == 404

    def test_like_by_nonexistent_user_returns_404(self, client: TestClient):
        """Liking as a non-existent user should return 404."""
        alice = create_user(client, "alice")
        post = create_post(client, alice["id"])
        fake_user_id = "nonexistent-user-id"
        
        response = client.post(
            f"/posts/{post['id']}/like",
            json={"user_id": fake_user_id},
        )
        assert response.status_code == 404

    def test_like_when_blocked_by_post_owner_returns_403(self, client: TestClient):
        """Liking a post when blocked by post owner should return 403."""
        alice = create_user(client, "alice")
        post = create_post(client, alice["id"])
        bob = create_user(client, "bob")
        
        # Alice blocks Bob via API
        client.post(f"/users/{alice['id']}/block", json={"blocked_user_id": bob["id"]})

        # Bob tries to like Alice's post
        response = client.post(
            f"/posts/{post['id']}/like",
            json={"user_id": bob["id"]},
        )
        assert response.status_code == 403


class TestUnlikePost:
    """Tests for unliking a post."""

    def test_unlike_returns_200_or_204(self, client: TestClient):
        """Unliking a post should return 200 or 204."""
        alice = create_user(client, "alice")
        post = create_post(client, alice["id"])
        bob = create_user(client, "bob")
        
        # Like first
        client.post(
            f"/posts/{post['id']}/like",
            json={"user_id": bob["id"]},
        )
        
        # Then unlike
        response = client.request("DELETE", f"/posts/{post['id']}/like", json={"user_id": bob["id"]},
        )
        assert response.status_code in [200, 204]

    def test_unlike_removes_like(self, client: TestClient):
        """Unliking a post should remove the like."""
        alice = create_user(client, "alice")
        post = create_post(client, alice["id"])
        bob = create_user(client, "bob")
        
        # Like
        client.post(
            f"/posts/{post['id']}/like",
            json={"user_id": bob["id"]},
        )
        assert bob["id"] in likes.get(post["id"], set())

        # Unlike
        client.request("DELETE", f"/posts/{post['id']}/like", json={"user_id": bob["id"]},
        )
        assert bob["id"] not in likes.get(post["id"], set())

    def test_unlike_when_not_liked_returns_400(self, client: TestClient):
        """Unliking a post you haven't liked should return 400."""
        alice = create_user(client, "alice")
        post = create_post(client, alice["id"])
        bob = create_user(client, "bob")
        
        response = client.request("DELETE", f"/posts/{post['id']}/like", json={"user_id": bob["id"]},
        )
        assert response.status_code == 400


class TestGetLikes:
    """Tests for retrieving likes list."""

    def test_get_likes_returns_correct_user_ids(self, client: TestClient):
        """Getting likes should return the correct list of user IDs."""
        alice = create_user(client, "alice")
        post = create_post(client, alice["id"])
        bob = create_user(client, "bob")
        charlie = create_user(client, "charlie")
        
        # Bob and Charlie like the post
        client.post(
            f"/posts/{post['id']}/like",
            json={"user_id": bob["id"]},
        )
        client.post(
            f"/posts/{post['id']}/like",
            json={"user_id": charlie["id"]},
        )
        
        response = client.get(f"/posts/{post['id']}/likes")
        assert response.status_code == 200
        data = response.json()
        
        # Should contain Bob and Charlie's IDs
        # Response might be {"user_ids": [...], "like_count": ...} or just a list
        if isinstance(data, dict):
            user_ids = data.get("user_ids", [])
        else:
            user_ids = data
        
        assert bob["id"] in user_ids
        assert charlie["id"] in user_ids

    def test_get_likes_empty_list(self, client: TestClient):
        """Getting likes for a post with no likes should return empty list."""
        alice = create_user(client, "alice")
        post = create_post(client, alice["id"])
        
        response = client.get(f"/posts/{post['id']}/likes")
        assert response.status_code == 200
        data = response.json()
        
        # Handle both response formats
        if isinstance(data, dict):
            user_ids = data.get("user_ids", [])
            assert user_ids == []
        else:
            assert data == []

    def test_get_likes_nonexistent_post_returns_404(self, client: TestClient):
        """Getting likes for non-existent post should return 404."""
        fake_post_id = "nonexistent-post-id"
        
        response = client.get(f"/posts/{fake_post_id}/likes")
        assert response.status_code == 404
