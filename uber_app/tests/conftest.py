"""Shared pytest fixtures for the Uber app test suite."""

import pytest
from fastapi.testclient import TestClient

from uber_app.main import app
from uber_app import storage


@pytest.fixture(autouse=True)
def clear_storage():
    """Reset in-memory storage before every test to ensure isolation."""
    storage.clear_all()
    yield
    storage.clear_all()


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_rider(client: TestClient) -> dict:
    """Create and return a test rider."""
    resp = client.post(
        "/api/riders",
        json={"name": "John Doe", "email": "john@example.com", "phone": "555-0100"},
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def sample_driver(client: TestClient) -> dict:
    """Create and return a test driver."""
    resp = client.post(
        "/api/drivers",
        json={
            "name": "Jane Driver",
            "email": "jane@example.com",
            "phone": "555-0200",
            "vehicle_make": "Toyota",
            "vehicle_model": "Camry",
            "license_plate": "ABC-1234",
        },
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def sample_ride(client: TestClient, sample_rider: dict) -> dict:
    """Create and return a test ride in 'requested' status."""
    resp = client.post(
        "/api/rides",
        json={
            "rider_id": sample_rider["id"],
            "pickup_location": "123 Main St",
            "dropoff_location": "456 Oak Ave",
        },
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def accepted_ride(client: TestClient, sample_ride: dict, sample_driver: dict) -> dict:
    """Create a ride that has been accepted by a driver."""
    resp = client.put(
        f"/api/rides/{sample_ride['id']}/accept",
        json={"driver_id": sample_driver["id"]},
    )
    assert resp.status_code == 200
    return resp.json()
