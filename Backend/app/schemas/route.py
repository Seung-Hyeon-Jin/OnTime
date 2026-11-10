from pydantic import BaseModel, Field
from app.schemas.transport import TransportType
from app.schemas.arrival import ArrivalItem


class Location(BaseModel):
    name: str
    latitude: float
    longitude: float
    city_code: str | None = None


class RouteSearchRequest(BaseModel):
    origin: Location
    destination: Location
    transport_types: list[TransportType] | None = None


class RouteSegment(BaseModel):
    transport_type: TransportType
    line_name: str | None = None
    departure_stop: str | None = None
    arrival_stop: str | None = None
    duration_minutes: int = Field(ge=0)
    distance_meters: int | None = Field(default=None, ge=0)
    stops: list["RouteStop"] = Field(default_factory=list)


class TransferDetail(BaseModel):
    transfer_station: str
    previous_arrival_at: str | None = None
    walking_seconds: int = Field(default=0, ge=0)
    next_vehicle_arrival_at: str | None = None
    waiting_seconds: int | None = Field(default=None, ge=0)
    transfer_feasible: bool


class RouteStop(BaseModel):
    name: str
    latitude: float
    longitude: float
    odsay_station_id: str
    station_id: str | None = None
    city_code: str | None = None
    city_name: str | None = None
    arrivals: list[ArrivalItem] = Field(default_factory=list)
    arrival_error: str | None = None


class RouteResponse(BaseModel):
    provider: str
    total_duration_minutes: int = Field(ge=0)
    transfer_count: int = Field(ge=0)
    fare: int | None = Field(default=None, ge=0)
    segments: list[RouteSegment]
    transfer_details: list[TransferDetail] = Field(default_factory=list)
    calculation_basis: dict | None = None
    alternatives: list["RouteResponse"] = Field(default_factory=list)