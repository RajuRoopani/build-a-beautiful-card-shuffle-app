"""Pydantic models for the URL Shortener API."""

from datetime import datetime
from pydantic import BaseModel, HttpUrl, field_validator


class ShortenRequest(BaseModel):
    """Request body for POST /shorten."""

    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure the URL is a valid HTTP/HTTPS URL.

        Pydantic v2's HttpUrl normalises the URL (e.g. adds a trailing slash),
        so we validate with HttpUrl but return the *original* stripped string
        to preserve the caller's exact input.
        """
        stripped = v.strip()
        if not stripped:
            raise ValueError("URL must not be empty")
        if not (stripped.startswith("http://") or stripped.startswith("https://")):
            raise ValueError("URL must start with http:// or https://")
        # Use pydantic's HttpUrl for deep structural validation
        try:
            HttpUrl(stripped)
        except Exception:
            raise ValueError(f"Invalid URL: {stripped!r}")
        return stripped


class ShortenResponse(BaseModel):
    """Response body for POST /shorten (201)."""

    short_code: str
    original_url: str
    short_url: str


class StatsResponse(BaseModel):
    """Response body for GET /stats/{short_code}."""

    short_code: str
    original_url: str
    created_at: datetime
    click_count: int
