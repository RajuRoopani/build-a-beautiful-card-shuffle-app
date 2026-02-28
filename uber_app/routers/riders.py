"""
Riders router — rider registration and ride history.
"""

import uuid
from typing import List

from fastapi import APIRouter, HTTPException

from uber_app import models, storage

router = APIRouter(prefix="/api/riders", tags=["riders"])


# ---------------------------------------------------------------------------
# POST /api/riders — Register a new rider
# ---------------------------------------------------------------------------

@router.post("", response_model=models.RiderResponse, status_code=201)
def create_rider(rider_in: models.RiderCreate) -> dict:
    """AC1 — Register a new rider."""
    rider_id = str(uuid.uuid4())
    rider_data: dict = {"id": rider_id, **rider_in.model_dump()}
    storage.riders[rider_id] = rider_data
    return rider_data


# ---------------------------------------------------------------------------
# GET /api/riders/{rider_id} — Get a rider
# ---------------------------------------------------------------------------

@router.get("/{rider_id}", response_model=models.RiderResponse)
def get_rider(rider_id: str) -> dict:
    """Return a rider by ID."""
    rider = storage.riders.get(rider_id)
    if rider is None:
        raise HTTPException(status_code=404, detail="Rider not found")
    return rider


# ---------------------------------------------------------------------------
# GET /api/riders/{rider_id}/rides — Rider's ride history
# ---------------------------------------------------------------------------

@router.get("/{rider_id}/rides", response_model=List[models.RideResponse])
def get_rider_rides(rider_id: str) -> List[dict]:
    """AC6 — Return all rides for a given rider."""
    if rider_id not in storage.riders:
        raise HTTPException(status_code=404, detail="Rider not found")
    return [r for r in storage.rides.values() if r["rider_id"] == rider_id]
