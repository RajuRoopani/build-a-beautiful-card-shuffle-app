"""In-memory storage module for URL mappings."""

import random
import string
from datetime import datetime, timedelta, timezone
from typing import Optional


# Characters used for Base62 short code generation (alphanumeric, URL-safe)
_BASE62_ALPHABET: str = string.ascii_letters + string.digits  # 62 chars
_SHORT_CODE_LENGTH: int = 8
_RETENTION_DAYS: int = 30


class URLStorage:
    """Thread-local in-memory store for short URL mappings.

    Each entry stored under a short code has the shape:
        {
            "short_code": str,
            "long_url":   str,
            "created_at": datetime (UTC, timezone-aware),
            "expires_at": datetime (UTC, timezone-aware),
        }
    """

    def __init__(self) -> None:
        """Initialise an empty URL mapping store."""
        self._store: dict[str, dict] = {}

    def _generate_short_code(self) -> str:
        """Generate a unique 8-character alphanumeric short code.

        Uses Base62 alphabet (a-z, A-Z, 0-9).  Regenerates if there is a
        collision with an existing (non-expired) entry — collisions are
        astronomically rare for 8 chars across 62^8 ≈ 218 trillion possibilities.

        Returns:
            A unique 8-character string.
        """
        while True:
            code = "".join(random.choices(_BASE62_ALPHABET, k=_SHORT_CODE_LENGTH))
            if code not in self._store:
                return code

    def create(self, long_url: str) -> dict:
        """Store a new short-code → long URL mapping and return the entry.

        A fresh short code is generated for every call, even if the same
        ``long_url`` was already stored previously (no deduplication).

        Args:
            long_url: The original URL to be shortened.

        Returns:
            A dict with keys ``short_code``, ``long_url``, ``created_at``,
            and ``expires_at`` (all datetimes are UTC-aware).
        """
        now: datetime = datetime.now(tz=timezone.utc)
        expires: datetime = now + timedelta(days=_RETENTION_DAYS)
        code: str = self._generate_short_code()

        entry: dict = {
            "short_code": code,
            "long_url": long_url,
            "created_at": now,
            "expires_at": expires,
        }
        self._store[code] = entry
        return entry

    def get(self, short_code: str) -> Optional[dict]:
        """Retrieve a mapping entry by its short code.

        Args:
            short_code: The 8-character code to look up.

        Returns:
            The entry dict if found, or ``None`` if the code is unknown.
        """
        return self._store.get(short_code)

    def is_expired(self, entry: dict) -> bool:
        """Check whether a mapping entry has passed its expiry date.

        Args:
            entry: A mapping dict previously returned by :meth:`create`.

        Returns:
            ``True`` if the entry's ``expires_at`` timestamp is in the past,
            ``False`` otherwise.
        """
        now: datetime = datetime.now(tz=timezone.utc)
        return entry["expires_at"] < now


# Module-level singleton — import this everywhere instead of instantiating directly.
url_storage: URLStorage = URLStorage()
