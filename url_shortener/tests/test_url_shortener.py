"""Tests for the URL Shortener application."""

import re
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from url_shortener.main import app
from url_shortener.storage import URLStorage, url_storage


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clear_storage():
    """Reset the module-level singleton store before each test."""
    url_storage._store.clear()
    yield
    url_storage._store.clear()


@pytest.fixture()
def client() -> TestClient:
    """Return a TestClient wired to the FastAPI app."""
    return TestClient(app, raise_server_exceptions=True)


# ── POST /shorten — happy path ─────────────────────────────────────────────────

class TestShortenEndpoint:
    """Tests for POST /shorten."""

    def test_returns_201_on_valid_url(self, client: TestClient) -> None:
        """POST /shorten with a valid URL should respond 201."""
        resp = client.post("/shorten", json={"url": "https://example.com/very/long/path"})
        assert resp.status_code == 201

    def test_response_contains_required_fields(self, client: TestClient) -> None:
        """Response JSON must include short_url, long_url, expires_at."""
        resp = client.post("/shorten", json={"url": "https://example.com"})
        body = resp.json()
        assert "short_url" in body
        assert "long_url" in body
        assert "expires_at" in body

    def test_short_url_is_exactly_8_alphanumeric_chars(self, client: TestClient) -> None:
        """The short_url value must be exactly 8 alphanumeric characters."""
        resp = client.post("/shorten", json={"url": "https://example.com"})
        short_url = resp.json()["short_url"]
        assert len(short_url) == 8
        assert re.fullmatch(r"[A-Za-z0-9]{8}", short_url), (
            f"short_url '{short_url}' contains non-alphanumeric characters"
        )

    def test_long_url_echoed_in_response(self, client: TestClient) -> None:
        """The long_url field must mirror the submitted URL."""
        url = "https://www.example.com/some/very/long/path?foo=bar"
        resp = client.post("/shorten", json={"url": url})
        assert resp.json()["long_url"] == url

    def test_expires_at_is_iso8601_string(self, client: TestClient) -> None:
        """expires_at must be a parseable ISO 8601 datetime string."""
        resp = client.post("/shorten", json={"url": "https://example.com"})
        expires_at = resp.json()["expires_at"]
        # Should not raise
        parsed = datetime.fromisoformat(expires_at)
        assert parsed is not None

    def test_expires_at_is_approximately_30_days_from_now(self, client: TestClient) -> None:
        """expires_at should be ~30 days in the future (within 5 seconds tolerance)."""
        resp = client.post("/shorten", json={"url": "https://example.com"})
        expires_at = datetime.fromisoformat(resp.json()["expires_at"])
        expected = datetime.now(tz=timezone.utc) + timedelta(days=30)
        delta = abs((expires_at - expected).total_seconds())
        assert delta < 5, f"expires_at is {delta:.1f}s away from expected 30-day window"

    def test_multiple_shortens_produce_different_codes(self, client: TestClient) -> None:
        """Two identical URLs should (almost certainly) get different short codes."""
        url = "https://example.com"
        codes = {
            client.post("/shorten", json={"url": url}).json()["short_url"]
            for _ in range(10)
        }
        # With 62^8 possible codes, the probability of a collision in 10 draws is negligible
        assert len(codes) >= 2, "Expected at least 2 distinct codes for 10 shortens"

    def test_http_url_is_accepted(self, client: TestClient) -> None:
        """Plain http:// URLs (not just https://) should also be accepted."""
        resp = client.post("/shorten", json={"url": "http://example.com/path"})
        assert resp.status_code == 201


# ── POST /shorten — validation errors ─────────────────────────────────────────

class TestShortenValidation:
    """Tests for POST /shorten input validation."""

    def test_empty_url_returns_400(self, client: TestClient) -> None:
        """An empty url string must result in HTTP 400."""
        resp = client.post("/shorten", json={"url": ""})
        assert resp.status_code == 400

    def test_whitespace_url_returns_400(self, client: TestClient) -> None:
        """A whitespace-only url must result in HTTP 400."""
        resp = client.post("/shorten", json={"url": "   "})
        assert resp.status_code == 400

    def test_url_without_scheme_returns_400(self, client: TestClient) -> None:
        """A URL without http/https scheme must result in HTTP 400."""
        resp = client.post("/shorten", json={"url": "example.com/path"})
        assert resp.status_code == 400

    def test_missing_url_field_returns_400(self, client: TestClient) -> None:
        """Missing the url field entirely must result in HTTP 400."""
        resp = client.post("/shorten", json={})
        assert resp.status_code == 400

    def test_non_http_scheme_returns_400(self, client: TestClient) -> None:
        """ftp:// and other non-http schemes must result in HTTP 400."""
        resp = client.post("/shorten", json={"url": "ftp://example.com"})
        assert resp.status_code == 400

    def test_error_response_has_detail_field(self, client: TestClient) -> None:
        """Error responses must contain a 'detail' key."""
        resp = client.post("/shorten", json={"url": ""})
        assert "detail" in resp.json()


# ── GET /{short_code} — happy path ────────────────────────────────────────────

class TestRedirectEndpoint:
    """Tests for GET /{short_code}."""

    def test_returns_307_redirect(self, client: TestClient) -> None:
        """Known short code must yield a 307 Temporary Redirect."""
        post_resp = client.post("/shorten", json={"url": "https://example.com"})
        code = post_resp.json()["short_url"]

        # Don't follow redirects so we can inspect the 307 directly
        get_resp = client.get(f"/{code}", follow_redirects=False)
        assert get_resp.status_code == 307

    def test_location_header_matches_original_url(self, client: TestClient) -> None:
        """The Location header on the redirect must equal the original URL."""
        original = "https://www.example.com/path?query=1"
        post_resp = client.post("/shorten", json={"url": original})
        code = post_resp.json()["short_url"]

        get_resp = client.get(f"/{code}", follow_redirects=False)
        assert get_resp.headers["location"] == original

    def test_following_redirect_reaches_destination(self, client: TestClient) -> None:
        """Following the redirect should land at the long URL (or attempt to)."""
        # We test that the client would follow and that the code lookup works;
        # actual external HTTP calls are out-of-scope for unit tests.
        post_resp = client.post("/shorten", json={"url": "https://example.com"})
        code = post_resp.json()["short_url"]

        get_resp = client.get(f"/{code}", follow_redirects=False)
        assert get_resp.status_code == 307
        assert "location" in get_resp.headers


# ── GET /{short_code} — not found / expired ───────────────────────────────────

class TestRedirectErrors:
    """Tests for GET /{short_code} error cases."""

    def test_unknown_code_returns_404(self, client: TestClient) -> None:
        """A code that was never created must return 404."""
        resp = client.get("/XXXXXXXX", follow_redirects=False)
        assert resp.status_code == 404

    def test_unknown_code_response_has_detail(self, client: TestClient) -> None:
        """404 response body must contain a 'detail' key."""
        resp = client.get("/ZZZZZZZZ", follow_redirects=False)
        assert "detail" in resp.json()

    def test_expired_code_returns_404_or_410(self, client: TestClient) -> None:
        """An expired short code must return 404 or 410."""
        post_resp = client.post("/shorten", json={"url": "https://example.com"})
        code = post_resp.json()["short_url"]

        # Force-expire the entry by winding its expires_at into the past
        url_storage._store[code]["expires_at"] = (
            datetime.now(tz=timezone.utc) - timedelta(seconds=1)
        )

        get_resp = client.get(f"/{code}", follow_redirects=False)
        assert get_resp.status_code in (404, 410)

    def test_expired_code_response_has_detail(self, client: TestClient) -> None:
        """Expired code response body must contain a 'detail' key."""
        post_resp = client.post("/shorten", json={"url": "https://example.com"})
        code = post_resp.json()["short_url"]
        url_storage._store[code]["expires_at"] = (
            datetime.now(tz=timezone.utc) - timedelta(seconds=1)
        )
        get_resp = client.get(f"/{code}", follow_redirects=False)
        assert "detail" in get_resp.json()


# ── URLStorage unit tests ──────────────────────────────────────────────────────

class TestURLStorage:
    """Unit tests for the URLStorage class in isolation."""

    def test_create_returns_entry_with_all_keys(self) -> None:
        """create() must return a dict with the required keys."""
        storage = URLStorage()
        entry = storage.create("https://example.com")
        assert "short_code" in entry
        assert "long_url" in entry
        assert "created_at" in entry
        assert "expires_at" in entry

    def test_create_short_code_is_8_chars(self) -> None:
        """Generated short code must be exactly 8 characters long."""
        storage = URLStorage()
        entry = storage.create("https://example.com")
        assert len(entry["short_code"]) == 8

    def test_create_short_code_is_alphanumeric(self) -> None:
        """Generated short code must be alphanumeric only."""
        storage = URLStorage()
        for _ in range(20):
            entry = storage.create("https://example.com")
            assert re.fullmatch(r"[A-Za-z0-9]{8}", entry["short_code"])

    def test_create_stores_correct_long_url(self) -> None:
        """create() must persist and return the original long URL."""
        storage = URLStorage()
        url = "https://example.com/path?a=1&b=2"
        entry = storage.create(url)
        assert entry["long_url"] == url

    def test_create_expires_at_is_30_days_after_created_at(self) -> None:
        """expires_at must be exactly 30 days after created_at."""
        storage = URLStorage()
        entry = storage.create("https://example.com")
        delta = entry["expires_at"] - entry["created_at"]
        assert delta == timedelta(days=30)

    def test_get_returns_none_for_unknown_code(self) -> None:
        """get() must return None for a code that was never stored."""
        storage = URLStorage()
        assert storage.get("XXXXXXXX") is None

    def test_get_returns_entry_for_known_code(self) -> None:
        """get() must return the same entry that create() returned."""
        storage = URLStorage()
        entry = storage.create("https://example.com")
        retrieved = storage.get(entry["short_code"])
        assert retrieved is not None
        assert retrieved["short_code"] == entry["short_code"]
        assert retrieved["long_url"] == entry["long_url"]

    def test_is_expired_returns_false_for_fresh_entry(self) -> None:
        """is_expired() must return False for a newly created entry."""
        storage = URLStorage()
        entry = storage.create("https://example.com")
        assert storage.is_expired(entry) is False

    def test_is_expired_returns_true_for_past_entry(self) -> None:
        """is_expired() must return True when expires_at is in the past."""
        storage = URLStorage()
        entry = storage.create("https://example.com")
        # Manually wind back expires_at
        entry["expires_at"] = datetime.now(tz=timezone.utc) - timedelta(seconds=1)
        assert storage.is_expired(entry) is True

    def test_multiple_creates_are_independent(self) -> None:
        """Each call to create() should produce a separately retrievable entry."""
        storage = URLStorage()
        e1 = storage.create("https://a.example.com")
        e2 = storage.create("https://b.example.com")
        assert storage.get(e1["short_code"]) is not None
        assert storage.get(e2["short_code"]) is not None
        assert e1["short_code"] != e2["short_code"] or e1["long_url"] != e2["long_url"]
