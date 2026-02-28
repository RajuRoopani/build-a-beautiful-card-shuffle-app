"""Test suite for Users router - registration, profile retrieval, and updates.

Tests cover user account management including:
- User registration with validation
- User profile retrieval with computed counts
- Profile updates (bio, display_name)
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


class TestUserRegistration:
    """Tests for POST /users (user registration)."""

    def test_create_user_success(self, client: TestClient):
        """Test successful user registration returns 201 with correct fields."""
        response = client.post(
            "/users",
            json={
                "username": "john_doe",
                "email": "john@example.com",
                "password": "secure_password_123",
                "display_name": "John Doe",
            },
        )
        assert response.status_code == 201
        data = response.json()
        
        # Verify all expected fields are present
        assert "id" in data
        assert data["username"] == "john_doe"
        assert data["email"] == "john@example.com"
        assert data["display_name"] == "John Doe"
        assert "bio" in data
        
    def test_create_user_password_not_in_response(self, client: TestClient):
        """Test that password is never returned in response."""
        response = client.post(
            "/users",
            json={
                "username": "jane_doe",
                "email": "jane@example.com",
                "password": "another_secure_password",
                "display_name": "Jane Doe",
            },
        )
        assert response.status_code == 201
        data = response.json()
        
        # Password should NOT be in response
        assert "password" not in data
        assert "password_hash" not in data

    def test_create_user_duplicate_username(self, client: TestClient):
        """Test that duplicate username returns 400."""
        # Create first user
        client.post(
            "/users",
            json={
                "username": "duplicate_user",
                "email": "first@example.com",
                "password": "pass123",
                "display_name": "First User",
            },
        )
        
        # Attempt to create second user with same username
        response = client.post(
            "/users",
            json={
                "username": "duplicate_user",
                "email": "second@example.com",
                "password": "pass456",
                "display_name": "Second User",
            },
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_create_multiple_users_unique_ids(self, client: TestClient):
        """Test that multiple users get unique IDs."""
        response1 = client.post(
            "/users",
            json={
                "username": "user1",
                "email": "user1@example.com",
                "password": "pass123",
                "display_name": "User One",
            },
        )
        response2 = client.post(
            "/users",
            json={
                "username": "user2",
                "email": "user2@example.com",
                "password": "pass456",
                "display_name": "User Two",
            },
        )
        
        id1 = response1.json()["id"]
        id2 = response2.json()["id"]
        
        assert id1 != id2
        assert len(id1) > 0
        assert len(id2) > 0


class TestUserProfileRetrieval:
    """Tests for GET /users/{user_id} (profile retrieval)."""

    def test_get_user_profile_success(self, client: TestClient):
        """Test retrieving a user profile returns correct fields and initial counts."""
        # Create a user
        create_response = client.post(
            "/users",
            json={
                "username": "profile_test",
                "email": "profile@example.com",
                "password": "pass123",
                "display_name": "Profile Test User",
            },
        )
        user_id = create_response.json()["id"]
        
        # Get the user profile
        response = client.get(f"/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        
        # Verify correct fields
        # Note: UserProfileResponse is a public view — email is intentionally omitted
        assert data["id"] == user_id
        assert data["username"] == "profile_test"
        assert data["display_name"] == "Profile Test User"
        assert "follower_count" in data
        assert "following_count" in data
        assert "post_count" in data

    def test_get_nonexistent_user_returns_404(self, client: TestClient):
        """Test that getting a non-existent user returns 404."""
        response = client.get("/users/nonexistent-user-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestUserUpdate:
    """Tests for PUT /users/{user_id} (profile updates)."""

    def test_update_user_bio(self, client: TestClient):
        """Test updating user bio returns updated value."""
        # Create a user
        create_response = client.post(
            "/users",
            json={
                "username": "bio_test",
                "email": "bio@example.com",
                "password": "pass123",
                "display_name": "Bio Test User",
            },
        )
        user_id = create_response.json()["id"]
        
        # Update bio
        response = client.put(
            f"/users/{user_id}",
            json={"bio": "This is my bio"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["bio"] == "This is my bio"

    def test_update_user_display_name(self, client: TestClient):
        """Test updating user display_name returns updated value."""
        # Create a user
        create_response = client.post(
            "/users",
            json={
                "username": "name_test",
                "email": "name@example.com",
                "password": "pass123",
                "display_name": "Original Name",
            },
        )
        user_id = create_response.json()["id"]
        
        # Update display_name
        response = client.put(
            f"/users/{user_id}",
            json={"display_name": "Updated Name"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Updated Name"

    def test_update_nonexistent_user_returns_404(self, client: TestClient):
        """Test that updating a non-existent user returns 404."""
        response = client.put(
            "/users/nonexistent-user-id",
            json={"bio": "New bio"},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
