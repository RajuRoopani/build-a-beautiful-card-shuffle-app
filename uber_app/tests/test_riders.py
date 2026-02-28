"""Tests for the Riders router."""

import re
import pytest
from fastapi.testclient import TestClient


def test_create_rider(client: TestClient):
    """Test creating a rider with valid data — AC1.
    
    Expected: 201 response with id, name, email, phone fields.
    """
    response = client.post("/api/riders", json={
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "phone": "555-1234"
    })
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "Alice Johnson"
    assert data["email"] == "alice@example.com"
    assert data["phone"] == "555-1234"


def test_create_rider_fields(client: TestClient):
    """Test that all required fields are returned in the response.
    
    Verifies the response model matches RiderResponse exactly.
    """
    response = client.post("/api/riders", json={
        "name": "Bob Smith",
        "email": "bob@example.com",
        "phone": "555-5678"
    })
    
    assert response.status_code == 201
    data = response.json()
    
    # Check all expected fields are present
    expected_fields = {"id", "name", "email", "phone"}
    assert set(data.keys()) == expected_fields
    
    # Verify types
    assert isinstance(data["id"], str)
    assert isinstance(data["name"], str)
    assert isinstance(data["email"], str)
    assert isinstance(data["phone"], str)


def test_get_rider_rides_empty(client: TestClient, sample_rider):
    """Test getting rides for a rider with no rides yet.
    
    Expected: 200 with empty list.
    """
    rider_id = sample_rider["id"]
    response = client.get(f"/api/riders/{rider_id}/rides")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_rider_rides_not_found(client: TestClient):
    """Test getting rides for a non-existent rider.
    
    Expected: 404 error.
    """
    fake_rider_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/riders/{fake_rider_id}/rides")
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_create_multiple_riders(client: TestClient):
    """Test creating multiple riders and verifying they have different IDs.
    
    Expected: Each rider has a unique UUID-like ID.
    """
    # Create first rider
    response1 = client.post("/api/riders", json={
        "name": "Rider One",
        "email": "rider1@example.com",
        "phone": "555-0001"
    })
    assert response1.status_code == 201
    rider1 = response1.json()
    
    # Create second rider
    response2 = client.post("/api/riders", json={
        "name": "Rider Two",
        "email": "rider2@example.com",
        "phone": "555-0002"
    })
    assert response2.status_code == 201
    rider2 = response2.json()
    
    # Verify IDs are different
    assert rider1["id"] != rider2["id"]
    
    # Verify both IDs look like UUIDs (standard format)
    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        re.IGNORECASE
    )
    assert uuid_pattern.match(rider1["id"])
    assert uuid_pattern.match(rider2["id"])


def test_rider_id_is_uuid(client: TestClient):
    """Test that rider IDs follow UUID format.
    
    Expected: ID matches standard UUID v4 pattern.
    """
    response = client.post("/api/riders", json={
        "name": "UUID Test Rider",
        "email": "uuid@example.com",
        "phone": "555-9999"
    })
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify UUID format: 8-4-4-4-12 hexadecimal digits
    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        re.IGNORECASE
    )
    assert uuid_pattern.match(data["id"]), f"ID {data['id']} is not a valid UUID"
