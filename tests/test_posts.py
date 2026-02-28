"""Test suite for Posts router - create, retrieve, delete, and list posts.

Tests cover Instagram-style post management including:
- Post creation with image/video media
- Media type validation
- Post retrieval and deletion
- Listing posts with proper ordering and filtering
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import reset_storage


@pytest.fixture
def client():
    """Provide a fresh TestClient with reset storage for each test."""
    reset_storage()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def user_id(client: TestClient) -> str:
    """Create and return a test user ID."""
    response = client.post(
        "/users",
        json={
            "username": "test_user",
            "email": "test@example.com",
            "password": "pass123",
            "display_name": "Test User",
        },
    )
    return response.json()["id"]


class TestPostCreation:
    """Tests for POST /posts (create post)."""

    def test_create_post_with_image(self, client: TestClient, user_id: str):
        """Test creating a post with image media returns 201."""
        response = client.post(
            "/posts",
            json={
                "user_id": user_id,
                "media_url": "https://example.com/image.jpg",
                "media_type": "image",
                "caption": "Check out this photo!",
            },
        )
        assert response.status_code == 201
        data = response.json()
        
        assert "id" in data
        assert data["user_id"] == user_id
        assert data["media_url"] == "https://example.com/image.jpg"
        assert data["media_type"] == "image"
        assert data["caption"] == "Check out this photo!"
        assert data["like_count"] == 0
        assert data["share_count"] == 0

    def test_create_post_with_video(self, client: TestClient, user_id: str):
        """Test creating a post with video media returns 201."""
        response = client.post(
            "/posts",
            json={
                "user_id": user_id,
                "media_url": "https://example.com/video.mp4",
                "media_type": "video",
                "caption": "Check out this video!",
            },
        )
        assert response.status_code == 201
        data = response.json()
        
        assert data["media_type"] == "video"
        assert data["media_url"] == "https://example.com/video.mp4"

    def test_create_post_missing_media_url(self, client: TestClient, user_id: str):
        """Test that creating post without media_url returns 400."""
        response = client.post(
            "/posts",
            json={
                "user_id": user_id,
                "media_type": "image",
                "caption": "Missing media URL",
            },
        )
        assert response.status_code == 422  # Validation error for missing required field

    def test_create_post_invalid_media_type(self, client: TestClient, user_id: str):
        """Test that invalid media_type (e.g., 'audio') is rejected."""
        # PostCreate uses a Pydantic pattern validator, so invalid media_type
        # returns 422 Unprocessable Entity (Pydantic rejects it before the router runs).
        response = client.post(
            "/posts",
            json={
                "user_id": user_id,
                "media_url": "https://example.com/audio.mp3",
                "media_type": "audio",
                "caption": "Audio post",
            },
        )
        assert response.status_code == 422

    def test_create_post_for_nonexistent_user(self, client: TestClient):
        """Test creating post for non-existent user returns 404."""
        response = client.post(
            "/posts",
            json={
                "user_id": "nonexistent-user-id",
                "media_url": "https://example.com/image.jpg",
                "media_type": "image",
                "caption": "This will fail",
            },
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_post_caption_optional(self, client: TestClient, user_id: str):
        """Test that caption is optional (post without caption)."""
        response = client.post(
            "/posts",
            json={
                "user_id": user_id,
                "media_url": "https://example.com/image.jpg",
                "media_type": "image",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["caption"] is None


class TestPostRetrieval:
    """Tests for GET /posts and GET /posts/{post_id}."""

    def test_get_post_returns_correct_fields(self, client: TestClient, user_id: str):
        """Test getting a post returns all fields with correct like/share counts."""
        # Create a post
        create_response = client.post(
            "/posts",
            json={
                "user_id": user_id,
                "media_url": "https://example.com/image.jpg",
                "media_type": "image",
                "caption": "Test post",
            },
        )
        post_id = create_response.json()["id"]
        
        # Get the post
        response = client.get(f"/posts/{post_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == post_id
        assert data["user_id"] == user_id
        assert data["media_url"] == "https://example.com/image.jpg"
        assert data["media_type"] == "image"
        assert data["caption"] == "Test post"
        assert data["like_count"] == 0
        assert data["share_count"] == 0
        assert "created_at" in data

    def test_get_nonexistent_post_returns_404(self, client: TestClient):
        """Test that getting a non-existent post returns 404."""
        response = client.get("/posts/nonexistent-post-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_user_posts_newest_first(self, client: TestClient, user_id: str):
        """Test that getting user's posts returns them newest first."""
        import time
        
        # Create first post
        post1_response = client.post(
            "/posts",
            json={
                "user_id": user_id,
                "media_url": "https://example.com/post1.jpg",
                "media_type": "image",
                "caption": "First post",
            },
        )
        post1_id = post1_response.json()["id"]
        
        # Small delay to ensure different timestamps
        time.sleep(0.01)
        
        # Create second post
        post2_response = client.post(
            "/posts",
            json={
                "user_id": user_id,
                "media_url": "https://example.com/post2.jpg",
                "media_type": "image",
                "caption": "Second post",
            },
        )
        post2_id = post2_response.json()["id"]
        
        # Get user's posts
        response = client.get(f"/users/{user_id}/posts")
        assert response.status_code == 200
        data = response.json()
        
        # Should have 2 posts
        assert len(data) >= 2
        # Second post should be first in list (newest first)
        assert data[0]["id"] == post2_id
        assert data[1]["id"] == post1_id

    def test_get_posts_for_nonexistent_user(self, client: TestClient):
        """Test that getting posts for non-existent user returns 404."""
        response = client.get("/users/nonexistent-user-id/posts")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestPostDeletion:
    """Tests for DELETE /posts/{post_id}."""

    def test_delete_post_success(self, client: TestClient, user_id: str):
        """Test successful post deletion returns 200."""
        # Create a post
        create_response = client.post(
            "/posts",
            json={
                "user_id": user_id,
                "media_url": "https://example.com/image.jpg",
                "media_type": "image",
                "caption": "To be deleted",
            },
        )
        post_id = create_response.json()["id"]
        
        # Delete the post
        response = client.delete(f"/posts/{post_id}")
        assert response.status_code == 200
        
        # Verify post is gone
        get_response = client.get(f"/posts/{post_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_post_returns_404(self, client: TestClient):
        """Test that deleting a non-existent post returns 404."""
        response = client.delete("/posts/nonexistent-post-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
