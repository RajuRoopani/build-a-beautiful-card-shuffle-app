"""FastAPI application entry point for the Uber-like ride-hailing app."""

from fastapi import FastAPI

from uber_app.routers import drivers, riders, rides

app = FastAPI(
    title="Uber-like Ride-Hailing App",
    description="A simple ride-hailing platform supporting riders, drivers, and ride matching.",
    version="1.0.0",
)

app.include_router(riders.router)
app.include_router(drivers.router)
app.include_router(rides.router)
