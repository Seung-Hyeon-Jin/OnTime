from fastapi import APIRouter, Depends, Query, Request

from app.core.deps import get_arrival_service
from app.schemas.arrival import (
    ArrivalResponse,
    BusStopSearchResponse,
    BusStopSearchResult,
)
from app.services.arrival_service import ArrivalService


router = APIRouter(
    prefix="/api/v1/arrivals",
    tags=["arrivals"],
)


@router.get("/subway", response_model=ArrivalResponse)
async def get_subway_arrivals(
    station_name: str,
    service: ArrivalService = Depends(get_arrival_service),
) -> ArrivalResponse:
    return await service.get_subway_arrivals(station_name)


@router.get("/bus", response_model=ArrivalResponse)
async def get_bus_arrivals(
    city_code: str = Query(..., min_length=1, pattern=r"^\d+$"),
    station_id: str = Query(..., min_length=1),
    service: ArrivalService = Depends(get_arrival_service),
) -> ArrivalResponse:
    return await service.get_bus_arrivals(city_code, station_id)


@router.get("/bus/stops", response_model=BusStopSearchResponse)
async def search_bus_stops(
    request: Request,
    query: str = Query(..., min_length=1),
    city_code: str | None = Query(default=None, pattern=r"^\d+$"),
) -> BusStopSearchResponse:
    repository = request.app.state.bus_stop_repository
    stops = repository.search_by_name(query, city_code=city_code)
    return BusStopSearchResponse(
        query=query,
        items=[
            BusStopSearchResult(
                station_id=stop.station_id,
                name=stop.name,
                city_code=stop.city_code,
                city_name=stop.city_name,
            )
            for stop in stops
        ],
    )