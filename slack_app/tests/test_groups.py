"""
Tests for the Groups endpoints:
  - POST /groups (create group)
  - GET /groups/{group_id} (get group details)
  - POST /groups/{group_id}/messages (send group message)
  - GET /groups/{group_id}/messages (get group messages)
  - POST /groups/{group_id}/members (add member)
"""
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_user(client: TestClient, username: str, display_name: str) -> dict:
    """Shortcut to create a user and return the response dict."""
    resp = client.post("/users", json={"username": username, "display_name": display_name})
    assert resp.status_code == 201
    return resp.json()


def _create_group(client: TestClient, name: str, creator_id: str) -> dict:
    """Shortcut to create a group and return the response dict."""
    resp = client.post("/groups", json={"name": name, "creator_id": creator_id})
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# POST /groups — Create Group
# ---------------------------------------------------------------------------

class TestCreateGroup:
    def test_create_group_returns_201(self, client: TestClient):
        user = _create_user(client, "alice", "Alice")
        resp = client.post("/groups", json={"name": "general", "creator_id": user["user_id"]})
        assert resp.status_code == 201

    def test_create_group_response_shape(self, client: TestClient):
        user = _create_user(client, "alice", "Alice")
        data = _create_group(client, "general", user["user_id"])
        assert "id" in data
        assert data["name"] == "general"
        assert data["creator_id"] == user["user_id"]
        assert "members" in data
        assert "created_at" in data

    def test_creator_auto_added_to_members(self, client: TestClient):
        user = _create_user(client, "alice", "Alice")
        group = _create_group(client, "general", user["user_id"])
        assert user["user_id"] in group["members"]

    def test_creator_is_first_member(self, client: TestClient):
        user = _create_user(client, "alice", "Alice")
        group = _create_group(client, "general", user["user_id"])
        assert group["members"][0] == user["user_id"]

    def test_create_group_unique_ids(self, client: TestClient):
        user = _create_user(client, "alice", "Alice")
        g1 = _create_group(client, "group-a", user["user_id"])
        g2 = _create_group(client, "group-b", user["user_id"])
        assert g1["id"] != g2["id"]

    def test_create_group_nonexistent_creator_returns_404(self, client: TestClient):
        resp = client.post("/groups", json={"name": "general", "creator_id": "ghost"})
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /groups/{group_id} — Get Group Details
# ---------------------------------------------------------------------------

class TestGetGroup:
    def test_get_existing_group(self, client: TestClient):
        user = _create_user(client, "alice", "Alice")
        group = _create_group(client, "general", user["user_id"])
        resp = client.get(f"/groups/{group['id']}")
        assert resp.status_code == 200

    def test_get_group_fields_match(self, client: TestClient):
        user = _create_user(client, "alice", "Alice")
        created = _create_group(client, "general", user["user_id"])
        fetched = client.get(f"/groups/{created['id']}").json()
        assert fetched["id"] == created["id"]
        assert fetched["name"] == created["name"]
        assert fetched["creator_id"] == created["creator_id"]
        assert fetched["members"] == created["members"]
        assert fetched["created_at"] == created["created_at"]

    def test_get_nonexistent_group_returns_404(self, client: TestClient):
        resp = client.get("/groups/nonexistent-id")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /groups/{group_id}/messages — Send Group Message
# ---------------------------------------------------------------------------

class TestSendGroupMessage:
    def test_send_message_returns_201(self, client: TestClient):
        user = _create_user(client, "alice", "Alice")
        group = _create_group(client, "general", user["user_id"])
        resp = client.post(f"/groups/{group['id']}/messages", json={
            "sender_id": user["user_id"],
            "content": "Hello group!",
        })
        assert resp.status_code == 201

    def test_send_message_response_shape(self, client: TestClient):
        user = _create_user(client, "alice", "Alice")
        group = _create_group(client, "general", user["user_id"])
        resp = client.post(f"/groups/{group['id']}/messages", json={
            "sender_id": user["user_id"],
            "content": "Hello group!",
        })
        data = resp.json()
        assert "id" in data
        assert data["group_id"] == group["id"]
        assert data["sender_id"] == user["user_id"]
        assert data["content"] == "Hello group!"
        assert "created_at" in data

    def test_send_message_unique_ids(self, client: TestClient):
        user = _create_user(client, "alice", "Alice")
        group = _create_group(client, "general", user["user_id"])
        payload = {"sender_id": user["user_id"], "content": "hi"}
        id1 = client.post(f"/groups/{group['id']}/messages", json=payload).json()["id"]
        id2 = client.post(f"/groups/{group['id']}/messages", json=payload).json()["id"]
        assert id1 != id2

    def test_send_message_nonexistent_group_returns_404(self, client: TestClient):
        user = _create_user(client, "alice", "Alice")
        resp = client.post("/groups/fake-id/messages", json={
            "sender_id": user["user_id"],
            "content": "Hello?",
        })
        assert resp.status_code == 404

    def test_send_message_non_member_returns_403(self, client: TestClient):
        alice = _create_user(client, "alice", "Alice")
        bob = _create_user(client, "bob", "Bob")
        group = _create_group(client, "general", alice["user_id"])
        resp = client.post(f"/groups/{group['id']}/messages", json={
            "sender_id": bob["user_id"],
            "content": "Can I talk?",
        })
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /groups/{group_id}/messages — Get Group Messages
# ---------------------------------------------------------------------------

class TestGetGroupMessages:
    def test_get_messages_returns_list(self, client: TestClient):
        user = _create_user(client, "alice", "Alice")
        group = _create_group(client, "general", user["user_id"])
        resp = client.get(f"/groups/{group['id']}/messages")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_messages_after_sending(self, client: TestClient):
        user = _create_user(client, "alice", "Alice")
        group = _create_group(client, "general", user["user_id"])
        client.post(f"/groups/{group['id']}/messages", json={
            "sender_id": user["user_id"],
            "content": "first",
        })
        client.post(f"/groups/{group['id']}/messages", json={
            "sender_id": user["user_id"],
            "content": "second",
        })
        msgs = client.get(f"/groups/{group['id']}/messages").json()
        assert len(msgs) == 2

    def test_get_messages_sorted_chronologically(self, client: TestClient):
        user = _create_user(client, "alice", "Alice")
        group = _create_group(client, "general", user["user_id"])
        for i in range(3):
            client.post(f"/groups/{group['id']}/messages", json={
                "sender_id": user["user_id"],
                "content": f"msg {i}",
            })
        msgs = client.get(f"/groups/{group['id']}/messages").json()
        timestamps = [m["created_at"] for m in msgs]
        assert timestamps == sorted(timestamps)

    def test_get_messages_nonexistent_group_returns_404(self, client: TestClient):
        resp = client.get("/groups/nonexistent-id/messages")
        assert resp.status_code == 404

    def test_messages_isolated_between_groups(self, client: TestClient):
        user = _create_user(client, "alice", "Alice")
        g1 = _create_group(client, "group-1", user["user_id"])
        g2 = _create_group(client, "group-2", user["user_id"])
        client.post(f"/groups/{g1['id']}/messages", json={
            "sender_id": user["user_id"],
            "content": "In group 1",
        })
        client.post(f"/groups/{g2['id']}/messages", json={
            "sender_id": user["user_id"],
            "content": "In group 2",
        })
        msgs1 = client.get(f"/groups/{g1['id']}/messages").json()
        msgs2 = client.get(f"/groups/{g2['id']}/messages").json()
        assert len(msgs1) == 1
        assert msgs1[0]["content"] == "In group 1"
        assert len(msgs2) == 1
        assert msgs2[0]["content"] == "In group 2"


# ---------------------------------------------------------------------------
# POST /groups/{group_id}/members — Add Member
# ---------------------------------------------------------------------------

class TestAddMember:
    def test_add_member_returns_200(self, client: TestClient):
        alice = _create_user(client, "alice", "Alice")
        bob = _create_user(client, "bob", "Bob")
        group = _create_group(client, "general", alice["user_id"])
        resp = client.post(f"/groups/{group['id']}/members", json={"user_id": bob["user_id"]})
        assert resp.status_code == 200

    def test_added_member_appears_in_group(self, client: TestClient):
        alice = _create_user(client, "alice", "Alice")
        bob = _create_user(client, "bob", "Bob")
        group = _create_group(client, "general", alice["user_id"])
        client.post(f"/groups/{group['id']}/members", json={"user_id": bob["user_id"]})
        updated = client.get(f"/groups/{group['id']}").json()
        assert bob["user_id"] in updated["members"]

    def test_added_member_can_send_message(self, client: TestClient):
        alice = _create_user(client, "alice", "Alice")
        bob = _create_user(client, "bob", "Bob")
        group = _create_group(client, "general", alice["user_id"])
        client.post(f"/groups/{group['id']}/members", json={"user_id": bob["user_id"]})
        resp = client.post(f"/groups/{group['id']}/messages", json={
            "sender_id": bob["user_id"],
            "content": "I'm in!",
        })
        assert resp.status_code == 201

    def test_add_member_nonexistent_group_returns_404(self, client: TestClient):
        bob = _create_user(client, "bob", "Bob")
        resp = client.post("/groups/fake-group/members", json={"user_id": bob["user_id"]})
        assert resp.status_code == 404

    def test_add_nonexistent_user_returns_404(self, client: TestClient):
        alice = _create_user(client, "alice", "Alice")
        group = _create_group(client, "general", alice["user_id"])
        resp = client.post(f"/groups/{group['id']}/members", json={"user_id": "ghost"})
        assert resp.status_code == 404

    def test_add_duplicate_member_returns_409(self, client: TestClient):
        alice = _create_user(client, "alice", "Alice")
        group = _create_group(client, "general", alice["user_id"])
        resp = client.post(f"/groups/{group['id']}/members", json={"user_id": alice["user_id"]})
        assert resp.status_code == 409
