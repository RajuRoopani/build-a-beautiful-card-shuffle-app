# Note-Taking REST API

A simple yet powerful REST API for managing notes, built with **FastAPI**. Create, read, update, and delete notes through standard HTTP endpoints.

## Project Description

This Note-Taking REST API provides a complete CRUD (Create, Read, Update, Delete) interface for managing notes. Each note has:
- A unique integer ID (auto-incremented)
- A title and content
- Creation and update timestamps

The API is built with **FastAPI** and uses **in-memory storage** for fast development and testing. Perfect for learning REST API design or as a foundation for more complex note-taking applications.

**Note:** All data is stored in memory and will be reset when the server restarts.

## Project Structure

```
note-taking-api/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application and endpoints
│   └── models.py         # Pydantic models and in-memory storage
├── tests/
│   ├── __init__.py
│   └── test_notes.py     # Comprehensive test suite
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- **fastapi** — Modern web framework for building APIs
- **uvicorn** — ASGI server for running FastAPI
- **pytest** — Testing framework
- **httpx** — HTTP client for testing

## Running the API

Start the development server with hot reload enabled:

```bash
uvicorn app.main:app --reload
```

The API will be available at **http://localhost:8000**

You can also view the interactive API documentation:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Running Tests

Run the complete test suite:

```bash
pytest tests/ -v
```

Run tests with coverage:

```bash
pytest tests/ -v --cov=app
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/notes` | Create a new note |
| GET | `/notes` | List all notes |
| GET | `/notes/{id}` | Get a single note by ID |
| PUT | `/notes/{id}` | Update a note |
| DELETE | `/notes/{id}` | Delete a note |

## Example API Usage

### 1. Create a Note

**Request:**
```bash
curl -X POST http://localhost:8000/notes \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Note",
    "content": "This is the content of my first note."
  }'
```

**Response:**
```json
{
  "id": 1,
  "title": "My First Note",
  "content": "This is the content of my first note.",
  "created_at": "2024-01-15T10:30:45.123456+00:00",
  "updated_at": "2024-01-15T10:30:45.123456+00:00"
}
```

### 2. List All Notes

**Request:**
```bash
curl -X GET http://localhost:8000/notes \
  -H "Content-Type: application/json"
```

**Response:**
```json
[
  {
    "id": 1,
    "title": "My First Note",
    "content": "This is the content of my first note.",
    "created_at": "2024-01-15T10:30:45.123456+00:00",
    "updated_at": "2024-01-15T10:30:45.123456+00:00"
  },
  {
    "id": 2,
    "title": "Shopping List",
    "content": "Milk, eggs, bread, cheese",
    "created_at": "2024-01-15T10:35:20.654321+00:00",
    "updated_at": "2024-01-15T10:35:20.654321+00:00"
  }
]
```

### 3. Get a Single Note

**Request:**
```bash
curl -X GET http://localhost:8000/notes/1 \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "id": 1,
  "title": "My First Note",
  "content": "This is the content of my first note.",
  "created_at": "2024-01-15T10:30:45.123456+00:00",
  "updated_at": "2024-01-15T10:30:45.123456+00:00"
}
```

### 4. Update a Note

**Request:**
```bash
curl -X PUT http://localhost:8000/notes/1 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Updated Note",
    "content": "This is the updated content."
  }'
```

**Response:**
```json
{
  "id": 1,
  "title": "My Updated Note",
  "content": "This is the updated content.",
  "created_at": "2024-01-15T10:30:45.123456+00:00",
  "updated_at": "2024-01-15T10:40:15.987654+00:00"
}
```

**Note:** You can update just the title or just the content by providing only one field:

```bash
curl -X PUT http://localhost:8000/notes/1 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New Title Only"
  }'
```

### 5. Delete a Note

**Request:**
```bash
curl -X DELETE http://localhost:8000/notes/1 \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "detail": "Note deleted"
}
```

## Request/Response Examples

### Creating a Note - Detailed Example

**Command:**
```bash
curl -X POST http://localhost:8000/notes \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Project Ideas",
    "content": "1. Build a todo app\n2. Create a blog\n3. Learn FastAPI"
  }'
```

**Formatted Request Body:**
```json
{
  "title": "Project Ideas",
  "content": "1. Build a todo app\n2. Create a blog\n3. Learn FastAPI"
}
```

**Response (201 Created):**
```json
{
  "id": 3,
  "title": "Project Ideas",
  "content": "1. Build a todo app\n2. Create a blog\n3. Learn FastAPI",
  "created_at": "2024-01-15T11:00:00.000000+00:00",
  "updated_at": "2024-01-15T11:00:00.000000+00:00"
}
```

### Error Handling

If you request a note that doesn't exist, you'll receive a 404 error:

**Request:**
```bash
curl -X GET http://localhost:8000/notes/999
```

**Response (404 Not Found):**
```json
{
  "detail": "Note not found"
}
```

## Important Notes

### In-Memory Storage
- Data is stored **in memory only** and **will be lost when the server restarts**
- This makes the API ideal for development, testing, and learning
- For production use, consider integrating a database like PostgreSQL or SQLite

### Auto-Increment IDs
- Note IDs are automatically generated as sequential integers
- The first note will have ID 1, the second ID 2, etc.
- IDs are never reused, even after deletion

### Timestamps
- All timestamps are in UTC timezone (timezone-aware)
- Timestamps are automatically managed by the API
- `created_at` never changes
- `updated_at` updates whenever the note is modified

## Development

### Code Organization
- `app/main.py` — FastAPI application with all endpoint handlers
- `app/models.py` — Pydantic request/response schemas and in-memory storage logic
- `tests/test_notes.py` — Comprehensive test suite using pytest and TestClient

### Testing with TestClient
The test suite uses FastAPI's `TestClient` to simulate HTTP requests:

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
response = client.post("/notes", json={"title": "Test", "content": "Content"})
assert response.status_code == 201
```

## Future Enhancements

Possible extensions to this API:
- Database integration (SQLite, PostgreSQL)
- User authentication and authorization
- Search and filtering capabilities
- Note categories or tags
- Rate limiting
- Pagination for listing notes
- Soft deletes (mark as deleted instead of removing)
