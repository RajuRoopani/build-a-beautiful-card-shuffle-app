"""
Tests for the Users and Direct Messages endpoints.
"""
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

class TestCreateUser:
    def test_create_user_returns_201(self, client: TestClient):
        resp = client.post("/users", json={"username": "alice", "display_name": "Alice"})
        assert resp.status_code == 201

    def test_create_user_response_shape(self, client: TestClient):
        resp = client.post("/users", json={"username": "alice", "display_name": "Alice"})
        data = resp.json()
        assert "user_id" in data
        assert data["username"] == "alice"
        assert data["display_name"] == "Alice"
        assert "created_at" in data

    def test_create_user_generates_unique_ids(self, client: TestClient):
        r1 = client.post("/users", json={"username": "u1", "display_name": "U1"})
        r2 = client.post("/users", json={"username": "u2", "display_name": "U2"})
        assert r1.json()["user_id"] != r2.json()["user_id"]


class TestListUsers:
    def test_list_users_empty(self, client: TestClient):
        resp = client.get("/users")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_users_returns_all(self, client: TestClient, two_users):
        resp = client.get("/users")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_list_users_contains_created_user(self, client: TestClient):
        client.post("/users", json={"username": "carol", "display_name": "Carol"})
        users = client.get("/users").json()
        usernames = [u["username"] for u in users]
        assert "carol" in usernames


class TestGetUser:
    def test_get_existing_user(self, client: TestClient):
        created = client.post("/users", json={"username": "dave", "display_name": "Dave"}).json()
        resp = client.get(f"/users/{created['user_id']}")
        assert resp.status_code == 200
        assert resp.json()["username"] == "dave"

    def test_get_nonexistent_user_returns_404(self, client: TestClient):
        resp = client.get("/users/does-not-exist")
        assert resp.status_code == 404

    def test_get_user_fields_match(self, client: TestClient):
        created = client.post("/users", json={"username": "eve", "display_name": "Eve"}).json()
        fetched = client.get(f"/users/{created['user_id']}").json()
        assert fetched["user_id"] == created["user_id"]
        assert fetched["username"] == created["username"]
        assert fetched["display_name"] == created["display_name"]
        assert fetched["created_at"] == created["created_at"]


# ---------------------------------------------------------------------------
# Direct Messages
# ---------------------------------------------------------------------------

class TestSendMessage:
    def test_send_message_returns_201(self, client: TestClient, two_users):
        alice, bob = two_users
        resp = client.post("/messages", json={
            "sender_id": alice["user_id"],
            "receiver_id": bob["user_id"],
            "content": "Hello Bob!",
        })
        assert resp.status_code == 201

    def test_send_message_response_shape(self, client: TestClient, two_users):
        alice, bob = two_users
        resp = client.post("/messages", json={
            "sender_id": alice["user_id"],
            "receiver_id": bob["user_id"],
            "content": "Hi there",
        })
        data = resp.json()
        assert "message_id" in data
        assert data["sender_id"] == alice["user_id"]
        assert data["receiver_id"] == bob["user_id"]
        assert data["content"] == "Hi there"
        assert "timestamp" in data

    def test_send_message_invalid_sender_returns_404(self, client: TestClient, two_users):
        _, bob = two_users
        resp = client.post("/messages", json={
            "sender_id": "ghost-id",
            "receiver_id": bob["user_id"],
            "content": "boo",
        })
        assert resp.status_code == 404

    def test_send_message_invalid_receiver_returns_404(self, client: TestClient, two_users):
        alice, _ = two_users
        resp = client.post("/messages", json={
            "sender_id": alice["user_id"],
            "receiver_id": "ghost-id",
            "content": "boo",
        })
        assert resp.status_code == 404

    def test_send_message_generates_unique_message_ids(self, client: TestClient, two_users):
        alice, bob = two_users
        payload = {"sender_id": alice["user_id"], "receiver_id": bob["user_id"], "content": "x"}
        id1 = client.post("/messages", json=payload).json()["message_id"]
        id2 = client.post("/messages", json=payload).json()["message_id"]
        assert id1 != id2


class TestGetConversation:
    def test_get_conversation_returns_messages(self, client: TestClient, two_users):
        alice, bob = two_users
        client.post("/messages", json={
            "sender_id": alice["user_id"],
            "receiver_id": bob["user_id"],
            "content": "Hey Bob",
        })
        resp = client.get("/messages", params={"user1": alice["user_id"], "user2": bob["user_id"]})
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["content"] == "Hey Bob"

    def test_get_conversation_bidirectional(self, client: TestClient, two_users):
        alice, bob = two_users
        client.post("/messages", json={
            "sender_id": alice["user_id"],
            "receiver_id": bob["user_id"],
            "content": "Hello Bob",
        })
        client.post("/messages", json={
            "sender_id": bob["user_id"],
            "receiver_id": alice["user_id"],
            "content": "Hello Alice",
        })
        resp = client.get("/messages", params={"user1": alice["user_id"], "user2": bob["user_id"]})
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_get_conversation_sorted_chronologically(self, client: TestClient, two_users):
        alice, bob = two_users
        for i in range(3):
            client.post("/messages", json={
                "sender_id": alice["user_id"],
                "receiver_id": bob["user_id"],
                "content": f"Message {i}",
            })
        msgs = client.get("/messages", params={
            "user1": alice["user_id"],
            "user2": bob["user_id"],
        }).json()
        timestamps = [m["timestamp"] for m in msgs]
        assert timestamps == sorted(timestamps)

    def test_get_conversation_excludes_unrelated_messages(self, client: TestClient):
        """Messages between other users should not appear in the conversation."""
        alice = client.post("/users", json={"username": "alice", "display_name": "Alice"}).json()
        bob = client.post("/users", json={"username": "bob", "display_name": "Bob"}).json()
        carol = client.post("/users", json={"username": "carol", "display_name": "Carol"}).json()

        # Alice → Bob
        client.post("/messages", json={
            "sender_id": alice["user_id"],
            "receiver_id": bob["user_id"],
            "content": "Hi Bob",
        })
        # Alice → Carol (should NOT appear in Alice-Bob conversation)
        client.post("/messages", json={
            "sender_id": alice["user_id"],
            "receiver_id": carol["user_id"],
            "content": "Hi Carol",
        })

        resp = client.get("/messages", params={"user1": alice["user_id"], "user2": bob["user_id"]})
        msgs = resp.json()
        assert len(msgs) == 1
        assert msgs[0]["content"] == "Hi Bob"

    def test_get_conversation_empty_when_no_messages(self, client: TestClient, two_users):
        alice, bob = two_users
        resp = client.get("/messages", params={"user1": alice["user_id"], "user2": bob["user_id"]})
        assert resp.status_code == 200
        assert resp.json() == []
