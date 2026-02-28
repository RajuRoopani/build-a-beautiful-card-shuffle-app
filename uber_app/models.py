"""Pydantic models for the Uber-like ride-hailing app."""

from pydantic import BaseModel
from typing import Optional


# ---------------------------------------------------------------------------
# Rider Models
# ---------------------------------------------------------------------------

class RiderCreate(BaseModel):
    name: str
    email: str
    phone: str


class RiderResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str


# ---------------------------------------------------------------------------
# Driver Models
# ---------------------------------------------------------------------------

class DriverCreate(BaseModel):
    name: str
    email: str
    phone: str
    vehicle_make: str
    vehicle_model: str
    license_plate: str


class DriverUpdate(BaseModel):
    """Partial update for a driver — all fields optional."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    license_plate: Optional[str] = None


class DriverResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    vehicle_make: str
    vehicle_model: str
    license_plate: str


# ---------------------------------------------------------------------------
# Ride Models
# ---------------------------------------------------------------------------

class RideCreate(BaseModel):
    rider_id: str
    pickup_location: str
    dropoff_location: str
    passenger_name: Optional[str] = None
    passenger_phone: Optional[str] = None


class RideResponse(BaseModel):
    id: str
    rider_id: str
    driver_id: Optional[str] = None
    pickup_location: str
    dropoff_location: str
    status: str  # requested | accepted | completed | cancelled
    passenger_name: Optional[str] = None
    passenger_phone: Optional[str] = None
    is_family_ride: bool = False
    created_at: str
    updated_at: str


class AcceptRideRequest(BaseModel):
    driver_id: str


class CompleteRideRequest(BaseModel):
    driver_id: str


class CancelRideRequest(BaseModel):
    driver_id: Optional[str] = None
    rider_id: Optional[str] = None
