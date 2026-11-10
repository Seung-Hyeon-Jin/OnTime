from fastapi import APIRouter, Depends, Query, Request

from app.schemas.location import LocationSearchResponse

router = APIRouter(prefix="/api/v1/locations", tags=["locations"])


@router.get("/search", response_model=LocationSearchResponse)
async def search_locations(
    request: Request,
    query: str = Query(..., min_length=1, description="장소명 또는 주소 키워드"),
) -> LocationSearchResponse:
    kakao_client = request.app.state.kakao_client
    return await kakao_client.search_places(query)


@router.get("/reverse-geocode")
async def reverse_geocode_location(
    request: Request,
    lat: float = Query(..., description="위도 Latitude"),
    lng: float = Query(..., description="경도 Longitude"),
):
    kakao_client = request.app.state.kakao_client
    return await kakao_client.reverse_geocode(lat, lng)
