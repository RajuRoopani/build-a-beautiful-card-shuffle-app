# Slack Messaging App

A FastAPI REST API that replicates core Slack features: user accounts, direct messages between users, and group chat channels with membership management.

Built by [Team Claw](https://github.com/RajuRoopani) — an autonomous multi-agent AI development team.

---

## Features

- **Users** — register users, list all users, look up by ID
- **Direct Messages** — send DMs between users, fetch full conversation history between any two users
- **Groups** — create group channels, add members, send and retrieve group messages with 403 enforcement for non-members

---

## Project Structure

```
slack_app/
├── main.py           # FastAPI app entry point
├── models.py         # Pydantic request/response schemas
├── storage.py        # In-memory data stores (reset-safe for testing)
├── requirements.txt
└── routers/
    ├── users.py      # POST/GET /users, GET /users/{id}
    ├── messages.py   # POST /messages, GET /messages
    └── groups.py     # POST/GET /groups, group messages, membership
tests/
└── slack_app/
    ├── conftest.py
    ├── test_users_messages.py   # 23 tests — users & DMs
    └── test_groups.py           # 25 tests — group chat
```

---

## API Reference

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/users` | Register a new user |
| `GET` | `/users` | List all users |
| `GET` | `/users/{user_id}` | Get user by ID |

**Create user**
```json
POST /users
{
  "username": "alice",
  "display_name": "Alice Smith"
}
```
Response `201`:
```json
{
  "user_id": "uuid",
  "username": "alice",
  "display_name": "Alice Smith",
  "created_at": "2026-01-01T00:00:00+00:00"
}
```

---

### Direct Messages

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/messages` | Send a DM |
| `GET` | `/messages?user1=<id>&user2=<id>` | Get conversation between two users |

**Send DM**
```json
POST /messages
{
  "sender_id": "<user_id>",
  "receiver_id": "<user_id>",
  "content": "Hey, what's up?"
}
```
Returns `201` with the message record. Returns `404` if either user doesn't exist.

**Get conversation**
```
GET /messages?user1=<id>&user2=<id>
```
Returns messages in both directions sorted chronologically.

---

### Groups

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/groups` | Create a group |
| `GET` | `/groups/{group_id}` | Get group details |
| `POST` | `/groups/{group_id}/messages` | Send a message to a group |
| `GET` | `/groups/{group_id}/messages` | Get all messages in a group |
| `POST` | `/groups/{group_id}/members` | Add a member to a group |

**Create group**
```json
POST /groups
{
  "name": "engineering",
  "creator_id": "<user_id>",
  "member_ids": ["<user_id2>", "<user_id3>"]
}
```
Response `201`:
```json
{
  "id": "uuid",
  "name": "engineering",
  "creator_id": "<user_id>",
  "members": ["<creator_id>", "<user_id2>", "<user_id3>"],
  "created_at": "2026-01-01T00:00:00+00:00"
}
```

**Send group message**
```json
POST /groups/{group_id}/messages
{
  "sender_id": "<user_id>",
  "content": "Hello team!"
}
```
Returns `201` on success, `403` if sender is not a member, `404` if group doesn't exist.

**Add member**
```json
POST /groups/{group_id}/members
{
  "user_id": "<new_member_id>"
}
```
Returns `200` with updated group, `409` if already a member, `404` if user or group not found.

---

## Installation

```bash
cd slack_app
pip install -r requirements.txt
```

## Running

```bash
uvicorn slack_app.main:app --reload
```

Visit `http://localhost:8000/docs` for the interactive Swagger UI.

## Tests

```bash
pytest slack_app/tests/ -v
```

All **48 tests** pass (23 for users/DMs + 25 for groups).

---

## Error Codes

| Status | Meaning |
|--------|---------|
| `404` | User, group, or resource not found |
| `403` | Sender not a member of the group |
| `409` | User already a member of the group |
| `422` | Missing or invalid request fields |
