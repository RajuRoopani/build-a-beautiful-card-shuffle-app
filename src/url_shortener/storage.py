"""In-memory storage for the URL Shortener API.

Storage schema:
    {
        "<short_code>": {
            "original_url": str,
            "created_at": datetime,
            "click_count": int,
        }
    }

Scaling notes
-------------
- The module-level ``_store`` dict is the authoritative data store.
- ``_url_cache`` is an LRU cache (max 1 024 entries) for the redirect
  hot-path: looking up the original URL by short_code is the most frequent
  operation under load, so we cache it separately from the full record to
  avoid copying the mutable dict on every cache hit.
- ``increment_clicks`` writes through directly to ``_store``; the cache entry
  for a given code holds only the original URL, so click count correctness is
  unaffected.
"""

from collections import OrderedDict
from datetime import datetime, timezone
from typing import TypedDict


class UrlRecord(TypedDict):
    original_url: str
    created_at: datetime
    click_count: int


# ---------------------------------------------------------------------------
# Internal state
# ---------------------------------------------------------------------------

# Authoritative store: short_code → UrlRecord
_store: dict[str, UrlRecord] = {}

# LRU cache for the redirect hot-path: short_code → original_url
_LRU_CAPACITY: int = 1_024
_url_cache: "OrderedDict[str, str]" = OrderedDict()


# ---------------------------------------------------------------------------
# Cache helpers (private)
# ---------------------------------------------------------------------------

def _cache_get(short_code: str) -> str | None:
    """Return the cached original URL for *short_code*, or None on miss.

    Moves the entry to the end (most-recently-used position) on hit.
    """
    if short_code not in _url_cache:
        return None
    _url_cache.move_to_end(short_code)
    return _url_cache[short_code]


def _cache_put(short_code: str, original_url: str) -> None:
    """Insert or refresh *short_code* → *original_url* in the LRU cache.

    Evicts the least-recently-used entry when capacity is exceeded.
    """
    if short_code in _url_cache:
        _url_cache.move_to_end(short_code)
    _url_cache[short_code] = original_url
    if len(_url_cache) > _LRU_CAPACITY:
        _url_cache.popitem(last=False)  # drop LRU entry


def _cache_invalidate(short_code: str) -> None:
    """Remove *short_code* from the cache if present."""
    _url_cache.pop(short_code, None)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

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
    _cache_put(short_code, original_url)
    return record


def get_url(short_code: str) -> UrlRecord | None:
    """Retrieve a URL record by short_code.

    Args:
        short_code: The short code to look up.

    Returns:
        The UrlRecord if found, else None.
    """
    return _store.get(short_code)


def get_original_url_cached(short_code: str) -> str | None:
    """Return the original URL for *short_code*, using the LRU cache.

    This is the hot-path helper used by the redirect endpoint.  It avoids
    a full ``_store`` dict lookup for frequently-accessed codes.

    Args:
        short_code: The short code to look up.

    Returns:
        The original URL string if found, else None.
    """
    cached = _cache_get(short_code)
    if cached is not None:
        return cached
    record = _store.get(short_code)
    if record is None:
        return None
    _cache_put(short_code, record["original_url"])
    return record["original_url"]


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
    """Remove all entries from the store and cache. Intended for use in tests."""
    _store.clear()
    _url_cache.clear()


def all_codes() -> list[str]:
    """Return all short codes currently stored. Intended for use in tests."""
    return list(_store.keys())
