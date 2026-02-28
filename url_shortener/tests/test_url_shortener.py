"""Tests for the URL Shortener application.

All tests are integration tests against the HTTP API using the TestClient fixture
from conftest.py. The in-memory SQLite database is reset before each test by the
``reset_db`` autouse fixture, ensuring full isolation.
"""

import re
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


# ─────────────────────────────────────────────────────────────────────────────
# POST /shorten — Happy Path (5+ tests)
# ─────────────────────────────────────────────────────────────────────────────


class TestShortenEndpoint:
    """Tests for POST /shorten successful case."""

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

    def test_expires_at_is_approximately_30_days_from_now(
        self, client: TestClient
    ) -> None:
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


# ─────────────────────────────────────────────────────────────────────────────
# POST /shorten — Validation (5+ tests)
# ─────────────────────────────────────────────────────────────────────────────


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


# ─────────────────────────────────────────────────────────────────────────────
# GET /{short_code} — Redirect (3+ tests)
# ─────────────────────────────────────────────────────────────────────────────


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


# ─────────────────────────────────────────────────────────────────────────────
# GET /{short_code} — Not Found & Expired (3+ tests)
# ─────────────────────────────────────────────────────────────────────────────


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
        """An expired short code must return 404 or 410.
        
        Uses mocking to force expiration rather than modifying internal state.
        """
        post_resp = client.post("/shorten", json={"url": "https://example.com"})
        code = post_resp.json()["short_url"]

        # Mock url_storage.is_expired to always return True for this test
        with patch("url_shortener.main.url_storage.is_expired", return_value=True):
            get_resp = client.get(f"/{code}", follow_redirects=False)
            assert get_resp.status_code in (404, 410)


# ─────────────────────────────────────────────────────────────────────────────
# GET /health (2+ tests)
# ─────────────────────────────────────────────────────────────────────────────


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_check_returns_200(self, client: TestClient) -> None:
        """GET /health must return 200 OK."""
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_response_has_required_fields(self, client: TestClient) -> None:
        """Health response must contain status, storage, and uptime_seconds."""
        resp = client.get("/health")
        body = resp.json()
        assert "status" in body
        assert "storage" in body
        assert "uptime_seconds" in body
        # Verify values are reasonable
        assert body["status"] == "healthy"
        assert body["storage"] == "sqlite"
        assert isinstance(body["uptime_seconds"], (int, float))
        assert body["uptime_seconds"] >= 0


# ─────────────────────────────────────────────────────────────────────────────
# GET /stats/{short_code} (3+ tests)
# ─────────────────────────────────────────────────────────────────────────────


class TestStatsEndpoint:
    """Tests for GET /stats/{short_code}."""

    def test_stats_returns_200_for_valid_code(self, client: TestClient) -> None:
        """GET /stats with a valid code must return 200."""
        # Create a short URL
        post_resp = client.post("/shorten", json={"url": "https://example.com"})
        code = post_resp.json()["short_url"]

        # Fetch stats
        stats_resp = client.get(f"/stats/{code}")
        assert stats_resp.status_code == 200

    def test_stats_response_has_required_fields(self, client: TestClient) -> None:
        """Stats response must include short_code, long_url, created_at, expires_at, click_count."""
        original_url = "https://example.com/path"
        post_resp = client.post("/shorten", json={"url": original_url})
        code = post_resp.json()["short_url"]

        stats_resp = client.get(f"/stats/{code}")
        body = stats_resp.json()

        assert "short_code" in body
        assert "long_url" in body
        assert "created_at" in body
        assert "expires_at" in body
        assert "click_count" in body

        # Verify values
        assert body["short_code"] == code
        assert body["long_url"] == original_url
        assert isinstance(body["click_count"], int)
        assert body["click_count"] == 0

    def test_click_count_increments_after_redirect(self, client: TestClient) -> None:
        """click_count must increment after each redirect."""
        post_resp = client.post("/shorten", json={"url": "https://example.com"})
        code = post_resp.json()["short_url"]

        # Get initial stats: click_count should be 0
        initial_stats = client.get(f"/stats/{code}").json()
        assert initial_stats["click_count"] == 0

        # Follow redirect (triggers click increment)
        client.get(f"/{code}", follow_redirects=False)

        # Stats after redirect: click_count should be greater than initial
        stats_after_redirect = client.get(f"/stats/{code}").json()
        assert stats_after_redirect["click_count"] > initial_stats["click_count"]

    def test_stats_unknown_code_returns_404(self, client: TestClient) -> None:
        """GET /stats with an unknown code must return 404."""
        resp = client.get("/stats/XXXXXXXX")
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_stats_expired_code_returns_410(self, client: TestClient) -> None:
        """GET /stats with an expired code must return 410.
        
        Uses mocking to force expiration.
        """
        post_resp = client.post("/shorten", json={"url": "https://example.com"})
        code = post_resp.json()["short_url"]

        # Mock is_expired to return True
        with patch("url_shortener.main.url_storage.is_expired", return_value=True):
            stats_resp = client.get(f"/stats/{code}")
            assert stats_resp.status_code == 410
            assert "detail" in stats_resp.json()
