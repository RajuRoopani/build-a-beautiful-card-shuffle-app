"""Edge case and validation tests for Twitter Clone API."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import reset_storage

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_teardown():
    reset_storage()
    yield
    reset_storage()


def make_user(username, email=None):
    r = client.post("/users", json={
        "username": username,
        "email": email or f"{username}@example.com",
        "password": "pass123",
        "display_name": username.title(),
    })
    assert r.status_code == 201
    return r.json()


def make_post(user_id, caption="Test post"):
    r = client.post("/posts", json={
        "user_id": user_id,
        "media_url": "https://example.com/img.jpg",
        "media_type": "image",
        "caption": caption,
    })
    assert r.status_code == 201
    return r.json()


def test_register_user_minimal_fields():
    """Register user with required fields returns correct structure."""
    response = client.post("/users", json={
        "username": "minimal_user",
        "email": "user@example.com",
        "password": "pass123",
        "display_name": "Minimal User",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "minimal_user"
    assert data["email"] == "user@example.com"
    assert data["display_name"] == "Minimal User"
    assert data["bio"] is None


def test_create_post_with_long_caption():
    """Create a post with a long caption should succeed."""
    user = make_user("user_long")
    long_caption = "a" * 500
    post = make_post(user["id"], caption=long_caption)
    assert post["caption"] == long_caption


def test_create_post_missing_required_fields():
    """Create a post without required fields should return 422."""
    response = client.post("/posts", json={"caption": "no user"})
    assert response.status_code == 422


def test_like_own_post():
    """A user should be able to like their own post."""
    user = make_user("user_like_own")
    post = make_post(user["id"], caption="My own post")
    like_resp = client.post(f"/posts/{post['id']}/like", json={"user_id": user["id"]})
    assert like_resp.status_code == 200
    data = like_resp.json()
    assert data["post_id"] == post["id"]
    assert data["like_count"] == 1


def test_share_own_post():
    """A user should be able to share their own post."""
    user = make_user("user_share_own")
    post = make_post(user["id"], caption="Original post")
    share_resp = client.post(f"/posts/{post['id']}/share", json={"user_id": user["id"]})
    assert share_resp.status_code == 201
    data = share_resp.json()
    assert data["original_post_id"] == post["id"]
    assert data["user_id"] == user["id"]


def test_get_user_posts_empty():
    """GET /users/{id}/posts when user has no posts returns empty list."""
    user = make_user("user_no_posts")
    response = client.get(f"/users/{user['id']}/posts")
    assert response.status_code == 200
    assert response.json() == []


def test_get_user_posts_returns_own_posts():
    """GET /users/{id}/posts returns posts by that user."""
    user = make_user("user_with_posts")
    post = make_post(user["id"], caption="My post")
    response = client.get(f"/users/{user['id']}/posts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == post["id"]


def test_get_followers_empty():
    """GET /users/{id}/followers when user has no followers returns empty list."""
    user = make_user("user_no_followers")
    response = client.get(f"/users/{user['id']}/followers")
    assert response.status_code == 200
    assert response.json() == []


def test_get_following_empty():
    """GET /users/{id}/following when user follows nobody returns empty list."""
    user = make_user("user_no_following")
    response = client.get(f"/users/{user['id']}/following")
    assert response.status_code == 200
    assert response.json() == []


def test_root_endpoint():
    """GET / returns a health/info response."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


def test_get_nonexistent_user_returns_404():
    """GET /users/{id} for non-existent user returns 404."""
    response = client.get("/users/does-not-exist")
    assert response.status_code == 404


def test_get_nonexistent_post_returns_404():
    """GET /posts/{id} for non-existent post returns 404."""
    response = client.get("/posts/does-not-exist")
    assert response.status_code == 404


def test_like_nonexistent_post_returns_404():
    """Liking a non-existent post returns 404."""
    user = make_user("user_404_like")
    response = client.post("/posts/nonexistent/like", json={"user_id": user["id"]})
    assert response.status_code == 404


def test_duplicate_username_returns_409_or_400():
    """Registering with a duplicate username should return 409 or 400."""
    make_user("dupe_user")
    response = client.post("/users", json={
        "username": "dupe_user",
        "email": "dupe2@example.com",
        "password": "pass123",
        "display_name": "Dupe",
    })
    assert response.status_code in [400, 409, 422]
