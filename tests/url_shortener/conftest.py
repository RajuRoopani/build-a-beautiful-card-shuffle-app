"""Pytest configuration for URL Shortener tests.

Provides a fresh TestClient and auto-clears storage between tests.
"""

import pytest
from fastapi.testclient import TestClient

from src.url_shortener.main import app
from src.url_shortener import storage


@pytest.fixture(autouse=True)
def clear_storage() -> None:
    """Wipe the in-memory store before and after every test for isolation."""
    storage.clear_store()
    yield
    storage.clear_store()


@pytest.fixture
def client() -> TestClient:
    """Return a TestClient that does NOT follow redirects (so we can assert 301)."""
    return TestClient(app, follow_redirects=False)
