from datetime import datetime, timezone
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

# PUBLIC_INTERFACE
class GeoPoint(BaseModel):
    """Represents a geographic coordinate (latitude, longitude)."""
    lat: float = Field(..., description="Latitude in decimal degrees", ge=-90, le=90)
    lng: float = Field(..., description="Longitude in decimal degrees", ge=-180, le=180)


# PUBLIC_INTERFACE
class LocationUpdate(BaseModel):
    """Incoming payload from courier app to update live location."""
    orderId: str = Field(..., description="Order identifier")
    courierId: str = Field(..., description="Courier/agent identifier")
    position: GeoPoint = Field(..., description="Current geo position of the courier")
    bearing: Optional[float] = Field(None, description="Heading in degrees")
    speedMps: Optional[float] = Field(None, description="Speed in meters per second", ge=0)
    timestamp: datetime = Field(..., description="Timestamp of the location sample (ISO 8601)")

    @validator("timestamp")
    def ensure_timezone(cls, v: datetime) -> datetime:
        # Normalize to UTC if naive, to avoid TZ issues in memory storage
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)


# PUBLIC_INTERFACE
class LocationSnapshot(BaseModel):
    """Latest location snapshot for an order, with optional ETA in minutes."""
    position: GeoPoint = Field(..., description="Latest known position")
    timestamp: datetime = Field(..., description="Timestamp of the latest position (UTC)")
    etaMinutes: Optional[int] = Field(None, description="Estimated minutes to arrival")


app = FastAPI(
    title="Location Service API",
    description="Provides live location updates and tracking for delivery orders.",
    version="1.0.0",
    openapi_tags=[
        {"name": "Location", "description": "Live tracking and latest position per order."}
    ],
)

# Allow cross-origin requests for local development and broad compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For MVP; tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store: orderId -> LocationSnapshot
_LOCATION_STORE: Dict[str, LocationSnapshot] = {}


def _estimate_eta_minutes(speed_mps: Optional[float]) -> Optional[int]:
    """
    Very naive ETA estimation for MVP purposes:
    - If speed_mps is not provided or zero, return None.
    - Otherwise, return a placeholder constant ETA.
    """
    if speed_mps is None or speed_mps <= 0:
        return None
    # Placeholder: return 10 minutes as a constant ETA for MVP
    return 10


@app.post(
    "/location/updates",
    status_code=202,
    tags=["Location"],
    summary="Submit live location update from courier app",
)
# PUBLIC_INTERFACE
def post_location_update(update: LocationUpdate):
    """
    Accepts a live location update and stores the latest snapshot for the given orderId.

    Parameters:
    - update: LocationUpdate payload containing orderId, courierId, position, and timestamp.

    Returns:
    - 202 Accepted with an empty body upon successful processing.
    """
    snapshot = LocationSnapshot(
        position=update.position,
        timestamp=update.timestamp,
        etaMinutes=_estimate_eta_minutes(update.speedMps),
    )
    # Store or overwrite the latest snapshot for the order
    _LOCATION_STORE[update.orderId] = snapshot
    return {"status": "accepted"}


@app.get(
    "/location/track/{orderId}",
    response_model=LocationSnapshot,
    tags=["Location"],
    summary="Get latest location and ETA for an order",
)
# PUBLIC_INTERFACE
def get_latest_location(orderId: str):
    """
    Fetches the latest known location snapshot for a specific order.

    Path parameters:
    - orderId: The identifier of the order whose latest location is requested.

    Returns:
    - 200 OK with LocationSnapshot if found.
    - 404 Not Found if no location exists for the given orderId.
    """
    snapshot = _LOCATION_STORE.get(orderId)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Location not found for orderId")
    return snapshot


@app.get("/", include_in_schema=False)
def root():
    return {"service": "LocationService", "status": "ok"}


# PUBLIC_INTERFACE
def get_app() -> FastAPI:
    """Factory accessor to retrieve the FastAPI application instance."""
    return app
