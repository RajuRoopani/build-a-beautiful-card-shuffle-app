"""Pydantic models for URL Shortener request/response schemas."""

from pydantic import BaseModel, field_validator, AnyHttpUrl
from typing import Annotated


class ShortenRequest(BaseModel):
    """Request model for shortening a URL.

    Attributes:
        url: The long URL to shorten. Must be a non-empty, valid HTTP(S) URL.
    """

    url: str

    @field_validator("url")
    @classmethod
    def url_must_be_valid(cls, v: str) -> str:
        """Validate that the URL is non-empty and well-formed."""
        v = v.strip()
        if not v:
            raise ValueError("URL must not be empty")
        # Require http:// or https:// scheme
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL must start with http:// or https://")
        # Basic sanity check: must have something after the scheme
        parts = v.split("//", 1)
        if len(parts) < 2 or not parts[1]:
            raise ValueError("URL is not valid")
        return v


class ShortenResponse(BaseModel):
    """Response model returned after successfully shortening a URL.

    Attributes:
        short_url: The 8-character alphanumeric short code.
        long_url:  The original long URL.
        expires_at: ISO 8601 datetime string indicating when the mapping expires.
    """

    short_url: str
    long_url: str
    expires_at: str


class ErrorResponse(BaseModel):
    """Generic error response model.

    Attributes:
        detail: Human-readable description of the error.
    """

    detail: str
