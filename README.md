# URL Shortener API

A production-grade URL shortener REST API built with FastAPI. This service allows you to shorten long URLs into compact short codes, redirect users via those short codes, and track click statistics for analytics.

## Features

- **Shorten URLs** — Convert long URLs into compact, memorable short codes (6-8 alphanumeric characters)
- **Redirect via Short Codes** — Fast 301 redirects that preserve referrer and cache behavior
- **Click Statistics Tracking** — Monitor the number of times each shortened URL has been accessed
- **Input Validation** — Comprehensive validation for URL format, length, and uniqueness

## Tech Stack

- **Python** 3.11+
- **FastAPI** — Modern, fast web framework for building REST APIs
- **Uvicorn** — Lightning-fast ASGI server
- **Pytest** — Comprehensive testing framework with fixtures and parametrization

## Project Structure

```
src/
  url_shortener/
    __init__.py           # Package initialization
    main.py               # FastAPI app instance and route definitions
    models.py             # Pydantic schemas for request/response
    storage.py            # In-memory storage backend
tests/
  __init__.py
  test_url_shortener.py   # Comprehensive test suite (happy path + error cases)
requirements.txt          # Python dependencies
README.md                 # This file
```

## Getting Started

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/RajuRoopani/url-shortener-api.git
   cd url-shortener-api
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server:**
   ```bash
   uvicorn src.url_shortener.main:app --reload
   ```

   The API will be available at `http://localhost:8000`

4. **View interactive API docs:**
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### 1. Shorten a URL

**Endpoint:** `POST /shorten`

**Description:** Convert a long URL into a short, memorable code.

**Request:**
```json
{
  "original_url": "https://www.example.com/very/long/url/that/nobody/wants/to/share"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://www.example.com/very/long/url"}'
```

**Success Response (201 Created):**
```json
{
  "short_code": "a7b2c9",
  "original_url": "https://www.example.com/very/long/url",
  "short_url": "http://localhost:8000/a7b2c9",
  "created_at": "2024-01-15T10:30:45.123456"
}
```

**Error Response (400 Bad Request):**
```json
{
  "detail": "Invalid URL format or URL already shortened"
}
```

---

### 2. Redirect to Original URL

**Endpoint:** `GET /{short_code}`

**Description:** Redirect to the original URL and increment click counter.

**cURL Example:**
```bash
curl -i http://localhost:8000/a7b2c9
```

**Success Response (301 Moved Permanently):**
```
HTTP/1.1 301 Moved Permanently
Location: https://www.example.com/very/long/url
Cache-Control: public, max-age=86400
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Short code 'invalid' not found"
}
```

---

### 3. Get Click Statistics

**Endpoint:** `GET /stats/{short_code}`

**Description:** Retrieve click count and metadata for a shortened URL.

**cURL Example:**
```bash
curl http://localhost:8000/stats/a7b2c9
```

**Success Response (200 OK):**
```json
{
  "short_code": "a7b2c9",
  "original_url": "https://www.example.com/very/long/url",
  "click_count": 42,
  "created_at": "2024-01-15T10:30:45.123456",
  "last_accessed": "2024-01-15T11:15:30.654321"
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Short code 'invalid' not found"
}
```

## Running Tests

Run the full test suite with pytest:

```bash
pytest tests/ -v
```

**Output Example:**
```
tests/test_url_shortener.py::test_shorten_valid_url PASSED
tests/test_url_shortener.py::test_shorten_invalid_url FAILED
tests/test_url_shortener.py::test_redirect_existing_code PASSED
tests/test_url_shortener.py::test_redirect_nonexistent_code PASSED
tests/test_url_shortener.py::test_stats_increments_click_count PASSED
...
```

**Run specific test file:**
```bash
pytest tests/test_url_shortener.py -v
```

**Run with coverage report:**
```bash
pytest tests/ --cov=src.url_shortener --cov-report=html
```

## Design Decisions

### In-Memory Storage

- **Choice:** Dictionary-based in-memory storage
- **Rationale:** Suitable for MVP and prototyping; no database setup required; fast read/write performance
- **Trade-off:** Data is lost on server restart; not suitable for production with persistence requirements
- **Future:** Can be upgraded to Redis or PostgreSQL without changing API contracts

### Short Code Generation

- **Format:** Random alphanumeric strings (6-8 characters)
- **Character Set:** `[a-z0-9]` (lowercase letters + digits)
- **Algorithm:** Random selection from character pool with collision detection
- **Collision Handling:** Retry with longer code if collision detected (extremely rare)
- **Why not sequential:** Random codes are shorter for equivalent uniqueness and harder to enumerate

### 301 vs 302 Redirects

- **Choice:** 301 (Moved Permanently)
- **Rationale:** SEO-friendly; browsers cache result; appropriate for permanent shortened URLs
- **Alternatives:** 302 (Found) for temporary redirects if needed in future

### Click Tracking

- **Implementation:** Counter incremented on each redirect request
- **Scope:** Each short code has independent click count
- **Accuracy:** Not guaranteed in concurrent scenarios (for strict accuracy, use database with atomic operations)

## Error Handling

The API returns standard HTTP status codes:

- **200 OK** — Request successful (GET /stats)
- **201 Created** — URL successfully shortened (POST /shorten)
- **301 Moved Permanently** — Redirect to original URL (GET /{short_code})
- **400 Bad Request** — Invalid input (malformed URL, already shortened)
- **404 Not Found** — Short code doesn't exist
- **500 Internal Server Error** — Unexpected server error

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Write tests for new functionality
3. Ensure all tests pass: `pytest tests/ -v`
4. Commit and push: `git push origin feature/your-feature`
5. Open a pull request

## License

MIT License — see LICENSE file for details

## Support

For issues, questions, or suggestions, please open an issue on GitHub:
https://github.com/RajuRoopani/url-shortener-api/issues
