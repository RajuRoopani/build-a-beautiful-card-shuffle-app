"""Tests for the Instagram-like API Block feature."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import (
    users_db, posts_db, follows, followers, likes, shares_db, post_shares, blocks,
)


@pytest.fixture(autouse=True)
def clear_db():
    users_db.clear(); posts_db.clear(); follows.clear(); followers.clear()
    likes.clear(); shares_db.clear(); post_shares.clear(); blocks.clear()
    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def create_user(client, username, email=None, display_name=None):
    if email is None: email = f"{username}@example.com"
    if display_name is None: display_name = username.title()
    resp = client.post("/users", json={"username": username, "email": email, "password": "password123", "display_name": display_name})
    assert resp.status_code == 201
    return resp.json()


def create_post(client, user_id, caption=None):
    resp = client.post("/posts", json={"user_id": user_id, "media_url": "https://example.com/image.jpg", "media_type": "image", "caption": caption or "Test post"})
    assert resp.status_code == 201
    return resp.json()


class TestBlockUser:

    def test_block_user_returns_200_or_201(self, client):
        alice = create_user(client, "alice")
        bob = create_user(client, "bob")
        response = client.post(f"/users/{alice['id']}/block", json={"blocked_user_id": bob["id"]})
        assert response.status_code in [200, 201]

    def test_block_self_returns_400(self, client):
        alice = create_user(client, "alice")
        response = client.post(f"/users/{alice['id']}/block", json={"blocked_user_id": alice["id"]})
        assert response.status_code == 400

    def test_block_already_blocked_user_returns_400(self, client):
        alice = create_user(client, "alice")
        bob = create_user(client, "bob")
        resp1 = client.post(f"/users/{alice['id']}/block", json={"blocked_user_id": bob["id"]})
        assert resp1.status_code in [200, 201]
        resp2 = client.post(f"/users/{alice['id']}/block", json={"blocked_user_id": bob["id"]})
        assert resp2.status_code == 400

    def test_block_nonexistent_user_returns_404(self, client):
        alice = create_user(client, "alice")
        response = client.post(f"/users/{alice['id']}/block", json={"blocked_user_id": "nonexistent"})
        assert response.status_code == 404

    def test_block_by_nonexistent_user_returns_404(self, client):
        bob = create_user(client, "bob")
        response = client.post(f"/users/nonexistent/block", json={"blocked_user_id": bob["id"]})
        assert response.status_code == 404

    def test_block_removes_follow_relationship(self, client):
        alice = create_user(client, "alice")
        bob = create_user(client, "bob")
        client.post(f"/users/{bob['id']}/follow", json={"follower_id": alice["id"]})
        assert bob["id"] in follows.get(alice["id"], set())
        # Alice blocks Bob
        client.post(f"/users/{alice['id']}/block", json={"blocked_user_id": bob["id"]})
        assert bob["id"] not in follows.get(alice["id"], set())


class TestUnblockUser:

    def test_unblock_returns_200_or_204(self, client):
        alice = create_user(client, "alice")
        bob = create_user(client, "bob")
        client.post(f"/users/{alice['id']}/block", json={"blocked_user_id": bob["id"]})
        response = client.request("DELETE", f"/users/{alice['id']}/block", json={"blocked_user_id": bob["id"]})
        assert response.status_code in [200, 204]

    def test_unblock_removes_block(self, client):
        alice = create_user(client, "alice")
        bob = create_user(client, "bob")
        client.post(f"/users/{alice['id']}/block", json={"blocked_user_id": bob["id"]})
        assert bob["id"] in blocks.get(alice["id"], set())
        client.request("DELETE", f"/users/{alice['id']}/block", json={"blocked_user_id": bob["id"]})
        assert bob["id"] not in blocks.get(alice["id"], set())

    def test_unblock_when_not_blocked_returns_400(self, client):
        alice = create_user(client, "alice")
        bob = create_user(client, "bob")
        response = client.request("DELETE", f"/users/{alice['id']}/block", json={"blocked_user_id": bob["id"]})
        assert response.status_code == 400


class TestGetBlocked:

    def test_get_blocked_returns_correct_users(self, client):
        alice = create_user(client, "alice")
        bob = create_user(client, "bob")
        charlie = create_user(client, "charlie")
        client.post(f"/users/{alice['id']}/block", json={"blocked_user_id": bob["id"]})
        client.post(f"/users/{alice['id']}/block", json={"blocked_user_id": charlie["id"]})
        response = client.get(f"/users/{alice['id']}/blocked")
        assert response.status_code == 200
        blocked_ids = [b["id"] for b in response.json()]
        assert bob["id"] in blocked_ids
        assert charlie["id"] in blocked_ids

    def test_get_blocked_empty_list(self, client):
        alice = create_user(client, "alice")
        response = client.get(f"/users/{alice['id']}/blocked")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_blocked_nonexistent_user_returns_404(self, client):
        response = client.get("/users/nonexistent/blocked")
        assert response.status_code == 404


class TestBlockEnforcement:

    def test_cannot_like_post_when_blocked_by_owner(self, client):
        alice = create_user(client, "alice")
        post = create_post(client, alice["id"])
        bob = create_user(client, "bob")
        # Alice blocks Bob
        client.post(f"/users/{alice['id']}/block", json={"blocked_user_id": bob["id"]})
        response = client.post(f"/posts/{post['id']}/like", json={"user_id": bob["id"]})
        assert response.status_code == 403

    def test_cannot_share_post_when_blocked_by_owner(self, client):
        alice = create_user(client, "alice")
        post = create_post(client, alice["id"])
        bob = create_user(client, "bob")
        # Alice blocks Bob
        client.post(f"/users/{alice['id']}/block", json={"blocked_user_id": bob["id"]})
        response = client.post(f"/posts/{post['id']}/share", json={"user_id": bob["id"]})
        assert response.status_code == 403
