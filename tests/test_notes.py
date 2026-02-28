"""Comprehensive test suite for the Note-Taking REST API.

Tests cover all 5 CRUD endpoints, error cases, validation, and partial updates.
Uses reset_storage() fixture to ensure test isolation.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import models


client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_storage():
    """Reset storage before and after each test to ensure isolation."""
    models.reset_storage()
    yield
    models.reset_storage()


# ==============================================================================
# Tests for POST /notes (Create)
# ==============================================================================


def test_create_note_success():
    """Test successful note creation returns 201 with all fields."""
    response = client.post(
        "/notes",
        json={"title": "My Note", "content": "This is content"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "My Note"
    assert data["content"] == "This is content"
    assert "created_at" in data
    assert "updated_at" in data
    assert data["created_at"] == data["updated_at"]


def test_create_multiple_notes_increments_id():
    """Test that creating multiple notes assigns incrementing IDs."""
    response1 = client.post(
        "/notes",
        json={"title": "First", "content": "First content"}
    )
    response2 = client.post(
        "/notes",
        json={"title": "Second", "content": "Second content"}
    )
    assert response1.json()["id"] == 1
    assert response2.json()["id"] == 2


def test_create_note_empty_title_validation_error():
    """Test that empty title returns 422 validation error."""
    response = client.post(
        "/notes",
        json={"title": "", "content": "Valid content"}
    )
    assert response.status_code == 422


def test_create_note_empty_content_validation_error():
    """Test that empty content returns 422 validation error."""
    response = client.post(
        "/notes",
        json={"title": "Valid Title", "content": ""}
    )
    assert response.status_code == 422


def test_create_note_missing_title():
    """Test that missing title returns 422 validation error."""
    response = client.post(
        "/notes",
        json={"content": "Content without title"}
    )
    assert response.status_code == 422


def test_create_note_missing_content():
    """Test that missing content returns 422 validation error."""
    response = client.post(
        "/notes",
        json={"title": "Title without content"}
    )
    assert response.status_code == 422


# ==============================================================================
# Tests for GET /notes (List All)
# ==============================================================================


def test_list_notes_empty():
    """Test that listing notes returns empty list when no notes exist."""
    response = client.get("/notes")
    assert response.status_code == 200
    assert response.json() == []


def test_list_notes_returns_all_notes():
    """Test that listing notes returns all created notes."""
    # Create 3 notes
    client.post("/notes", json={"title": "Note 1", "content": "Content 1"})
    client.post("/notes", json={"title": "Note 2", "content": "Content 2"})
    client.post("/notes", json={"title": "Note 3", "content": "Content 3"})

    response = client.get("/notes")
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) == 3
    assert notes[0]["title"] == "Note 1"
    assert notes[1]["title"] == "Note 2"
    assert notes[2]["title"] == "Note 3"


def test_list_notes_contains_all_fields():
    """Test that each note in list contains all required fields."""
    client.post("/notes", json={"title": "Test", "content": "Content"})

    response = client.get("/notes")
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) == 1
    note = notes[0]
    assert "id" in note
    assert "title" in note
    assert "content" in note
    assert "created_at" in note
    assert "updated_at" in note


# ==============================================================================
# Tests for GET /notes/{id} (Get Single Note)
# ==============================================================================


def test_get_note_by_id_success():
    """Test retrieving a single note by ID."""
    create_response = client.post(
        "/notes",
        json={"title": "Target Note", "content": "Target content"}
    )
    note_id = create_response.json()["id"]

    response = client.get(f"/notes/{note_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == note_id
    assert data["title"] == "Target Note"
    assert data["content"] == "Target content"


def test_get_note_nonexistent_returns_404():
    """Test that getting a non-existent note returns 404."""
    response = client.get("/notes/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Note not found"


def test_get_note_from_multiple_returns_correct():
    """Test that getting a note from multiple returns the correct one."""
    client.post("/notes", json={"title": "Note 1", "content": "Content 1"})
    response2 = client.post("/notes", json={"title": "Note 2", "content": "Content 2"})
    client.post("/notes", json={"title": "Note 3", "content": "Content 3"})

    note_id = response2.json()["id"]
    response = client.get(f"/notes/{note_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Note 2"


# ==============================================================================
# Tests for PUT /notes/{id} (Update)
# ==============================================================================


def test_update_note_title_only():
    """Test partial update of note title only."""
    create_response = client.post(
        "/notes",
        json={"title": "Original Title", "content": "Original content"}
    )
    note_id = create_response.json()["id"]
    original_updated_at = create_response.json()["updated_at"]

    response = client.put(
        f"/notes/{note_id}",
        json={"title": "Updated Title"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == note_id
    assert data["title"] == "Updated Title"
    assert data["content"] == "Original content"
    assert data["updated_at"] != original_updated_at


def test_update_note_content_only():
    """Test partial update of note content only."""
    create_response = client.post(
        "/notes",
        json={"title": "Original Title", "content": "Original content"}
    )
    note_id = create_response.json()["id"]
    original_updated_at = create_response.json()["updated_at"]

    response = client.put(
        f"/notes/{note_id}",
        json={"content": "Updated content"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == note_id
    assert data["title"] == "Original Title"
    assert data["content"] == "Updated content"
    assert data["updated_at"] != original_updated_at


def test_update_note_both_fields():
    """Test updating both title and content."""
    create_response = client.post(
        "/notes",
        json={"title": "Original Title", "content": "Original content"}
    )
    note_id = create_response.json()["id"]

    response = client.put(
        f"/notes/{note_id}",
        json={"title": "New Title", "content": "New content"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert data["content"] == "New content"


def test_update_note_nonexistent_returns_404():
    """Test that updating a non-existent note returns 404."""
    response = client.put(
        "/notes/999",
        json={"title": "Updated"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Note not found"


def test_update_note_empty_title_validation_error():
    """Test that empty title in update returns 422."""
    create_response = client.post(
        "/notes",
        json={"title": "Original", "content": "Content"}
    )
    note_id = create_response.json()["id"]

    response = client.put(
        f"/notes/{note_id}",
        json={"title": ""}
    )
    assert response.status_code == 422


def test_update_note_empty_content_validation_error():
    """Test that empty content in update returns 422."""
    create_response = client.post(
        "/notes",
        json={"title": "Title", "content": "Original"}
    )
    note_id = create_response.json()["id"]

    response = client.put(
        f"/notes/{note_id}",
        json={"content": ""}
    )
    assert response.status_code == 422


def test_update_note_updates_updated_at_timestamp():
    """Test that updated_at timestamp changes after update."""
    create_response = client.post(
        "/notes",
        json={"title": "Original", "content": "Content"}
    )
    note_id = create_response.json()["id"]
    created_at = create_response.json()["created_at"]
    original_updated_at = create_response.json()["updated_at"]

    response = client.put(
        f"/notes/{note_id}",
        json={"title": "Updated"}
    )
    updated_data = response.json()
    assert updated_data["created_at"] == created_at
    assert updated_data["updated_at"] != original_updated_at


# ==============================================================================
# Tests for DELETE /notes/{id}
# ==============================================================================


def test_delete_note_success():
    """Test successful deletion of a note."""
    create_response = client.post(
        "/notes",
        json={"title": "To Delete", "content": "Delete me"}
    )
    note_id = create_response.json()["id"]

    response = client.delete(f"/notes/{note_id}")
    assert response.status_code == 200
    assert response.json()["detail"] == "Note deleted"


def test_delete_note_removes_from_list():
    """Test that deleted note no longer appears in list."""
    client.post("/notes", json={"title": "Keep", "content": "Keep this"})
    delete_response = client.post(
        "/notes",
        json={"title": "Delete", "content": "Delete this"}
    )
    note_id = delete_response.json()["id"]

    client.delete(f"/notes/{note_id}")

    list_response = client.get("/notes")
    notes = list_response.json()
    assert len(notes) == 1
    assert notes[0]["title"] == "Keep"


def test_delete_note_nonexistent_returns_404():
    """Test that deleting a non-existent note returns 404."""
    response = client.delete("/notes/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Note not found"


def test_delete_note_cannot_get_after_deletion():
    """Test that getting a deleted note returns 404."""
    create_response = client.post(
        "/notes",
        json={"title": "Delete Me", "content": "Content"}
    )
    note_id = create_response.json()["id"]

    client.delete(f"/notes/{note_id}")

    response = client.get(f"/notes/{note_id}")
    assert response.status_code == 404


def test_delete_note_clears_list():
    """Test that deleting all notes results in empty list."""
    response1 = client.post("/notes", json={"title": "Note 1", "content": "Content 1"})
    response2 = client.post("/notes", json={"title": "Note 2", "content": "Content 2"})

    client.delete(f"/notes/{response1.json()['id']}")
    client.delete(f"/notes/{response2.json()['id']}")

    list_response = client.get("/notes")
    assert list_response.json() == []
