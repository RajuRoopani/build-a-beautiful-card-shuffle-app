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
def sample_rider(client: TestClient):
    """Create and return a sample rider for testing."""
    response = client.post("/api/riders", json={
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "555-0100"
    })
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def sample_driver(client: TestClient):
    """Create and return a sample driver for testing."""
    response = client.post("/api/drivers", json={
        "name": "Jane Driver",
        "email": "jane@example.com",
        "phone": "555-0200",
        "vehicle_make": "Toyota",
        "vehicle_model": "Camry",
        "license_plate": "ABC-1234"
    })
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def sample_rider(client):
    """Create and return a test rider."""
    resp = client.post(
        "/api/riders",
        json={"name": "John Doe", "email": "john@example.com", "phone": "555-0100"},
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def sample_driver(client):
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
