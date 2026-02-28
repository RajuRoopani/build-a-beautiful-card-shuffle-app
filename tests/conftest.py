"""
tests/conftest.py
─────────────────
Shared pytest fixtures for the Instagram-like API test suite.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Return a synchronous TestClient wrapping the FastAPI app.

    Scoped to the session so the app is only instantiated once per test run.
    Individual tests that mutate the in-memory stores should reset them via
    a function-scoped fixture that clears the relevant dicts/sets.
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=False)
def reset_stores():
    """Optional fixture: clears all in-memory data stores before a test.

    Mark a test with ``@pytest.mark.usefixtures('reset_stores')`` or
    declare it as a parameter to get a clean slate.
    """
    import app.models as m

    m.users_db.clear()
    m.posts_db.clear()
    m.follows.clear()
    m.followers.clear()
    m.likes.clear()
    m.shares_db.clear()
    m.post_shares.clear()
    m.blocks.clear()

    yield

    # Teardown — clear again after test so later tests aren't polluted.
    m.users_db.clear()
    m.posts_db.clear()
    m.follows.clear()
    m.followers.clear()
    m.likes.clear()
    m.shares_db.clear()
    m.post_shares.clear()
    m.blocks.clear()
