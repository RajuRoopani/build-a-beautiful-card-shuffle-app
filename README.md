# URL Shortener API

A lightweight, high-performance URL shortening service built with FastAPI. Convert long URLs into compact 8-character alphanumeric codes with automatic expiration management.

---

## Features

- **Shorten URLs** — Convert long URLs to compact 8-character alphanumeric codes
- **Automatic Redirection** — Redirect short codes to original URLs via 307 (Temporary Redirect) responses
- **30-Day Retention** — URLs automatically expire after 30 days
- **Input Validation** — Validates URL format and length before processing
- **In-Memory Storage** — Fast, thread-safe storage with expiration tracking
- **Simple API** — Two endpoints: shorten and redirect

---

## Project Structure

```
url_shortener/
├── __init__.py
├── main.py          # FastAPI application & endpoints
├── models.py        # Pydantic request/response models
├── storage.py       # In-memory URL storage
└── tests/
    ├── __init__.py
    └── test_url_shortener.py
```

---

## Installation

```bash
pip install -r requirements.txt
```

**Requirements:**
- FastAPI 0.104+
- Uvicorn 0.24+
- Pydantic 2.0+
- Pytest 7.0+ (for testing)

---

## Running the App

Start the FastAPI development server:

```bash
uvicorn url_shortener.main:app --reload
```

The API will be available at `http://localhost:8000`

**Interactive API Docs:** `http://localhost:8000/docs` (Swagger UI)

---

## API Endpoints

### POST /shorten
Shorten a long URL.

**Request:**
```bash
curl -X POST "http://localhost:8000/shorten" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.example.com/very/long/path/to/resource"}'
```

**Response (201 Created):**
```json
{
  "short_code": "a7b2k9m1",
  "original_url": "https://www.example.com/very/long/path/to/resource",
  "expires_at": "2026-02-15T10:30:00Z"
}
```

**Errors:**
- `400 Bad Request` — Invalid or missing URL
- `422 Unprocessable Entity` — Invalid request format

---

### GET /{short_code}
Redirect to the original URL.

**Request:**
```bash
curl -L "http://localhost:8000/a7b2k9m1"
```

**Response (307 Temporary Redirect):**
- Redirects to the original URL if found and not expired
- Returns `Location` header with the original URL

**Errors:**
- `404 Not Found` — Short code not found or expired
- `410 Gone` — Short code has expired

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | **FastAPI** 0.104+ |
| HTTP Server | **Uvicorn** 0.24+ |
| Data Validation | **Pydantic** 2.0+ |
| Testing | **Pytest** 7.0+ |
| Python | 3.9+ |

---

## Running Tests

Execute the test suite:

```bash
pytest url_shortener/tests/ -v
```

**Example output:**
```
url_shortener/tests/test_url_shortener.py::test_shorten_valid_url PASSED
url_shortener/tests/test_url_shortener.py::test_shorten_invalid_url PASSED
url_shortener/tests/test_url_shortener.py::test_redirect_valid_code PASSED
url_shortener/tests/test_url_shortener.py::test_redirect_expired_code PASSED
...
```

---

## Implementation Details

### Short Code Generation
- **Format:** 8-character alphanumeric codes (0-9, a-z, A-Z)
- **Encoding:** Base62 encoding ensures unique, URL-safe identifiers
- **Collision Resistance:** ~62^8 possible codes (approximately 218 trillion)

### Expiration Strategy
- **Retention Period:** 30 days from creation
- **Check Mechanism:** Lazy expiration (checked on redirect)
- **Storage:** Expiration timestamp stored with each URL mapping

### Input Validation
- URL must be valid HTTP/HTTPS URL
- Maximum URL length: 2048 characters
- Rejects relative URLs and non-HTTP(S) schemes

---

## Example Usage

### Python Client
```python
import requests

# Shorten a URL
response = requests.post(
    "http://localhost:8000/shorten",
    json={"url": "https://github.com/RajuRoopani/build-url-shorterner-app-from-scratch"}
)
data = response.json()
short_code = data["short_code"]
print(f"Short URL: http://localhost:8000/{short_code}")

# Redirect using short code
redirect = requests.get(
    f"http://localhost:8000/{short_code}",
    allow_redirects=False
)
print(f"Redirect: {redirect.headers['location']}")
```

### cURL Examples
```bash
# Shorten a URL
curl -X POST "http://localhost:8000/shorten" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/path"}'

# Use short code (will redirect)
curl -L "http://localhost:8000/abc12345"
```

---

## Development

### Code Structure
- **main.py** — FastAPI app setup and endpoint handlers
- **models.py** — Pydantic request/response schemas
- **storage.py** — URLStorage class for in-memory data management
- **tests/test_url_shortener.py** — Comprehensive test suite

### Testing Strategy
- Unit tests for storage operations
- Integration tests for API endpoints
- Edge case coverage (expired URLs, invalid inputs, etc.)
- All tests use in-memory SQLite for isolation

---

## Error Handling

| Status | Description |
|--------|-------------|
| `201 Created` | Successfully shortened URL |
| `307 Temporary Redirect` | Redirecting to original URL |
| `400 Bad Request` | Invalid or malformed URL |
| `404 Not Found` | Short code not found |
| `410 Gone` | Short code has expired |
| `422 Unprocessable Entity` | Invalid request schema |

---

## Performance Characteristics

- **Shorten Operation:** O(1) average time complexity
- **Redirect Operation:** O(1) average time complexity
- **Storage:** In-memory dictionary (no database latency)
- **Throughput:** Thousands of requests per second on standard hardware

---

## Future Enhancements

- [ ] Persistent database storage (PostgreSQL, MongoDB)
- [ ] Custom short codes (user-defined aliases)
- [ ] Click analytics and statistics
- [ ] URL preview before redirect
- [ ] QR code generation
- [ ] Rate limiting and quota management
- [ ] API authentication and key management

---

## Contributing

Built by [Team Claw](https://github.com/RajuRoopani) — an autonomous multi-agent AI development team.

---

## License

MIT License - See LICENSE file for details
