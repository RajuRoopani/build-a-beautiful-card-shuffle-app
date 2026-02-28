"""Tests for the Drivers router."""

import re
import pytest
from fastapi.testclient import TestClient


def test_create_driver(client: TestClient):
    """Test creating a driver with valid data — AC6.
    
    Expected: 201 response with id and all fields including vehicle info.
    """
    response = client.post("/api/drivers", json={
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "555-2000",
        "vehicle_make": "Honda",
        "vehicle_model": "Civic",
        "license_plate": "XYZ-9876"
    })
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify basic fields
    assert "id" in data
    assert data["name"] == "Jane Doe"
    assert data["email"] == "jane@example.com"
    assert data["phone"] == "555-2000"
    
    # Verify vehicle fields
    assert data["vehicle_make"] == "Honda"
    assert data["vehicle_model"] == "Civic"
    assert data["license_plate"] == "XYZ-9876"


def test_create_driver_fields(client: TestClient):
    """Test that all required driver fields are returned in the response.
    
    Specifically verifies vehicle_make, vehicle_model, and license_plate.
    """
    response = client.post("/api/drivers", json={
        "name": "John Smith",
        "email": "john@example.com",
        "phone": "555-3000",
        "vehicle_make": "Ford",
        "vehicle_model": "Focus",
        "license_plate": "ABC-5555"
    })
    
    assert response.status_code == 201
    data = response.json()
    
    # Check all expected fields are present
    expected_fields = {
        "id", "name", "email", "phone",
        "vehicle_make", "vehicle_model", "license_plate"
    }
    assert set(data.keys()) == expected_fields
    
    # Verify vehicle-specific fields
    assert data["vehicle_make"] == "Ford"
    assert data["vehicle_model"] == "Focus"
    assert data["license_plate"] == "ABC-5555"
    
    # Verify types
    assert isinstance(data["id"], str)
    assert isinstance(data["vehicle_make"], str)
    assert isinstance(data["vehicle_model"], str)
    assert isinstance(data["license_plate"], str)


def test_create_multiple_drivers(client: TestClient):
    """Test creating multiple drivers and verifying they have different IDs.
    
    Expected: Each driver has a unique ID.
    """
    # Create first driver
    response1 = client.post("/api/drivers", json={
        "name": "Driver One",
        "email": "driver1@example.com",
        "phone": "555-4001",
        "vehicle_make": "Toyota",
        "vehicle_model": "Prius",
        "license_plate": "GREEN-1"
    })
    assert response1.status_code == 201
    driver1 = response1.json()
    
    # Create second driver
    response2 = client.post("/api/drivers", json={
        "name": "Driver Two",
        "email": "driver2@example.com",
        "phone": "555-4002",
        "vehicle_make": "Tesla",
        "vehicle_model": "Model 3",
        "license_plate": "ELECTRIC-1"
    })
    assert response2.status_code == 201
    driver2 = response2.json()
    
    # Verify IDs are different
    assert driver1["id"] != driver2["id"]
    
    # Verify data integrity
    assert driver1["name"] == "Driver One"
    assert driver2["name"] == "Driver Two"


def test_driver_id_is_uuid(client: TestClient):
    """Test that driver IDs follow UUID format.
    
    Expected: ID matches standard UUID v4 pattern.
    """
    response = client.post("/api/drivers", json={
        "name": "UUID Test Driver",
        "email": "uuid.driver@example.com",
        "phone": "555-5555",
        "vehicle_make": "BMW",
        "vehicle_model": "X5",
        "license_plate": "UUUUUU"
    })
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify UUID format: 8-4-4-4-12 hexadecimal digits
    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        re.IGNORECASE
    )
    assert uuid_pattern.match(data["id"]), f"ID {data['id']} is not a valid UUID"


def test_rider_id_is_uuid(client: TestClient):
    """Test that rider IDs (created via riders endpoint) follow UUID format.
    
    Expected: Rider IDs match standard UUID v4 pattern.
    """
    response = client.post("/api/riders", json={
        "name": "UUID Test Rider",
        "email": "uuid.rider@example.com",
        "phone": "555-5500"
    })
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify UUID format: 8-4-4-4-12 hexadecimal digits
    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        re.IGNORECASE
    )
    assert uuid_pattern.match(data["id"]), f"ID {data['id']} is not a valid UUID"
