"""FastAPI application entry point for the URL Shortener service."""

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse

from url_shortener.models import ShortenRequest, ShortenResponse, ErrorResponse
from url_shortener.storage import url_storage

app = FastAPI(
    title="URL Shortener",
    description="Shorten long URLs into 8-character codes with a 30-day TTL.",
    version="1.0.0",
)


@app.post(
    "/shorten",
    status_code=201,
    response_model=ShortenResponse,
    responses={400: {"model": ErrorResponse}},
    summary="Shorten a long URL",
)
def shorten_url(request: ShortenRequest) -> ShortenResponse:
    """Accept a long URL and return a shortened version with an expiry date.

    Args:
        request: A JSON body containing the ``url`` field.

    Returns:
        A :class:`ShortenResponse` with ``short_url``, ``long_url``, and
        ``expires_at`` (ISO 8601).

    Raises:
        HTTPException 400: If the URL is empty or invalid (enforced by the
            Pydantic model validator before this handler is reached).
    """
    entry = url_storage.create(request.url)
    return ShortenResponse(
        short_url=entry["short_code"],
        long_url=entry["long_url"],
        expires_at=entry["expires_at"].isoformat(),
    )


@app.get(
    "/{short_code}",
    responses={
        307: {"description": "Redirect to the original URL"},
        404: {"model": ErrorResponse},
        410: {"model": ErrorResponse},
    },
    summary="Redirect to the original URL",
)
def redirect_to_url(short_code: str) -> RedirectResponse:
    """Look up a short code and redirect to the corresponding long URL.

    Args:
        short_code: The 8-character code embedded in the path.

    Returns:
        A 307 Temporary Redirect response with a ``Location`` header pointing
        to the original long URL.

    Raises:
        HTTPException 404: If the short code is not found in the store.
        HTTPException 410: If the short code exists but has expired.
    """
    entry = url_storage.get(short_code)

    if entry is None:
        raise HTTPException(status_code=404, detail="Short URL not found")

    if url_storage.is_expired(entry):
        raise HTTPException(status_code=410, detail="Short URL has expired")

    return RedirectResponse(url=entry["long_url"], status_code=307)


# ── Validation error handler ──────────────────────────────────────────────────
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """Return a 400 response (instead of FastAPI's default 422) for invalid input."""
    errors = exc.errors()
    detail = errors[0]["msg"] if errors else "Invalid request"
    return JSONResponse(status_code=400, content={"detail": detail})
