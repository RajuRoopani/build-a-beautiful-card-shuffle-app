"""
Shared pytest fixtures for the Slack app test suite.
"""
import pytest
from fastapi.testclient import TestClient

from slack_app.main import app
from slack_app.storage import reset_storage


@pytest.fixture(autouse=True)
def clear_storage():
    """Reset in-memory storage before every test to ensure isolation."""
    reset_storage()
    yield
    reset_storage()


@pytest.fixture
def client() -> TestClient:
    """Return a FastAPI test client wired to the Slack app."""
    return TestClient(app)


@pytest.fixture
def two_users(client: TestClient):
    """Create and return two users as (user_a_dict, user_b_dict)."""
    resp_a = client.post("/users", json={"username": "alice", "display_name": "Alice"})
    resp_b = client.post("/users", json={"username": "bob", "display_name": "Bob"})
    assert resp_a.status_code == 201
    assert resp_b.status_code == 201
    return resp_a.json(), resp_b.json()
