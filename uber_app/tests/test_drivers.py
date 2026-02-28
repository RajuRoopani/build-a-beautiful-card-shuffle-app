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

    assert driver1["id"] != driver2["id"]
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

    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        re.IGNORECASE
    )
    assert uuid_pattern.match(data["id"]), f"ID {data['id']} is not a valid UUID"


def test_get_driver(client: TestClient, sample_driver: dict):
    """Test retrieving a driver by ID returns correct profile."""
    driver_id = sample_driver["id"]
    response = client.get(f"/api/drivers/{driver_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == driver_id
    assert data["name"] == sample_driver["name"]
    assert data["email"] == sample_driver["email"]
    assert data["vehicle_make"] == sample_driver["vehicle_make"]
    assert data["license_plate"] == sample_driver["license_plate"]


def test_get_driver_not_found(client: TestClient):
    """Test retrieving a nonexistent driver returns 404."""
    response = client.get("/api/drivers/nonexistent-driver-id")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_update_driver_name(client: TestClient, sample_driver: dict):
    """Test partially updating a driver's name via PUT."""
    driver_id = sample_driver["id"]
    response = client.put(
        f"/api/drivers/{driver_id}",
        json={"name": "Updated Name"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    # Other fields should be unchanged
    assert data["email"] == sample_driver["email"]
    assert data["phone"] == sample_driver["phone"]
    assert data["vehicle_make"] == sample_driver["vehicle_make"]
    assert data["vehicle_model"] == sample_driver["vehicle_model"]
    assert data["license_plate"] == sample_driver["license_plate"]


def test_update_driver_vehicle_info(client: TestClient, sample_driver: dict):
    """Test updating a driver's vehicle information."""
    driver_id = sample_driver["id"]
    response = client.put(
        f"/api/drivers/{driver_id}",
        json={
            "vehicle_make": "Honda",
            "vehicle_model": "Accord",
            "license_plate": "NEW-PLATE"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["vehicle_make"] == "Honda"
    assert data["vehicle_model"] == "Accord"
    assert data["license_plate"] == "NEW-PLATE"
    # Name/contact unchanged
    assert data["name"] == sample_driver["name"]
    assert data["email"] == sample_driver["email"]


def test_update_driver_not_found(client: TestClient):
    """Test updating a nonexistent driver returns 404."""
    response = client.put(
        "/api/drivers/nonexistent-id",
        json={"name": "Ghost Driver"}
    )
    assert response.status_code == 404
    assert "detail" in response.json()


def test_get_driver_rides_empty(client: TestClient, sample_driver: dict):
    """Test getting rides for a driver who has accepted no rides yet returns empty list."""
    driver_id = sample_driver["id"]
    response = client.get(f"/api/drivers/{driver_id}/rides")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_driver_rides_not_found(client: TestClient):
    """Test getting rides for a nonexistent driver returns 404."""
    response = client.get("/api/drivers/nonexistent-driver-id/rides")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_get_driver_rides_after_acceptance(
    client: TestClient, sample_rider: dict, sample_driver: dict
):
    """Test that a driver's ride history includes rides they have accepted."""
    driver_id = sample_driver["id"]

    # Create a ride
    ride_resp = client.post("/api/rides", json={
        "rider_id": sample_rider["id"],
        "pickup_location": "100 Main St",
        "dropoff_location": "200 Oak Ave",
    })
    ride_id = ride_resp.json()["id"]

    # Driver accepts the ride
    client.put(f"/api/rides/{ride_id}/accept", json={"driver_id": driver_id})

    # Check driver ride history
    response = client.get(f"/api/drivers/{driver_id}/rides")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == ride_id
    assert data[0]["driver_id"] == driver_id
    assert data[0]["status"] == "accepted"
