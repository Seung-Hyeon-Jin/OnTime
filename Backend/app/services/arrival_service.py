import logging
from app.clients.subway_client import SubwayClient
from app.clients.bus_client import BusClient
from app.core.redis_service import cache_service
from app.schemas.arrival import ArrivalResponse

logger = logging.getLogger(__name__)

class ArrivalService:
    def __init__(
        self,
        subway_client: SubwayClient,
        bus_client: BusClient,
    ):
        self.subway_client = subway_client
        self.bus_client = bus_client

    async def get_subway_arrivals(
        self,
        station_name: str,
    ) -> ArrivalResponse:
        norm_name = station_name.replace(" ", "").removesuffix("역")
        cache_key = f"subway_arrival:{norm_name}"

        cached_data = await cache_service.get(cache_key)
        if cached_data:
            return ArrivalResponse.model_validate(cached_data)

        response = await self.subway_client.get_arrivals(station_name)
        await cache_service.set(cache_key, response.model_dump(mode="json"))

        return response


    async def get_bus_arrivals(
        self,
        city_code: str,
        station_id: str,
    ) -> ArrivalResponse:
        cache_key = f"bus_arrival:{city_code}:{station_id}"

        cached_data = await cache_service.get(cache_key)
        if cached_data:
            return ArrivalResponse.model_validate(cached_data)

        response = await self.bus_client.get_arrivals(city_code,station_id)
        await cache_service.set(cache_key, response.model_dump(mode="json"))

        return response