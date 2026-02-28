"""Tests for the URL Shortener API.

Covers:
    - POST /shorten   — happy path, invalid URL, missing URL, duplicate handling
    - GET /{short_code} — happy path (301 redirect), click count increment, 404
    - GET /stats/{short_code} — happy path, 404, click count accuracy
"""

import pytest
from fastapi.testclient import TestClient

from src.url_shortener.main import app
from src.url_shortener import storage


@pytest.fixture(autouse=True)
def clear_storage() -> None:
    """Wipe the in-memory store before every test for isolation."""
    storage.clear_store()
    yield
    storage.clear_store()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, follow_redirects=False)


# ---------------------------------------------------------------------------
# POST /shorten
# ---------------------------------------------------------------------------

class TestShortenEndpoint:
    def test_shorten_valid_url_returns_201(self, client: TestClient) -> None:
        response = client.post("/shorten", json={"url": "https://example.com"})
        assert response.status_code == 201

    def test_shorten_response_contains_expected_fields(self, client: TestClient) -> None:
        response = client.post("/shorten", json={"url": "https://example.com"})
        data = response.json()
        assert "short_code" in data
        assert "original_url" in data
        assert "short_url" in data

    def test_shorten_original_url_matches_input(self, client: TestClient) -> None:
        url = "https://www.google.com/search?q=fastapi"
        response = client.post("/shorten", json={"url": url})
        assert response.json()["original_url"] == url

    def test_shorten_short_url_contains_short_code(self, client: TestClient) -> None:
        response = client.post("/shorten", json={"url": "https://example.com"})
        data = response.json()
        assert data["short_code"] in data["short_url"]

    def test_shorten_short_code_is_alphanumeric(self, client: TestClient) -> None:
        response = client.post("/shorten", json={"url": "https://example.com"})
        code = response.json()["short_code"]
        assert code.isalnum(), f"Short code {code!r} is not alphanumeric"

    def test_shorten_short_code_length_is_7(self, client: TestClient) -> None:
        response = client.post("/shorten", json={"url": "https://example.com"})
        code = response.json()["short_code"]
        assert len(code) == 7

    def test_shorten_two_requests_produce_different_codes(self, client: TestClient) -> None:
        r1 = client.post("/shorten", json={"url": "https://example.com"})
        r2 = client.post("/shorten", json={"url": "https://example.org"})
        assert r1.json()["short_code"] != r2.json()["short_code"]

    def test_shorten_http_url_also_accepted(self, client: TestClient) -> None:
        response = client.post("/shorten", json={"url": "http://example.com"})
        assert response.status_code == 201

    def test_shorten_missing_url_field_returns_422(self, client: TestClient) -> None:
        response = client.post("/shorten", json={})
        assert response.status_code == 422

    def test_shorten_invalid_url_no_scheme_returns_400(self, client: TestClient) -> None:
        response = client.post("/shorten", json={"url": "not-a-url"})
        assert response.status_code == 400

    def test_shorten_ftp_url_returns_400(self, client: TestClient) -> None:
        response = client.post("/shorten", json={"url": "ftp://files.example.com"})
        assert response.status_code == 400

    def test_shorten_empty_string_url_returns_400(self, client: TestClient) -> None:
        response = client.post("/shorten", json={"url": ""})
        assert response.status_code == 400

    def test_shorten_stores_url_in_storage(self, client: TestClient) -> None:
        client.post("/shorten", json={"url": "https://example.com"})
        codes = storage.all_codes()
        assert len(codes) == 1


# ---------------------------------------------------------------------------
# GET /{short_code} — redirect
# ---------------------------------------------------------------------------

class TestRedirectEndpoint:
    def _shorten(self, client: TestClient, url: str) -> str:
        """Helper: create a short URL and return the short_code."""
        response = client.post("/shorten", json={"url": url})
        assert response.status_code == 201
        return response.json()["short_code"]

    def test_redirect_returns_301(self, client: TestClient) -> None:
        code = self._shorten(client, "https://example.com")
        response = client.get(f"/{code}")
        assert response.status_code == 301

    def test_redirect_location_header_is_original_url(self, client: TestClient) -> None:
        url = "https://example.com"
        code = self._shorten(client, url)
        response = client.get(f"/{code}")
        assert response.headers["location"] == url

    def test_redirect_increments_click_count(self, client: TestClient) -> None:
        code = self._shorten(client, "https://example.com")
        client.get(f"/{code}")
        record = storage.get_url(code)
        assert record is not None
        assert record["click_count"] == 1

    def test_redirect_multiple_clicks_tracked(self, client: TestClient) -> None:
        code = self._shorten(client, "https://example.com")
        for _ in range(5):
            client.get(f"/{code}")
        record = storage.get_url(code)
        assert record is not None
        assert record["click_count"] == 5

    def test_redirect_unknown_code_returns_404(self, client: TestClient) -> None:
        response = client.get("/unknownXYZ")
        assert response.status_code == 404

    def test_redirect_404_body_has_detail(self, client: TestClient) -> None:
        response = client.get("/unknownXYZ")
        assert "detail" in response.json()
        assert response.json()["detail"] == "Short code not found"


# ---------------------------------------------------------------------------
# GET /stats/{short_code}
# ---------------------------------------------------------------------------

class TestStatsEndpoint:
    def _shorten(self, client: TestClient, url: str) -> str:
        """Helper: create a short URL and return the short_code."""
        response = client.post("/shorten", json={"url": url})
        assert response.status_code == 201
        return response.json()["short_code"]

    def test_stats_returns_200(self, client: TestClient) -> None:
        code = self._shorten(client, "https://example.com")
        response = client.get(f"/stats/{code}")
        assert response.status_code == 200

    def test_stats_response_contains_expected_fields(self, client: TestClient) -> None:
        code = self._shorten(client, "https://example.com")
        data = client.get(f"/stats/{code}").json()
        for field in ("short_code", "original_url", "created_at", "click_count"):
            assert field in data, f"Missing field: {field}"

    def test_stats_short_code_matches(self, client: TestClient) -> None:
        url = "https://example.com"
        code = self._shorten(client, url)
        data = client.get(f"/stats/{code}").json()
        assert data["short_code"] == code

    def test_stats_original_url_matches(self, client: TestClient) -> None:
        url = "https://example.com"
        code = self._shorten(client, url)
        data = client.get(f"/stats/{code}").json()
        assert data["original_url"] == url

    def test_stats_initial_click_count_is_zero(self, client: TestClient) -> None:
        code = self._shorten(client, "https://example.com")
        data = client.get(f"/stats/{code}").json()
        assert data["click_count"] == 0

    def test_stats_click_count_reflects_redirects(self, client: TestClient) -> None:
        code = self._shorten(client, "https://example.com")
        # Perform 3 redirects
        for _ in range(3):
            client.get(f"/{code}")
        data = client.get(f"/stats/{code}").json()
        assert data["click_count"] == 3

    def test_stats_created_at_is_iso_timestamp(self, client: TestClient) -> None:
        from datetime import datetime
        code = self._shorten(client, "https://example.com")
        data = client.get(f"/stats/{code}").json()
        # Should parse without error
        ts = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        assert ts is not None

    def test_stats_unknown_code_returns_404(self, client: TestClient) -> None:
        response = client.get("/stats/unknownXYZ")
        assert response.status_code == 404

    def test_stats_404_body_has_detail(self, client: TestClient) -> None:
        response = client.get("/stats/unknownXYZ")
        assert response.json()["detail"] == "Short code not found"


# ---------------------------------------------------------------------------
# Storage unit tests
# ---------------------------------------------------------------------------

class TestStorage:
    def test_save_and_get_url(self) -> None:
        storage.save_url("abc123", "https://example.com")
        record = storage.get_url("abc123")
        assert record is not None
        assert record["original_url"] == "https://example.com"
        assert record["click_count"] == 0

    def test_get_nonexistent_returns_none(self) -> None:
        assert storage.get_url("doesnotexist") is None

    def test_save_duplicate_raises_value_error(self) -> None:
        storage.save_url("abc123", "https://example.com")
        with pytest.raises(ValueError, match="already exists"):
            storage.save_url("abc123", "https://other.com")

    def test_increment_clicks_increases_count(self) -> None:
        storage.save_url("abc123", "https://example.com")
        storage.increment_clicks("abc123")
        storage.increment_clicks("abc123")
        record = storage.get_url("abc123")
        assert record is not None
        assert record["click_count"] == 2

    def test_increment_clicks_unknown_code_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            storage.increment_clicks("doesnotexist")

    def test_clear_store_removes_all_entries(self) -> None:
        storage.save_url("abc123", "https://example.com")
        storage.save_url("xyz789", "https://other.com")
        storage.clear_store()
        assert storage.get_url("abc123") is None
        assert storage.get_url("xyz789") is None

    def test_all_codes_returns_saved_codes(self) -> None:
        storage.save_url("code1", "https://a.com")
        storage.save_url("code2", "https://b.com")
        codes = storage.all_codes()
        assert "code1" in codes
        assert "code2" in codes
