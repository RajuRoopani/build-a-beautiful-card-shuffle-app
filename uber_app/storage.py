"""
In-memory data store.

Each dict maps ID (str) → dict representation of the entity.
These are module-level singletons shared across all imports.
"""

riders: dict = {}
drivers: dict = {}
rides: dict = {}


def clear_all() -> None:
    """Clear all in-memory storage (used between tests)."""
    riders.clear()
    drivers.clear()
    rides.clear()
