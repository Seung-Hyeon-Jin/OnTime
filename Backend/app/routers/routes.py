from fastapi import APIRouter, Depends

from app.core.deps import get_route_service
from app.schemas.route import RouteResponse, RouteSearchRequest
from app.services.route_service import RouteService


router = APIRouter(prefix="/api/v1/routes", tags=["routes"])


@router.post("/search", response_model=RouteResponse)
async def search_routes(
    request: RouteSearchRequest,
    service: RouteService = Depends(get_route_service),
) -> RouteResponse:
    return await service.search(request)