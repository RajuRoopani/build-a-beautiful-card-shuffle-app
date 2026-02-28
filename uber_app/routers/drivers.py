"""
Drivers router — driver registration, profile management, and ride history.

Endpoints:
  POST   /api/drivers                    — Register a new driver
  GET    /api/drivers/{driver_id}        — Get driver profile
  PUT    /api/drivers/{driver_id}        — Update driver profile
  GET    /api/drivers/{driver_id}/rides  — Get driver's ride history
"""

from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, HTTPException, status

from uber_app import storage
from uber_app.models import DriverCreate, DriverResponse, DriverUpdate, RideResponse

router = APIRouter(prefix="/api/drivers", tags=["drivers"])


# ---------------------------------------------------------------------------
# POST /api/drivers — Register a new driver
# ---------------------------------------------------------------------------

@router.post("", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
def create_driver(body: DriverCreate) -> DriverResponse:
    """AC6 — Register a new driver with vehicle details."""
    driver_id = str(uuid.uuid4())
    driver: dict = {
        "id": driver_id,
        "name": body.name,
        "email": body.email,
        "phone": body.phone,
        "vehicle_make": body.vehicle_make,
        "vehicle_model": body.vehicle_model,
        "license_plate": body.license_plate,
    }
    storage.drivers[driver_id] = driver
    return DriverResponse(**driver)


# ---------------------------------------------------------------------------
# GET /api/drivers/{driver_id} — Get driver profile
# ---------------------------------------------------------------------------

@router.get("/{driver_id}", response_model=DriverResponse)
def get_driver(driver_id: str) -> DriverResponse:
    """Return a driver's profile by ID."""
    driver = storage.drivers.get(driver_id)
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return DriverResponse(**driver)


# ---------------------------------------------------------------------------
# PUT /api/drivers/{driver_id} — Update driver profile
# ---------------------------------------------------------------------------

@router.put("/{driver_id}", response_model=DriverResponse)
def update_driver(driver_id: str, body: DriverUpdate) -> DriverResponse:
    """
    Partially update a driver's profile.

    Only fields provided in the request body are updated; omitted fields
    retain their current values.
    """
    driver = storage.drivers.get(driver_id)
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")

    update_data = body.model_dump(exclude_none=True)
    driver.update(update_data)
    storage.drivers[driver_id] = driver

    return DriverResponse(**driver)


# ---------------------------------------------------------------------------
# GET /api/drivers/{driver_id}/rides — Driver's ride history
# ---------------------------------------------------------------------------

@router.get("/{driver_id}/rides", response_model=List[RideResponse])
def get_driver_rides(driver_id: str) -> List[dict]:
    """AC10 — Return all rides assigned to a given driver."""
    if driver_id not in storage.drivers:
        raise HTTPException(status_code=404, detail="Driver not found")
    return [r for r in storage.rides.values() if r.get("driver_id") == driver_id]
