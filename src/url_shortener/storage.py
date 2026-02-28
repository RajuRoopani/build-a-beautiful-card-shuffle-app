"""In-memory storage for the URL Shortener API.

Storage schema:
    {
        "<short_code>": {
            "original_url": str,
            "created_at": datetime,
            "click_count": int,
        }
    }
"""

from datetime import datetime, timezone
from typing import TypedDict


class UrlRecord(TypedDict):
    original_url: str
    created_at: datetime
    click_count: int


# Module-level in-memory store.
_store: dict[str, UrlRecord] = {}


def save_url(short_code: str, original_url: str) -> UrlRecord:
    """Persist a new short_code → URL mapping.

    Args:
        short_code: The generated short code.
        original_url: The original URL to map to.

    Returns:
        The newly created UrlRecord.

    Raises:
        ValueError: If short_code already exists in the store.
    """
    if short_code in _store:
        raise ValueError(f"Short code {short_code!r} already exists")

    record: UrlRecord = {
        "original_url": original_url,
        "created_at": datetime.now(tz=timezone.utc),
        "click_count": 0,
    }
    _store[short_code] = record
    return record


def get_url(short_code: str) -> UrlRecord | None:
    """Retrieve a URL record by short_code.

    Args:
        short_code: The short code to look up.

    Returns:
        The UrlRecord if found, else None.
    """
    return _store.get(short_code)


def increment_clicks(short_code: str) -> None:
    """Increment the click count for a given short_code.

    Args:
        short_code: The short code whose click count should be incremented.

    Raises:
        KeyError: If the short_code does not exist in the store.
    """
    if short_code not in _store:
        raise KeyError(f"Short code {short_code!r} not found")
    _store[short_code]["click_count"] += 1


def clear_store() -> None:
    """Remove all entries from the store. Intended for use in tests."""
    _store.clear()


def all_codes() -> list[str]:
    """Return all short codes currently stored. Intended for use in tests."""
    return list(_store.keys())
