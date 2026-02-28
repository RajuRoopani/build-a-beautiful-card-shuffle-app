"""Tests for the Instagram-like API Follow feature.

Tests follow/unfollow functionality, follower/following lists, and block enforcement.

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


class TestFollowUser:
    """Tests for following a user."""

    def test_follow_user_returns_200_or_201(self, client: TestClient):
        """Following a user should return 200 or 201."""
        alice = create_user(client, "alice")
        bob = create_user(client, "bob")
        
        response = client.post(
            f"/users/{bob['id']}/follow",
            json={"follower_id": alice["id"]},
        )
        assert response.status_code in [200, 201]

    def test_follow_user_adds_relationship(self, client: TestClient):
        """Following a user should create a follow relationship."""
        alice = create_user(client, "alice")
        bob = create_user(client, "bob")
        
        response = client.post(
            f"/users/{bob['id']}/follow",
            json={"follower_id": alice["id"]},
        )
        assert response.status_code in [200, 201]
        
        # Verify relationship exists
        assert bob["id"] in follows.get(alice["id"], set())

    def test_follow_self_returns_400(self, client: TestClient):
        """Attempting to follow oneself should return 400."""
        alice = create_user(client, "alice")
        
        response = client.post(
            f"/users/{alice['id']}/follow",
            json={"follower_id": alice["id"]},
        )
        assert response.status_code == 400

    def test_follow_already_followed_user_returns_400(self, client: TestClient):
        """Following a user twice should return 400."""
        alice = create_user(client, "alice")
        bob = create_user(client, "bob")
        
        # First follow
        response1 = client.post(
            f"/users/{bob['id']}/follow",
            json={"follower_id": alice["id"]},
        )
        assert response1.status_code in [200, 201]
        
        # Second follow (should fail)
        response2 = client.post(
            f"/users/{bob['id']}/follow",
            json={"follower_id": alice["id"]},
        )
        assert response2.status_code == 400

    def test_follow_nonexistent_user_returns_404(self, client: TestClient):
        """Following a non-existent user should return 404."""
        alice = create_user(client, "alice")
        fake_id = "nonexistent-user-id"
        
        response = client.post(
            f"/users/{fake_id}/follow",
            json={"follower_id": alice["id"]},
        )
        assert response.status_code == 404

    def test_follow_by_nonexistent_follower_returns_404(self, client: TestClient):
        """Following as a non-existent user should return 404."""
        bob = create_user(client, "bob")
        fake_id = "nonexistent-user-id"
        
        response = client.post(
            f"/users/{bob['id']}/follow",
            json={"follower_id": fake_id},
        )
        assert response.status_code == 404

    def test_follow_when_blocked_returns_403(self, client: TestClient):
        """Following a user who has blocked you should return 403."""
        alice = create_user(client, "alice")
        bob = create_user(client, "bob")
        
        # Bob blocks Alice via the API
        client.post(
            f"/users/{bob['id']}/block",
            json={"blocked_user_id": alice["id"]},
        )

        # Alice tries to follow Bob (but Bob has blocked Alice)
        response = client.post(
            f"/users/{bob['id']}/follow",
            json={"follower_id": alice["id"]},
        )
        assert response.status_code == 403


class TestUnfollowUser:
    """Tests for unfollowing a user."""

    def test_unfollow_returns_200_or_204(self, client: TestClient):
        """Unfollowing a user should return 200 or 204."""
        alice = create_user(client, "alice")
        bob = create_user(client, "bob")
        
        # Follow first
        client.post(
            f"/users/{bob['id']}/follow",
            json={"follower_id": alice["id"]},
        )
        
        # Then unfollow
        response = client.request("DELETE", f"/users/{bob['id']}/follow", json={"follower_id": alice["id"]},
        )
        assert response.status_code in [200, 204]

    def test_unfollow_removes_relationship(self, client: TestClient):
        """Unfollowing should remove the follow relationship."""
        alice = create_user(client, "alice")
        bob = create_user(client, "bob")

        # Follow
        client.post(
            f"/users/{bob['id']}/follow",
            json={"follower_id": alice["id"]},
        )
        assert bob["id"] in follows.get(alice["id"], set())

        # Unfollow
        client.request("DELETE", f"/users/{bob['id']}/follow", json={"follower_id": alice["id"]},
        )
        assert bob["id"] not in follows.get(alice["id"], set())

    def test_unfollow_when_not_following_returns_400(self, client: TestClient):
        """Unfollowing a user you're not following should return 400."""
        alice = create_user(client, "alice")
        bob = create_user(client, "bob")
        
        response = client.request("DELETE", f"/users/{bob['id']}/follow", json={"follower_id": alice["id"]},
        )
        assert response.status_code == 400


class TestGetFollowers:
    """Tests for retrieving followers list."""

    def test_get_followers_returns_correct_users(self, client: TestClient):
        """Getting followers should return the correct list of users."""
        alice = create_user(client, "alice")
        bob = create_user(client, "bob")
        charlie = create_user(client, "charlie")
        
        # Alice and Charlie follow Bob
        client.post(
            f"/users/{bob['id']}/follow",
            json={"follower_id": alice["id"]},
        )
        client.post(
            f"/users/{bob['id']}/follow",
            json={"follower_id": charlie["id"]},
        )
        
        response = client.get(f"/users/{bob['id']}/followers")
        assert response.status_code == 200
        followers_list = response.json()
        
        # Should contain Alice and Charlie
        follower_ids = [f["id"] for f in followers_list]
        assert alice["id"] in follower_ids
        assert charlie["id"] in follower_ids

    def test_get_followers_empty_list(self, client: TestClient):
        """Getting followers for a user with no followers should return empty list."""
        alice = create_user(client, "alice")
        
        response = client.get(f"/users/{alice['id']}/followers")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_followers_nonexistent_user_returns_404(self, client: TestClient):
        """Getting followers for non-existent user should return 404."""
        fake_id = "nonexistent-user-id"
        
        response = client.get(f"/users/{fake_id}/followers")
        assert response.status_code == 404


class TestGetFollowing:
    """Tests for retrieving following list."""

    def test_get_following_returns_correct_users(self, client: TestClient):
        """Getting following should return the correct list of users."""
        alice = create_user(client, "alice")
        bob = create_user(client, "bob")
        charlie = create_user(client, "charlie")
        
        # Alice follows Bob and Charlie
        client.post(
            f"/users/{bob['id']}/follow",
            json={"follower_id": alice["id"]},
        )
        client.post(
            f"/users/{charlie['id']}/follow",
            json={"follower_id": alice["id"]},
        )
        
        response = client.get(f"/users/{alice['id']}/following")
        assert response.status_code == 200
        following_list = response.json()
        
        # Should contain Bob and Charlie
        following_ids = [f["id"] for f in following_list]
        assert bob["id"] in following_ids
        assert charlie["id"] in following_ids

    def test_get_following_empty_list(self, client: TestClient):
        """Getting following for a user who follows no one should return empty list."""
        alice = create_user(client, "alice")
        
        response = client.get(f"/users/{alice['id']}/following")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_following_nonexistent_user_returns_404(self, client: TestClient):
        """Getting following for non-existent user should return 404."""
        fake_id = "nonexistent-user-id"
        
        response = client.get(f"/users/{fake_id}/following")
        assert response.status_code == 404
