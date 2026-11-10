from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.transport import TransportType


class ArrivalItem(BaseModel):
    transport_type: TransportType
    station_or_stop_name: str
    line_name: str | None = None
    direction: str | None = None
    arrival_seconds: int | None = Field(default=None, ge=0)
    arrival_message: str | None = None
    vehicle_number: str | None = None


class ArrivalResponse(BaseModel):
    provider: str
    queried_at: datetime
    items: list[ArrivalItem]


class BusStopSearchResult(BaseModel):
    station_id: str
    name: str
    city_code: str
    city_name: str


class BusStopSearchResponse(BaseModel):
    query: str
    items: list[BusStopSearchResult]