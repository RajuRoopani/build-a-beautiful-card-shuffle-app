# Instagram-Like Social Media API

A FastAPI-based REST API that simulates core Instagram features, providing endpoints for user authentication, post management, social interactions (follows, likes, shares), and user blocking functionality.

## Features

- **User Management**: Register users and manage profiles
- **Posts**: Create, retrieve, and delete posts with media attachments
- **Follows**: Follow/unfollow users and view follower/following lists
- **Feed**: View a personalized feed based on followed users
- **Likes**: Like/unlike posts and track post likes
- **Shares**: Share posts to extend reach
- **Blocks**: Block users to prevent interactions
- **Block Enforcement**: Blocked users cannot like, share, or interact with a blocker's content

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd <project-directory>
pip install -r requirements.txt
```

## Running the API

Start the development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Running Tests

Run the full test suite:

```bash
pytest -v
```

Run specific test files:

```bash
# Test follows functionality
pytest tests/test_follows.py -v

# Test likes functionality
pytest tests/test_likes.py -v

# Test shares functionality
pytest tests/test_shares.py -v

# Test blocks functionality
pytest tests/test_blocks.py -v
```

Run with coverage:

```bash
pytest --cov=app tests/ -v
```

## API Endpoints

### User Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users` | Register a new user |
| GET | `/users/{user_id}` | Get user profile with social counts |
| PUT | `/users/{user_id}` | Update user profile (bio, display_name) |

### Posts

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/posts` | Create a new post |
| GET | `/posts/{post_id}` | Get a specific post |
| DELETE | `/posts/{post_id}` | Delete a post |
| GET | `/users/{user_id}/posts` | Get all posts by a user |

### Feed

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/feed/{user_id}` | Get personalized feed for a user |

### Follows

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users/{user_id}/follow` | Follow a user |
| DELETE | `/users/{user_id}/follow` | Unfollow a user |
| GET | `/users/{user_id}/followers` | Get list of followers |
| GET | `/users/{user_id}/following` | Get list of following |

### Likes

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/posts/{post_id}/like` | Like a post |
| DELETE | `/posts/{post_id}/like` | Unlike a post |
| GET | `/posts/{post_id}/likes` | Get likes for a post |

### Shares

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/posts/{post_id}/share` | Share a post |
| GET | `/posts/{post_id}/shares` | Get shares for a post |

### Blocks

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users/{user_id}/block` | Block a user |
| DELETE | `/users/{user_id}/block` | Unblock a user |
| GET | `/users/{user_id}/blocked` | Get list of blocked users |

## Data Models

### User

```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "display_name": "string",
  "bio": "string or null",
  "follower_count": 0,
  "following_count": 0,
  "post_count": 0
}
```

### Post

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "media_url": "string",
  "media_type": "image or video",
  "caption": "string or null",
  "created_at": "ISO 8601 datetime",
  "like_count": 0,
  "share_count": 0
}
```

### Share

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "original_post_id": "uuid",
  "created_at": "ISO 8601 datetime"
}
```

## Error Responses

### 400 Bad Request
- Duplicate username on registration
- Self-follow/self-block attempts
- Attempting to follow/block/like already-interacted user

### 403 Forbidden
- Attempting to interact with content when blocked by the content owner

### 404 Not Found
- User not found
- Post not found

### 422 Unprocessable Entity
- Invalid or missing required fields in request body

## Tech Stack

- **Framework**: FastAPI
- **Data Validation**: Pydantic
- **Testing**: pytest, httpx (TestClient)
- **Storage**: In-memory dictionaries and sets
- **Server**: Uvicorn

## Architecture

The API uses in-memory data stores for simplicity and fast development iteration:

- `users_db`: Dictionary of user records
- `posts_db`: Dictionary of post records
- `follows`: Set of (follower_id, following_id) tuples
- `followers`: Reverse index mapping user_id to set of follower IDs
- `likes`: Set of (user_id, post_id) tuples
- `shares_db`: Dictionary of share records
- `post_shares`: Index mapping post_id to set of sharing user IDs
- `blocks`: Set of (blocker_id, blocked_id) tuples

## Testing

The test suite includes:
- **test_follows.py**: 9 tests covering follow/unfollow, follower/following lists
- **test_likes.py**: 9 tests covering like/unlike, like lists, and block enforcement
- **test_shares.py**: 6 tests covering share creation, share counts, and block enforcement
- **test_blocks.py**: 11 tests covering block/unblock, blocked lists, and block enforcement

Total: **35+ tests** ensuring comprehensive coverage of all features

Each test:
- Resets in-memory storage before execution (isolation)
- Uses FastAPI's TestClient for integration testing
- Tests success cases (2xx status codes)
- Tests error cases (4xx status codes)
- Tests block enforcement (403 Forbidden)

## Future Enhancements

- Persistent database (PostgreSQL/MongoDB)
- Authentication/JWT tokens
- Comments and replies
- Hashtags and mentions
- User search
- Notifications
- Rate limiting
- Media processing and storage
- Pagination for lists
- Real-time updates (WebSockets)

## License

MIT
