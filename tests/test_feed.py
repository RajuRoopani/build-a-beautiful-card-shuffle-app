"""Test suite for Feed router - GET /users/{user_id}/feed."""

import time
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import reset_storage


@pytest.fixture
def client():
    reset_storage()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def users(client):
    def make(username):
        r = client.post("/users", json={"username": username, "email": f"{username}@example.com", "password": "pass123", "display_name": username.title()})
        assert r.status_code == 201
        return r.json()["id"]
    return {"user1": make("user1"), "user2": make("user2"), "user3": make("user3")}


def make_post(client, user_id, caption="Test post"):
    r = client.post("/posts", json={"user_id": user_id, "media_url": "https://example.com/img.jpg", "media_type": "image", "caption": caption})
    assert r.status_code == 201
    return r.json()


def follow(client, follower_id, target_id):
    client.post(f"/users/{target_id}/follow", json={"follower_id": follower_id})


class TestFeed:

    def test_feed_empty_for_user_following_nobody(self, client, users):
        response = client.get(f"/users/{users['user1']}/feed")
        assert response.status_code == 200
        assert response.json() == []

    def test_feed_includes_posts_from_followed_user(self, client, users):
        user1_id, user2_id = users["user1"], users["user2"]
        make_post(client, user2_id, caption="User 2 post")
        follow(client, user1_id, user2_id)
        response = client.get(f"/users/{user1_id}/feed")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == user2_id
        assert data[0]["caption"] == "User 2 post"

    def test_feed_ordered_newest_first(self, client, users):
        user1_id, user2_id = users["user1"], users["user2"]
        follow(client, user1_id, user2_id)
        post1 = make_post(client, user2_id, caption="Post 1")
        time.sleep(0.01)
        post2 = make_post(client, user2_id, caption="Post 2")
        response = client.get(f"/users/{user1_id}/feed")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert data[0]["id"] == post2["id"]
        assert data[1]["id"] == post1["id"]

    def test_feed_excludes_own_posts(self, client, users):
        user1_id, user2_id = users["user1"], users["user2"]
        make_post(client, user1_id, caption="Own post")
        follow(client, user1_id, user2_id)
        make_post(client, user2_id, caption="User 2 post")
        response = client.get(f"/users/{user1_id}/feed")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == user2_id

    def test_feed_nonexistent_user_returns_404(self, client):
        response = client.get("/users/nonexistent-user-id/feed")
        assert response.status_code == 404

    def test_feed_excludes_blocked_user_posts(self, client, users):
        user1_id, user2_id, user3_id = users["user1"], users["user2"], users["user3"]
        follow(client, user1_id, user2_id)
        follow(client, user1_id, user3_id)
        make_post(client, user2_id, caption="User 2 post")
        make_post(client, user3_id, caption="User 3 post")
        # User1 blocks User2
        client.post(f"/users/{user1_id}/block", json={"blocked_user_id": user2_id})
        response = client.get(f"/users/{user1_id}/feed")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == user3_id

    def test_feed_multiple_followed_users(self, client, users):
        user1_id, user2_id, user3_id = users["user1"], users["user2"], users["user3"]
        follow(client, user1_id, user2_id)
        follow(client, user1_id, user3_id)
        make_post(client, user2_id, caption="User 2 post")
        make_post(client, user3_id, caption="User 3 post")
        response = client.get(f"/users/{user1_id}/feed")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        user_ids = {p["user_id"] for p in data}
        assert user2_id in user_ids
        assert user3_id in user_ids
