"""Tests for the token-bucket rate limiter.

Covers:
    - TokenBucket unit tests (consume, refill, capacity cap)
    - RateLimitMiddleware integration tests via FastAPI TestClient
      (allowed requests, 429 enforcement, Retry-After header,
       per-IP isolation, X-Forwarded-For handling)
"""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from src.url_shortener.rate_limiter import (
    RATE_LIMIT,
    WINDOW_SECONDS,
    RateLimitMiddleware,
    TokenBucket,
)
from src.url_shortener.main import app
from src.url_shortener import storage


# ===========================================================================
# Helpers / fixtures
# ===========================================================================


@pytest.fixture(autouse=True)
def clear_storage() -> None:
    """Isolate storage between tests."""
    storage.clear_store()
    yield
    storage.clear_store()


def _get_middleware() -> RateLimitMiddleware:
    """Return the RateLimitMiddleware instance attached to the app."""
    for middleware in app.user_middleware:
        if middleware.cls is RateLimitMiddleware:
            # Accessing the built middleware stack is tricky; instead we
            # reset via the app's middleware stack after it has been built.
            break
    # Walk the built ASGI stack to find our middleware instance.
    layer = app.middleware_stack
    while layer is not None:
        if isinstance(layer, RateLimitMiddleware):
            return layer
        layer = getattr(layer, "app", None)
    raise RuntimeError("RateLimitMiddleware not found in the middleware stack")


@pytest.fixture(autouse=True)
def reset_rate_limiter() -> None:
    """Reset per-IP bucket state before every test."""
    try:
        mw = _get_middleware()
        mw.reset()
    except RuntimeError:
        pass  # middleware stack not yet built — harmless
    yield
    try:
        mw = _get_middleware()
        mw.reset()
    except RuntimeError:
        pass


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, follow_redirects=False)


# ===========================================================================
# Unit tests — TokenBucket
# ===========================================================================


class TestTokenBucket:
    """Pure unit tests for TokenBucket with no I/O."""

    def test_bucket_starts_full(self) -> None:
        bucket = TokenBucket(capacity=10, refill_rate=1)
        # All 10 tokens should be available immediately.
        for _ in range(10):
            assert bucket.consume() is True

    def test_bucket_empty_returns_false(self) -> None:
        bucket = TokenBucket(capacity=3, refill_rate=1)
        for _ in range(3):
            bucket.consume()
        assert bucket.consume() is False

    def test_bucket_refills_over_time(self) -> None:
        # 1 token/second, start empty.
        bucket = TokenBucket(capacity=5, refill_rate=1)
        # Drain it.
        while bucket.consume():
            pass
        # Wait slightly more than 1 second — should have ~1 token.
        time.sleep(1.1)
        assert bucket.consume() is True

    def test_bucket_does_not_exceed_capacity(self) -> None:
        bucket = TokenBucket(capacity=5, refill_rate=100)
        # Even with a very high refill rate, tokens cap at capacity.
        time.sleep(0.2)
        assert bucket.tokens <= 5.0

    def test_bucket_tokens_property_is_non_negative(self) -> None:
        bucket = TokenBucket(capacity=3, refill_rate=1)
        for _ in range(10):
            bucket.consume()
        assert bucket.tokens >= 0.0

    def test_invalid_capacity_raises(self) -> None:
        with pytest.raises(ValueError, match="capacity"):
            TokenBucket(capacity=0, refill_rate=1)

    def test_invalid_refill_rate_raises(self) -> None:
        with pytest.raises(ValueError, match="refill_rate"):
            TokenBucket(capacity=10, refill_rate=0)

    def test_consume_multiple_tokens(self) -> None:
        bucket = TokenBucket(capacity=10, refill_rate=1)
        assert bucket.consume(tokens=5) is True
        assert bucket.consume(tokens=5) is True
        assert bucket.consume(tokens=1) is False


# ===========================================================================
# Integration tests — RateLimitMiddleware via FastAPI TestClient
# ===========================================================================


class TestRateLimitMiddleware:
    """Integration tests that fire real HTTP requests through the middleware."""

    # -----------------------------------------------------------------------
    # Basic enforcement
    # -----------------------------------------------------------------------

    def test_requests_within_limit_are_allowed(self, client: TestClient) -> None:
        """10 requests from the same IP should all succeed (well within 100)."""
        for _ in range(10):
            r = client.post("/shorten", json={"url": "https://example.com"})
            assert r.status_code == 201, f"Expected 201, got {r.status_code}"

    def test_request_over_limit_returns_429(self, client: TestClient) -> None:
        """After exhausting the bucket, the next request must return 429."""
        mw = _get_middleware()
        # Configure a tiny bucket directly so we don't have to make 100 calls.
        mw.reset()
        # Drain the default bucket for our test IP by poking it internally.
        ip = "testclient"  # TestClient uses "testclient" as host
        bucket = mw._get_or_create_bucket(ip)
        # Manually drain to zero.
        bucket._tokens = 0

        r = client.post("/shorten", json={"url": "https://example.com"})
        assert r.status_code == 429

    def test_429_response_has_detail_field(self, client: TestClient) -> None:
        """429 body must include a 'detail' key."""
        mw = _get_middleware()
        mw._get_or_create_bucket("testclient")._tokens = 0
        r = client.get("/stats/doesnotexist")
        assert r.status_code == 429
        assert "detail" in r.json()

    def test_429_response_has_retry_after_header(self, client: TestClient) -> None:
        """429 response must include a Retry-After header."""
        mw = _get_middleware()
        mw._get_or_create_bucket("testclient")._tokens = 0
        r = client.get("/stats/doesnotexist")
        assert r.status_code == 429
        assert "retry-after" in r.headers
        assert int(r.headers["retry-after"]) == int(WINDOW_SECONDS)

    # -----------------------------------------------------------------------
    # Per-IP isolation
    # -----------------------------------------------------------------------

    def test_different_ips_have_independent_buckets(self, client: TestClient) -> None:
        """Draining one IP's bucket must not affect another IP's bucket."""
        mw = _get_middleware()
        # Drain IP A.
        mw._get_or_create_bucket("1.2.3.4")._tokens = 0

        # IP B should still succeed.
        r = client.get(
            "/stats/doesnotexist",
            headers={"X-Forwarded-For": "9.9.9.9"},
        )
        # 404 means it got through the rate limiter — that's what we want.
        assert r.status_code == 404

    def test_x_forwarded_for_used_as_ip(self, client: TestClient) -> None:
        """The middleware should honour X-Forwarded-For for the bucket key."""
        mw = _get_middleware()
        forwarded_ip = "203.0.113.1"
        mw._get_or_create_bucket(forwarded_ip)._tokens = 0

        r = client.get(
            "/stats/any",
            headers={"X-Forwarded-For": forwarded_ip},
        )
        assert r.status_code == 429

    def test_x_forwarded_for_first_ip_used(self, client: TestClient) -> None:
        """When X-Forwarded-For has multiple IPs, only the first is used."""
        mw = _get_middleware()
        real_client_ip = "10.0.0.1"
        proxy_ip = "10.0.0.2"
        mw._get_or_create_bucket(real_client_ip)._tokens = 0

        # Header: "client, proxy"
        r = client.get(
            "/stats/any",
            headers={"X-Forwarded-For": f"{real_client_ip}, {proxy_ip}"},
        )
        assert r.status_code == 429

    # -----------------------------------------------------------------------
    # Refill / recovery
    # -----------------------------------------------------------------------

    def test_bucket_refills_and_allows_requests_again(
        self, client: TestClient
    ) -> None:
        """After a brief wait, a drained bucket should start accepting again."""
        # Use a tiny capacity + fast refill so we don't sleep long.
        mw = _get_middleware()
        ip = "testclient"
        # Replace the real bucket with a 1-token/second bucket.
        tiny_bucket = TokenBucket(capacity=1, refill_rate=1)
        tiny_bucket._tokens = 0  # start empty
        with mw._lock:
            mw._buckets[ip] = tiny_bucket

        # Should be denied now.
        r1 = client.post("/shorten", json={"url": "https://example.com"})
        assert r1.status_code == 429

        # After ~1 s the bucket should refill one token.
        time.sleep(1.1)
        r2 = client.post("/shorten", json={"url": "https://example.com"})
        assert r2.status_code == 201

    # -----------------------------------------------------------------------
    # Constants
    # -----------------------------------------------------------------------

    def test_default_rate_limit_is_100(self) -> None:
        assert RATE_LIMIT == 100

    def test_default_window_seconds_is_60(self) -> None:
        assert WINDOW_SECONDS == 60.0

    # -----------------------------------------------------------------------
    # Non-HTTP traffic passes through
    # -----------------------------------------------------------------------

    def test_middleware_reset_clears_buckets(self) -> None:
        """reset() should remove all stored buckets."""
        mw = _get_middleware()
        mw._get_or_create_bucket("1.1.1.1")
        mw._get_or_create_bucket("2.2.2.2")
        mw.reset()
        assert len(mw._buckets) == 0
