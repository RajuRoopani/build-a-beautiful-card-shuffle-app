"""Token-bucket rate limiter for the URL Shortener API.

Algorithm
---------
Each IP address gets its own bucket with a capacity of RATE_LIMIT tokens.
Tokens are replenished continuously at a rate of RATE_LIMIT tokens per
WINDOW_SECONDS.  Every incoming request consumes one token.  When a bucket
is empty the middleware returns 429 Too Many Requests immediately, before
the request reaches any route handler.

Thread-safety
-------------
The bucket store is a plain dict protected by a threading.Lock so the
module is safe to use with multi-threaded ASGI servers (e.g. uvicorn with
multiple workers sharing memory would still need Redis — but for a single
process this is correct).

Configuration
-------------
RATE_LIMIT      — maximum tokens (= max burst) and sustained req/window.
WINDOW_SECONDS  — refill window in seconds.
"""

from __future__ import annotations

import threading
import time
from typing import Callable

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

# ---------------------------------------------------------------------------
# Constants — 100 requests per 60-second window, per IP.
# ---------------------------------------------------------------------------
RATE_LIMIT: int = 100          # tokens == max requests per window
WINDOW_SECONDS: float = 60.0   # refill window length in seconds


class TokenBucket:
    """A single per-IP token bucket.

    Tokens are added continuously (lazy evaluation on each call to
    ``consume``).  The bucket never exceeds *capacity* tokens.

    Args:
        capacity:       Maximum number of tokens (also the initial fill level).
        refill_rate:    Tokens added per second.
    """

    def __init__(self, capacity: float, refill_rate: float) -> None:
        if capacity <= 0:
            raise ValueError(f"capacity must be > 0, got {capacity}")
        if refill_rate <= 0:
            raise ValueError(f"refill_rate must be > 0, got {refill_rate}")

        self._capacity: float = capacity
        self._refill_rate: float = refill_rate  # tokens / second
        self._tokens: float = float(capacity)   # start full
        self._last_refill: float = time.monotonic()
        self._lock: threading.Lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def consume(self, tokens: float = 1.0) -> bool:
        """Attempt to consume *tokens* from the bucket.

        Refills the bucket based on elapsed time before checking availability.

        Args:
            tokens: Number of tokens to consume (default 1).

        Returns:
            True  — request allowed (tokens were available).
            False — request denied (bucket was empty).
        """
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    @property
    def tokens(self) -> float:
        """Current token count (read-only snapshot, approximate)."""
        with self._lock:
            self._refill()
            return self._tokens

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _refill(self) -> None:
        """Add tokens proportional to elapsed time since the last refill.

        Must be called while holding ``self._lock``.
        """
        now = time.monotonic()
        elapsed = now - self._last_refill
        added = elapsed * self._refill_rate
        self._tokens = min(self._capacity, self._tokens + added)
        self._last_refill = now


class RateLimitMiddleware:
    """ASGI middleware that enforces per-IP token-bucket rate limiting.

    Attaches one :class:`TokenBucket` per unique client IP.  Buckets are
    created lazily on first request and live for the lifetime of the process.

    Requests that exceed the limit receive a **429 Too Many Requests**
    response with a ``Retry-After`` header set to *WINDOW_SECONDS*.

    Args:
        app:            The wrapped ASGI application.
        rate_limit:     Max requests per *window_seconds* (default 100).
        window_seconds: Window length in seconds (default 60).
    """

    def __init__(
        self,
        app: ASGIApp,
        rate_limit: int = RATE_LIMIT,
        window_seconds: float = WINDOW_SECONDS,
    ) -> None:
        self._app = app
        self._rate_limit = rate_limit
        self._window_seconds = window_seconds
        # tokens / second for each bucket
        self._refill_rate: float = rate_limit / window_seconds
        self._buckets: dict[str, TokenBucket] = {}
        self._lock: threading.Lock = threading.Lock()

    # ------------------------------------------------------------------
    # ASGI interface
    # ------------------------------------------------------------------

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            # Pass through WebSocket / lifespan events unchanged.
            await self._app(scope, receive, send)
            return

        request = Request(scope)
        client_ip = self._get_client_ip(request)
        bucket = self._get_or_create_bucket(client_ip)

        if not bucket.consume():
            response = self._rate_limit_response()
            await response(scope, receive, send)
            return

        await self._app(scope, receive, send)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_client_ip(self, request: Request) -> str:
        """Extract the real client IP from the request.

        Checks the ``X-Forwarded-For`` header first (for reverse-proxy
        deployments), then falls back to the direct connection address.

        Args:
            request: The incoming Starlette Request.

        Returns:
            IP address string, or ``"unknown"`` if none is found.
        """
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For may be "client, proxy1, proxy2" — take the first.
            return forwarded_for.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def _get_or_create_bucket(self, ip: str) -> TokenBucket:
        """Return the existing bucket for *ip*, creating it if needed.

        Args:
            ip: Client IP address string.

        Returns:
            The :class:`TokenBucket` for this IP.
        """
        with self._lock:
            if ip not in self._buckets:
                self._buckets[ip] = TokenBucket(
                    capacity=self._rate_limit,
                    refill_rate=self._refill_rate,
                )
            return self._buckets[ip]

    def _rate_limit_response(self) -> JSONResponse:
        """Build a 429 JSON response with a ``Retry-After`` header.

        Returns:
            A :class:`JSONResponse` with status 429.
        """
        retry_after = int(self._window_seconds)
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Try again later."},
            headers={"Retry-After": str(retry_after)},
        )

    # ------------------------------------------------------------------
    # Testing helpers
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Clear all bucket state.  **For use in tests only.**"""
        with self._lock:
            self._buckets.clear()
