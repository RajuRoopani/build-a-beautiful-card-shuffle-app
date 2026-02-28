"""Pydantic models for the Note-Taking REST API.

Defines request and response schemas for note CRUD operations,
as well as the in-memory storage mechanism.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    """Schema for creating a new note."""

    title: str = Field(..., min_length=1, description="The title of the note")
    content: str = Field(..., min_length=1, description="The content of the note")


class NoteUpdate(BaseModel):
    """Schema for updating an existing note."""

    title: Optional[str] = Field(None, min_length=1, description="Updated title")
    content: Optional[str] = Field(None, min_length=1, description="Updated content")


class NoteResponse(BaseModel):
    """Schema for note responses returned by the API."""

    id: int = Field(..., description="Unique identifier for the note")
    title: str = Field(..., description="The title of the note")
    content: str = Field(..., description="The content of the note")
    created_at: datetime = Field(..., description="Timestamp when the note was created")
    updated_at: datetime = Field(..., description="Timestamp when the note was last updated")


# ---------------------------------------------------------------------------
# In-memory storage
# ---------------------------------------------------------------------------

notes_db: dict[int, dict] = {}
id_counter: int = 0


def reset_storage() -> None:
    """Reset the in-memory storage. Useful for testing."""
    global notes_db, id_counter
    notes_db.clear()
    id_counter = 0


def next_id() -> int:
    """Return the next auto-incremented note ID."""
    global id_counter
    id_counter += 1
    return id_counter
