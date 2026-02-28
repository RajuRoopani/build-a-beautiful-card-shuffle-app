"""
Rides router — all ride-lifecycle endpoints.

Status flow:
    requested → accepted → completed
        ↑           |
        └───────────┘  (driver cancels → back to requested)
    requested → cancelled  (rider cancels)
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from uber_app import models, storage

router = APIRouter(prefix="/api/rides", tags=["rides"])


def _now_iso() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# POST /api/rides — Create a ride request
# ---------------------------------------------------------------------------

@router.post("", response_model=models.RideResponse, status_code=201)
def create_ride(ride_in: models.RideCreate) -> models.RideResponse:
    """
    AC2, AC3 — Request a ride (for self or a family member).

    * rider_id must exist in storage.
    * If both passenger_name AND passenger_phone are provided → is_family_ride=True.
    """
    if ride_in.rider_id not in storage.riders:
        raise HTTPException(status_code=404, detail="Rider not found")

    is_family_ride = bool(ride_in.passenger_name and ride_in.passenger_phone)
    now = _now_iso()
    ride_id = str(uuid.uuid4())

    ride_data: dict = {
        "id": ride_id,
        "rider_id": ride_in.rider_id,
        "driver_id": None,
        "pickup_location": ride_in.pickup_location,
        "dropoff_location": ride_in.dropoff_location,
        "status": "requested",
        "passenger_name": ride_in.passenger_name,
        "passenger_phone": ride_in.passenger_phone,
        "is_family_ride": is_family_ride,
        "created_at": now,
        "updated_at": now,
    }

    storage.rides[ride_id] = ride_data
    return ride_data


# ---------------------------------------------------------------------------
# GET /api/rides — List rides (optionally filtered by status)
# ---------------------------------------------------------------------------

@router.get("", response_model=List[models.RideResponse])
def list_rides(
    status: Optional[str] = Query(default=None, description="Filter by ride status"),
) -> List[dict]:
    """
    AC7 — Return all rides, optionally filtered by ?status=<value>.

    Valid status values: requested, accepted, completed, cancelled.
    """
    all_rides = list(storage.rides.values())
    if status is not None:
        all_rides = [r for r in all_rides if r["status"] == status]
    return all_rides


# ---------------------------------------------------------------------------
# GET /api/rides/{ride_id} — Get ride status
# ---------------------------------------------------------------------------

@router.get("/{ride_id}", response_model=models.RideResponse)
def get_ride(ride_id: str) -> models.RideResponse:
    """AC5 — Return a single ride by ID."""
    ride = storage.rides.get(ride_id)
    if ride is None:
        raise HTTPException(status_code=404, detail="Ride not found")
    return ride


# ---------------------------------------------------------------------------
# PUT /api/rides/{ride_id}/accept — Driver accepts a ride
# ---------------------------------------------------------------------------

@router.put("/{ride_id}/accept", response_model=models.RideResponse)
def accept_ride(ride_id: str, body: models.AcceptRideRequest) -> dict:
    """
    AC8 — A driver accepts a requested ride.

    * ride must exist (404 otherwise).
    * ride status must be "requested" (409 otherwise — checked first).
    * driver must exist in storage (404 otherwise).
    """
    ride = storage.rides.get(ride_id)
    if ride is None:
        raise HTTPException(status_code=404, detail="Ride not found")

    # Check status before driver existence so already-accepted returns 409
    if ride["status"] != "requested":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot accept ride with status '{ride['status']}'. Ride must be in 'requested' state.",
        )

    if body.driver_id not in storage.drivers:
        raise HTTPException(status_code=404, detail="Driver not found")

    ride["driver_id"] = body.driver_id
    ride["status"] = "accepted"
    ride["updated_at"] = _now_iso()
    return ride


# ---------------------------------------------------------------------------
# PUT /api/rides/{ride_id}/complete — Driver completes a ride
# ---------------------------------------------------------------------------

@router.put("/{ride_id}/complete", response_model=models.RideResponse)
def complete_ride(ride_id: str, body: models.CompleteRideRequest) -> dict:
    """
    AC9 — Mark an accepted ride as completed.

    * ride must exist (404 otherwise).
    * ride status must be "accepted" (409 otherwise).
    * Only the assigned driver may complete the ride (403 on mismatch).
    """
    ride = storage.rides.get(ride_id)
    if ride is None:
        raise HTTPException(status_code=404, detail="Ride not found")

    if ride["status"] != "accepted":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot complete ride with status '{ride['status']}'. Ride must be in 'accepted' state.",
        )

    if ride["driver_id"] != body.driver_id:
        raise HTTPException(
            status_code=403,
            detail="Only the assigned driver can complete this ride.",
        )

    ride["status"] = "completed"
    ride["updated_at"] = _now_iso()
    return ride


# ---------------------------------------------------------------------------
# PUT /api/rides/{ride_id}/rider-cancel — Rider cancels their own ride
# ---------------------------------------------------------------------------

@router.put("/{ride_id}/rider-cancel", response_model=models.RideResponse)
def rider_cancel_ride(ride_id: str) -> dict:
    """
    AC13 — Rider cancels their own ride request.

    * ride must exist (404 otherwise).
    * ride status must be "requested" — riders cannot cancel an accepted ride (409).
    * Sets ride status to "cancelled".
    """
    ride = storage.rides.get(ride_id)
    if ride is None:
        raise HTTPException(status_code=404, detail="Ride not found")

    if ride["status"] != "requested":
        raise HTTPException(
            status_code=409,
            detail=f"Rider can only cancel a 'requested' ride, current status: '{ride['status']}'.",
        )

    ride["status"] = "cancelled"
    ride["updated_at"] = _now_iso()
    return ride


# ---------------------------------------------------------------------------
# PUT /api/rides/{ride_id}/cancel — Driver cancels an accepted ride
# ---------------------------------------------------------------------------

@router.put("/{ride_id}/cancel", response_model=models.RideResponse)
def driver_cancel_ride(ride_id: str, body: Optional[models.CancelRideRequest] = None) -> dict:
    """
    Driver cancel endpoint — reverts an accepted ride back to "requested".

    * ride must exist (404 otherwise).
    * ride status must be "accepted" (409 otherwise).
    * Clears the driver assignment so another driver can pick up the ride.

    Also supports the legacy unified cancel format where body contains
    driver_id or rider_id (kept for backwards compatibility).
    """
    ride = storage.rides.get(ride_id)
    if ride is None:
        raise HTTPException(status_code=404, detail="Ride not found")

    # If a body is provided, use it to determine cancel type (legacy support)
    if body is not None:
        # Rider cancel via body
        if body.rider_id is not None:
            if ride["status"] != "requested":
                raise HTTPException(
                    status_code=409,
                    detail=f"Rider can only cancel a 'requested' ride, current status: '{ride['status']}'.",
                )
            ride["status"] = "cancelled"
            ride["updated_at"] = _now_iso()
            return ride

        # Driver cancel via body
        if body.driver_id is not None:
            if ride["status"] != "accepted":
                raise HTTPException(
                    status_code=409,
                    detail=f"Driver can only cancel an 'accepted' ride, current status: '{ride['status']}'.",
                )
            ride["status"] = "requested"
            ride["driver_id"] = None
            ride["updated_at"] = _now_iso()
            return ride

    # No body or empty body — treat as driver-style cancel (must be accepted)
    if ride["status"] != "accepted":
        raise HTTPException(
            status_code=409,
            detail=f"Driver can only cancel an 'accepted' ride, current status: '{ride['status']}'.",
        )

    ride["status"] = "requested"
    ride["driver_id"] = None
    ride["updated_at"] = _now_iso()
    return ride
