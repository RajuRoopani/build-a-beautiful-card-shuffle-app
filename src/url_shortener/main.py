"""FastAPI application for the URL Shortener API.

Endpoints:
    POST /shorten           — Create a short URL
    GET  /{short_code}      — Redirect to original URL (301)
    GET  /stats/{short_code} — Return click statistics
"""

import random
import string

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse

from src.url_shortener.models import ShortenRequest, ShortenResponse, StatsResponse
from src.url_shortener import storage

app = FastAPI(
    title="URL Shortener API",
    description="A production-grade URL Shortener with click statistics.",
    version="1.0.0",
)

_SHORT_CODE_LENGTH: int = 7
_ALPHABET: str = string.ascii_letters + string.digits


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors from Pydantic.

    If the error is in the 'url' field AND the field exists but is invalid
    (type != 'missing'), return 400 (Bad Request).
    Otherwise, return 422 (Unprocessable Entity).
    """
    for error in exc.errors():
        if "url" in error.get("loc", []) and error.get("type") != "missing":
            return JSONResponse(status_code=400, content={"detail": "Invalid URL"})
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


def _generate_short_code() -> str:
    """Generate a unique 7-character alphanumeric short code.

    Retries until a code that is not already stored is produced.
    The probability of collision is astronomically low for reasonable
    store sizes (62^7 ≈ 3.5 billion combinations).

    Returns:
        A unique short code string.
    """
    while True:
        code = "".join(random.choices(_ALPHABET, k=_SHORT_CODE_LENGTH))
        if storage.get_url(code) is None:
            return code


def _build_short_url(request: Request, short_code: str) -> str:
    """Construct the full short URL from the incoming request base URL.

    Args:
        request: The current FastAPI Request object.
        short_code: The short code to append.

    Returns:
        Full short URL string, e.g. "http://localhost:8000/abc1234".
    """
    base_url = str(request.base_url).rstrip("/")
    return f"{base_url}/{short_code}"


@app.post(
    "/shorten",
    response_model=ShortenResponse,
    status_code=201,
    summary="Shorten a URL",
    responses={
        201: {"description": "Short URL created successfully"},
        400: {"description": "Invalid or missing URL"},
    },
)
def shorten_url(body: ShortenRequest, request: Request) -> ShortenResponse:
    """Accept a long URL and return a shortened version.

    Args:
        body: Request body containing the URL to shorten.
        request: FastAPI Request (used to build the short_url).

    Returns:
        ShortenResponse with the short_code, original_url, and short_url.

    Raises:
        HTTPException 400: If the URL fails validation.
    """
    # Pydantic validation runs on body instantiation; if we reach here the
    # URL is already validated. Wrap just in case of edge cases.
    try:
        original_url: str = str(body.url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    short_code = _generate_short_code()
    storage.save_url(short_code, original_url)
    short_url = _build_short_url(request, short_code)

    return ShortenResponse(
        short_code=short_code,
        original_url=original_url,
        short_url=short_url,
    )


@app.get(
    "/stats/{short_code}",
    response_model=StatsResponse,
    summary="Get click statistics for a short URL",
    responses={
        200: {"description": "Statistics returned successfully"},
        404: {"description": "Short code not found"},
    },
)
def get_stats(short_code: str) -> StatsResponse:
    """Return click statistics for a given short code.

    This endpoint is declared *before* the wildcard /{short_code} route so
    that FastAPI matches /stats/{short_code} first and does not treat "stats"
    as a redirect target.

    Args:
        short_code: The short code to look up.

    Returns:
        StatsResponse with click count and creation timestamp.

    Raises:
        HTTPException 404: If the short code is not found.
    """
    record = storage.get_url(short_code)
    if record is None:
        raise HTTPException(status_code=404, detail="Short code not found")

    return StatsResponse(
        short_code=short_code,
        original_url=record["original_url"],
        created_at=record["created_at"],
        click_count=record["click_count"],
    )


@app.get(
    "/{short_code}",
    summary="Redirect to the original URL",
    response_class=RedirectResponse,
    responses={
        301: {"description": "Redirect to original URL"},
        404: {"description": "Short code not found"},
    },
)
def redirect_to_url(short_code: str) -> RedirectResponse:
    """Look up a short code and issue a 301 redirect to the original URL.

    Also increments the click count for the short code.

    Args:
        short_code: The short code to resolve.

    Returns:
        A 301 RedirectResponse pointing to the original URL.

    Raises:
        HTTPException 404: If the short code is not found.
    """
    record = storage.get_url(short_code)
    if record is None:
        raise HTTPException(status_code=404, detail="Short code not found")

    storage.increment_clicks(short_code)
    return RedirectResponse(url=record["original_url"], status_code=301)
