"""Test suite for Uber app ride endpoints.

Tests cover:
- Ride creation (self and family rides)
- Ride status tracking
- Driver accepting rides
- Ride completion
- Ride cancellation
- Error cases (404, 409, 403)
"""

import pytest
from fastapi.testclient import TestClient


class TestRideCreation:
    """Tests for creating rides."""

    def test_create_ride(self, client: TestClient, sample_rider: dict):
        """Test creating a basic ride (AC2).
        
        As a rider, I want to request a ride so I can get from point A to point B.
        """
        response = client.post(
            "/api/rides",
            json={
                "rider_id": sample_rider["id"],
                "pickup_location": "123 Main St",
                "dropoff_location": "456 Oak Ave",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "requested"
        assert data["rider_id"] == sample_rider["id"]
        assert data["pickup_location"] == "123 Main St"
        assert data["dropoff_location"] == "456 Oak Ave"
        assert data["is_family_ride"] is False
        assert data["driver_id"] is None
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_ride_family(self, client: TestClient, sample_rider: dict):
        """Test creating a family ride with passenger info (AC3).
        
        As a rider, I want to request a ride for a family member (with
        passenger name & phone) so they can get from point A to point B.
        """
        response = client.post(
            "/api/rides",
            json={
                "rider_id": sample_rider["id"],
                "pickup_location": "789 Family Ln",
                "dropoff_location": "999 Destination Ave",
                "passenger_name": "Jane Doe",
                "passenger_phone": "555-0101",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["is_family_ride"] is True
        assert data["passenger_name"] == "Jane Doe"
        assert data["passenger_phone"] == "555-0101"
        assert data["status"] == "requested"

    def test_create_ride_not_family(self, client: TestClient, sample_rider: dict):
        """Test creating a ride without passenger fields results in is_family_ride=False."""
        response = client.post(
            "/api/rides",
            json={
                "rider_id": sample_rider["id"],
                "pickup_location": "100 Normal St",
                "dropoff_location": "200 Regular Ave",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["is_family_ride"] is False
        assert data["passenger_name"] is None
        assert data["passenger_phone"] is None

    def test_create_ride_invalid_rider(self, client: TestClient):
        """Test creating a ride with nonexistent rider_id returns 404."""
        response = client.post(
            "/api/rides",
            json={
                "rider_id": "nonexistent-rider-id",
                "pickup_location": "123 Main St",
                "dropoff_location": "456 Oak Ave",
            },
        )
        assert response.status_code == 404


class TestRidePartialFamilyFields:
    """Tests for rides with partial family ride fields."""

    def test_create_ride_partial_family_fields_not_family_ride(
        self, client: TestClient, sample_rider: dict
    ):
        """Test that providing only passenger_name or passenger_phone doesn't make it a family ride.
        
        is_family_ride is only True when BOTH passenger_name AND passenger_phone are provided.
        """
        # Create ride with only passenger_name
        response = client.post(
            "/api/rides",
            json={
                "rider_id": sample_rider["id"],
                "pickup_location": "100 Partial St",
                "dropoff_location": "200 Partial Ave",
                "passenger_name": "Jane Doe",
                # passenger_phone not provided
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["is_family_ride"] is False
        assert data["passenger_name"] == "Jane Doe"
        assert data["passenger_phone"] is None

    def test_create_ride_partial_phone_only_not_family_ride(
        self, client: TestClient, sample_rider: dict
    ):
        """Test that providing only passenger_phone doesn't make it a family ride."""
        response = client.post(
            "/api/rides",
            json={
                "rider_id": sample_rider["id"],
                "pickup_location": "100 Phone Only St",
                "dropoff_location": "200 Phone Only Ave",
                "passenger_phone": "555-0101",
                # passenger_name not provided
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["is_family_ride"] is False
        assert data["passenger_name"] is None
        assert data["passenger_phone"] == "555-0101"


class TestRideRetrieval:
    """Tests for retrieving rides."""

    def test_list_rides_empty(self, client: TestClient):
        """Test that listing rides when none exist returns empty list."""
        response = client.get("/api/rides")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_ride(self, client: TestClient, sample_rider: dict):
        """Test retrieving a specific ride by ID (AC5)."""
        # Create a ride
        create_resp = client.post(
            "/api/rides",
            json={
                "rider_id": sample_rider["id"],
                "pickup_location": "123 Main St",
                "dropoff_location": "456 Oak Ave",
            },
        )
        ride_id = create_resp.json()["id"]

        # Retrieve the ride
        response = client.get(f"/api/rides/{ride_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == ride_id
        assert data["rider_id"] == sample_rider["id"]
        assert data["status"] == "requested"

    def test_get_ride_not_found(self, client: TestClient):
        """Test retrieving a nonexistent ride returns 404."""
        response = client.get("/api/rides/nonexistent-ride-id")
        assert response.status_code == 404

    def test_list_rides_by_status(self, client: TestClient, sample_rider: dict):
        """Test filtering rides by status (AC7).
        
        Create multiple rides with different statuses and verify we can
        filter by status=requested.
        """
        # Create a requested ride
        ride1 = client.post(
            "/api/rides",
            json={
                "rider_id": sample_rider["id"],
                "pickup_location": "123 Main St",
                "dropoff_location": "456 Oak Ave",
            },
        ).json()

        # Create another requested ride
        ride2 = client.post(
            "/api/rides",
            json={
                "rider_id": sample_rider["id"],
                "pickup_location": "789 Park Ave",
                "dropoff_location": "999 5th St",
            },
        ).json()

        # List rides with status=requested
        response = client.get("/api/rides?status=requested")
        assert response.status_code == 200
        data = response.json()
        # Should get both rides
        assert len(data) >= 2
        ride_ids = [r["id"] for r in data]
        assert ride1["id"] in ride_ids
        assert ride2["id"] in ride_ids
        # All should be "requested"
        for ride in data:
            assert ride["status"] == "requested"

    def test_get_rider_rides(self, client: TestClient, sample_rider: dict):
        """Test retrieving all rides for a specific rider (AC4)."""
        # Create multiple rides for the rider
        ride1 = client.post(
            "/api/rides",
            json={
                "rider_id": sample_rider["id"],
                "pickup_location": "100 1st St",
                "dropoff_location": "200 2nd St",
            },
        ).json()

        ride2 = client.post(
            "/api/rides",
            json={
                "rider_id": sample_rider["id"],
                "pickup_location": "300 3rd St",
                "dropoff_location": "400 4th St",
            },
        ).json()

        # Retrieve all rides for this rider
        response = client.get(f"/api/riders/{sample_rider['id']}/rides")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        ride_ids = [r["id"] for r in data]
        assert ride1["id"] in ride_ids
        assert ride2["id"] in ride_ids


class TestDriverAcceptRide:
    """Tests for drivers accepting rides."""

    def test_driver_accept_ride(
        self, client: TestClient, sample_rider: dict, sample_driver: dict
    ):
        """Test driver accepting a requested ride (AC8)."""
        # Create a ride
        ride_resp = client.post(
            "/api/rides",
            json={
                "rider_id": sample_rider["id"],
                "pickup_location": "123 Main St",
                "dropoff_location": "456 Oak Ave",
            },
        )
        ride_id = ride_resp.json()["id"]

        # Driver accepts the ride
        response = client.put(
            f"/api/rides/{ride_id}/accept",
            json={"driver_id": sample_driver["id"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["driver_id"] == sample_driver["id"]
        assert data["id"] == ride_id

    def test_driver_accept_already_accepted(
        self, client: TestClient, sample_rider: dict, sample_driver: dict
    ):
        """Test accepting a ride that's already accepted returns 409 (AC9)."""
        # Create another driver for the second attempt
        other_driver_resp = client.post(
            "/api/drivers",
            json={
                "name": "Bob Driver",
                "email": "bob@example.com",
                "phone": "555-0300",
                "vehicle_make": "Honda",
                "vehicle_model": "Civic",
                "license_plate": "XYZ-9999",
            },
        )
        other_driver = other_driver_resp.json()

        # Create a ride
        ride_resp = client.post(
            "/api/rides",
            json={
                "rider_id": sample_rider["id"],
                "pickup_location": "123 Main St",
                "dropoff_location": "456 Oak Ave",
            },
        )
        ride_id = ride_resp.json()["id"]

        # First driver accepts
        client.put(
            f"/api/rides/{ride_id}/accept",
            json={"driver_id": sample_driver["id"]},
        )

        # Another driver tries to accept the same ride
        response = client.put(
            f"/api/rides/{ride_id}/accept",
            json={"driver_id": other_driver["id"]},
        )
        assert response.status_code == 409


class TestRideCompletion:
    """Tests for completing rides."""

    def test_complete_ride(
        self, client: TestClient, sample_rider: dict, sample_driver: dict
    ):
        """Test completing an accepted ride (AC10)."""
        # Create a ride
        ride_resp = client.post(
            "/api/rides",
            json={
                "rider_id": sample_rider["id"],
                "pickup_location": "123 Main St",
                "dropoff_location": "456 Oak Ave",
            },
        )
        ride_id = ride_resp.json()["id"]

        # Driver accepts the ride
        client.put(
            f"/api/rides/{ride_id}/accept",
            json={"driver_id": sample_driver["id"]},
        )

        # Driver completes the ride
        response = client.put(
            f"/api/rides/{ride_id}/complete",
            json={"driver_id": sample_driver["id"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["driver_id"] == sample_driver["id"]

    def test_complete_ride_wrong_driver(
        self, client: TestClient, sample_rider: dict, sample_driver: dict
    ):
        """Test completing a ride with wrong driver_id returns 403 (AC11)."""
        # Create a ride
        ride_resp = client.post(
            "/api/rides",
            json={
                "rider_id": sample_rider["id"],
                "pickup_location": "123 Main St",
                "dropoff_location": "456 Oak Ave",
            },
        )
        ride_id = ride_resp.json()["id"]

        # Driver accepts the ride
        client.put(
            f"/api/rides/{ride_id}/accept",
            json={"driver_id": sample_driver["id"]},
        )

        # Wrong driver tries to complete
        wrong_driver_id = "wrong-driver-id"
        response = client.put(
            f"/api/rides/{ride_id}/complete",
            json={"driver_id": wrong_driver_id},
        )
        assert response.status_code == 403


class TestRideCancellation:
    """Tests for cancelling rides."""

    def test_driver_cancel_ride(
        self, client: TestClient, sample_rider: dict, sample_driver: dict
    ):
        """Test driver cancelling an accepted ride returns to requested (AC12).
        
        Driver can cancel an accepted ride to return it to "requested" state
        so another driver can pick it up.
        """
        # Create a ride
        ride_resp = client.post(
            "/api/rides",
            json={
                "rider_id": sample_rider["id"],
                "pickup_location": "123 Main St",
                "dropoff_location": "456 Oak Ave",
            },
        )
        ride_id = ride_resp.json()["id"]

        # Driver accepts the ride
        client.put(
            f"/api/rides/{ride_id}/accept",
            json={"driver_id": sample_driver["id"]},
        )

        # Driver cancels the ride
        response = client.put(
            f"/api/rides/{ride_id}/cancel",
            json={"driver_id": sample_driver["id"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "requested"
        assert data["driver_id"] is None

    def test_rider_cancel_success(self, client: TestClient, sample_rider: dict):
        """Test rider cancelling their own requested ride (AC13).
        
        As a rider, I want to cancel my ride request if it's still pending,
        so I can cancel if my plans change before a driver accepts.
        """
        # Create a ride (requested)
        ride_resp = client.post(
            "/api/rides",
            json={
                "rider_id": sample_rider["id"],
                "pickup_location": "100 Start",
                "dropoff_location": "200 End",
            },
        )
        ride_id = ride_resp.json()["id"]
        assert ride_resp.json()["status"] == "requested"

        # Rider cancels the ride by providing rider_id
        cancel_resp = client.put(
            f"/api/rides/{ride_id}/cancel",
            json={"rider_id": sample_rider["id"]}
        )
        assert cancel_resp.status_code == 200
        data = cancel_resp.json()
        assert data["status"] == "cancelled"
        assert data["id"] == ride_id

    def test_rider_cancel_after_accept_fails(
        self, client: TestClient, sample_rider: dict, sample_driver: dict
    ):
        """Test that rider cannot cancel a ride after a driver accepts it (AC14).
        
        Once a driver accepts a ride, the rider can no longer cancel it directly.
        The driver must cancel first to return it to requested state.
        """
        # Create a ride (requested)
        ride_resp = client.post(
            "/api/rides",
            json={
                "rider_id": sample_rider["id"],
                "pickup_location": "100 Start",
                "dropoff_location": "200 End",
            },
        )
        ride_id = ride_resp.json()["id"]

        # Driver accepts
        accept_resp = client.put(
            f"/api/rides/{ride_id}/accept",
            json={"driver_id": sample_driver["id"]},
        )
        assert accept_resp.json()["status"] == "accepted"

        # Rider tries to cancel after accept (should fail with 409)
        cancel_resp = client.put(
            f"/api/rides/{ride_id}/cancel",
            json={"rider_id": sample_rider["id"]}
        )
        assert cancel_resp.status_code == 409

    def test_driver_cancel_requested_ride_not_allowed(
        self, client: TestClient, sample_rider: dict, sample_driver: dict
    ):
        """Test that driver cannot cancel a ride that's still in requested state.
        
        Driver can only cancel accepted rides (returns to requested).
        """
        # Create a ride (status="requested")
        ride_resp = client.post(
            "/api/rides",
            json={
                "rider_id": sample_rider["id"],
                "pickup_location": "300 No Cancel St",
                "dropoff_location": "400 No Cancel Ave",
            },
        )
        ride_id = ride_resp.json()["id"]

        # Try to cancel without accepting (should fail with 409)
        response = client.put(
            f"/api/rides/{ride_id}/cancel",
            json={"driver_id": sample_driver["id"]}
        )
        assert response.status_code == 409

    def test_rider_cancel_nonexistent_ride(self, client: TestClient, sample_rider: dict):
        """Test that cancelling a nonexistent ride returns 404."""
        response = client.put(
            "/api/rides/nonexistent-ride-id/cancel",
            json={"rider_id": sample_rider["id"]}
        )
        assert response.status_code == 404


class TestRideEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_get_rider_rides_rider_not_found(self, client: TestClient):
        """Test getting rides for nonexistent rider returns 404."""
        response = client.get("/api/riders/nonexistent-rider-id/rides")
        assert response.status_code == 404

    def test_complete_before_accept(self, client: TestClient, sample_rider: dict, sample_driver: dict):
        """Test completing a ride without accepting it first returns 409."""
        # Create a ride (status="requested")
        ride_resp = client.post(
            "/api/rides",
            json={
                "rider_id": sample_rider["id"],
                "pickup_location": "123 Main St",
                "dropoff_location": "456 Oak Ave",
            },
        )
        ride_id = ride_resp.json()["id"]

        # Try to complete without accepting
        response = client.put(
            f"/api/rides/{ride_id}/complete",
            json={"driver_id": sample_driver["id"]},
        )
        assert response.status_code == 409

    def test_accept_nonexistent_ride(self, client: TestClient, sample_driver: dict):
        """Test accepting a ride that doesn't exist returns 404."""
        response = client.put(
            "/api/rides/nonexistent-ride-id/accept",
            json={"driver_id": sample_driver["id"]},
        )
        assert response.status_code == 404

    def test_accept_with_nonexistent_driver(self, client: TestClient, sample_rider: dict):
        """Test accepting a ride with a nonexistent driver returns 404."""
        # Create a ride
        ride_resp = client.post(
            "/api/rides",
            json={
                "rider_id": sample_rider["id"],
                "pickup_location": "100 Test St",
                "dropoff_location": "200 Test Ave",
            },
        )
        ride_id = ride_resp.json()["id"]

        # Try to accept with nonexistent driver
        response = client.put(
            f"/api/rides/{ride_id}/accept",
            json={"driver_id": "nonexistent-driver-id"},
        )
        assert response.status_code == 404



    def test_multiple_rides_for_single_rider(self, client: TestClient, sample_rider: dict):
        """Test creating multiple rides for one rider and retrieving them all."""
        ride_ids = []
        for i in range(3):
            ride_resp = client.post(
                "/api/rides",
                json={
                    "rider_id": sample_rider["id"],
                    "pickup_location": f"{i * 100} Start St",
                    "dropoff_location": f"{i * 100} End Ave",
                },
            )
            ride_ids.append(ride_resp.json()["id"])

        # Retrieve all rides for the rider
        response = client.get(f"/api/riders/{sample_rider['id']}/rides")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        returned_ids = {r["id"] for r in data}
        assert returned_ids == set(ride_ids)

    def test_ride_status_progression(
        self, client: TestClient, sample_rider: dict, sample_driver: dict
    ):
        """Test the full lifecycle of a ride: requested -> accepted -> completed."""
        # Create ride (requested)
        ride_resp = client.post(
            "/api/rides",
            json={
                "rider_id": sample_rider["id"],
                "pickup_location": "Start",
                "dropoff_location": "End",
            },
        )
        ride_id = ride_resp.json()["id"]
        assert ride_resp.json()["status"] == "requested"

        # Accept ride
        accept_resp = client.put(
            f"/api/rides/{ride_id}/accept",
            json={"driver_id": sample_driver["id"]},
        )
        assert accept_resp.json()["status"] == "accepted"
        assert accept_resp.json()["driver_id"] == sample_driver["id"]

        # Complete ride
        complete_resp = client.put(
            f"/api/rides/{ride_id}/complete",
            json={"driver_id": sample_driver["id"]},
        )
        assert complete_resp.json()["status"] == "completed"

        # Verify final state
        get_resp = client.get(f"/api/rides/{ride_id}")
        assert get_resp.json()["status"] == "completed"

    def test_list_all_rides(self, client: TestClient, sample_rider: dict):
        """Test listing all rides without status filter."""
        # Create multiple rides
        ride1 = client.post(
            "/api/rides",
            json={
                "rider_id": sample_rider["id"],
                "pickup_location": "A",
                "dropoff_location": "B",
            },
        ).json()

        ride2 = client.post(
            "/api/rides",
            json={
                "rider_id": sample_rider["id"],
                "pickup_location": "C",
                "dropoff_location": "D",
            },
        ).json()

        # List all rides
        response = client.get("/api/rides")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        ride_ids = [r["id"] for r in data]
        assert ride1["id"] in ride_ids
        assert ride2["id"] in ride_ids

    def test_updated_at_changes_on_accept(
        self, client: TestClient, sample_rider: dict, sample_driver: dict
    ):
        """Test that updated_at timestamp changes when a ride is accepted."""
        # Create a ride
        ride_resp = client.post(
            "/api/rides",
            json={
                "rider_id": sample_rider["id"],
                "pickup_location": "Start",
                "dropoff_location": "End",
            },
        )
        ride = ride_resp.json()
        created_at = ride["created_at"]
        original_updated_at = ride["updated_at"]

        # Accept the ride
        accept_resp = client.put(
            f"/api/rides/{ride['id']}/accept",
            json={"driver_id": sample_driver["id"]},
        )
        accepted_ride = accept_resp.json()
        new_updated_at = accepted_ride["updated_at"]

        # updated_at should have changed
        assert new_updated_at != original_updated_at
        # created_at should NOT have changed
        assert accepted_ride["created_at"] == created_at
