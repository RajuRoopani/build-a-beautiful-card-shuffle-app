"""Note-Taking REST API built with FastAPI.

Provides CRUD endpoints for managing notes stored in-memory.
Notes have a title, content, and auto-managed timestamps.
"""

from datetime import datetime, timezone
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app.models import (
    NoteCreate,
    NoteUpdate,
    NoteResponse,
    notes_db,
    next_id,
)

app = FastAPI(
    title="Note-Taking API",
    description="A simple REST API for managing notes",
    version="1.0.0",
)


@app.post("/notes", response_model=NoteResponse, status_code=201)
def create_note(note: NoteCreate) -> NoteResponse:
    """Create a new note.

    Accepts a JSON body with title and content, generates a unique ID
    and timestamps, stores the note in memory, and returns it.
    """
    now = datetime.now(timezone.utc)
    note_id = next_id()
    note_data = {
        "id": note_id,
        "title": note.title,
        "content": note.content,
        "created_at": now,
        "updated_at": now,
    }
    notes_db[note_id] = note_data
    return NoteResponse(**note_data)


@app.get("/notes", response_model=List[NoteResponse])
def list_notes() -> List[NoteResponse]:
    """Return a list of all notes.

    Returns an empty list if no notes exist.
    """
    return [NoteResponse(**note) for note in notes_db.values()]


@app.get("/notes/{note_id}", response_model=NoteResponse)
def get_note(note_id: int) -> NoteResponse:
    """Retrieve a single note by its ID.

    Returns HTTP 404 if the note does not exist.
    """
    if note_id not in notes_db:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteResponse(**notes_db[note_id])


@app.put("/notes/{note_id}", response_model=NoteResponse)
def update_note(note_id: int, note: NoteUpdate) -> NoteResponse:
    """Update an existing note.

    Accepts optional title and/or content fields. Updates the
    updated_at timestamp. Returns HTTP 404 if the note does not exist.
    """
    if note_id not in notes_db:
        raise HTTPException(status_code=404, detail="Note not found")
    existing = notes_db[note_id]
    if note.title is not None:
        existing["title"] = note.title
    if note.content is not None:
        existing["content"] = note.content
    existing["updated_at"] = datetime.now(timezone.utc)
    return NoteResponse(**existing)


@app.delete("/notes/{note_id}")
def delete_note(note_id: int) -> JSONResponse:
    """Delete a note by its ID.

    Returns HTTP 200 on success. Returns HTTP 404 if the note does not exist.
    """
    if note_id not in notes_db:
        raise HTTPException(status_code=404, detail="Note not found")
    del notes_db[note_id]
    return JSONResponse(status_code=200, content={"detail": "Note deleted"})
