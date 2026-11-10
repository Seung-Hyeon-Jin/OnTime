import asyncio
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from app.clients.bus_client import BusClient
from app.clients.subway_client import SubwayClient
from app.core.redis_service import CacheService
from app.schemas.arrival import ArrivalItem, ArrivalResponse
from app.schemas.transport import TransportType
from app.services.arrival_service import ArrivalService


class ArrivalCacheTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.subway_client = AsyncMock(spec=SubwayClient)
        self.bus_client = AsyncMock(spec=BusClient)
        self.service = ArrivalService(
            subway_client=self.subway_client,
            bus_client=self.bus_client,
        )

        self.mock_subway_response = ArrivalResponse(
            provider="seoul-subway",
            queried_at=datetime.now(timezone.utc),
            items=[
                ArrivalItem(
                    transport_type=TransportType.SUBWAY,
                    station_or_stop_name="강남",
                    line_name="2호선",
                    direction="성수방면",
                    arrival_seconds=120,
                    arrival_message="2분 후",
                )
            ],
        )

    async def test_cache_service_in_memory_fallback(self):
        cache = CacheService()
        await cache.set("test_key", {"foo": "bar"}, ttl=5)
        res = await cache.get("test_key")
        self.assertIsNotNone(res)
        self.assertEqual(res["foo"], "bar")

    async def test_arrival_service_uses_cache_on_second_call(self):
        self.subway_client.get_arrivals.return_value = self.mock_subway_response

        # 1회차 호출 -> mock subway_client 호출됨
        res1 = await self.service.get_subway_arrivals("강남역")
        self.assertEqual(len(res1.items), 1)
        self.assertEqual(res1.items[0].line_name, "2호선")
        self.assertEqual(self.subway_client.get_arrivals.call_count, 1)

        # 2회차 호출 -> mock subway_client 호출되지 않고 캐시 데이터 반환 (Cache Hit)
        res2 = await self.service.get_subway_arrivals("강남역")
        self.assertEqual(len(res2.items), 1)
        self.assertEqual(res2.items[0].line_name, "2호선")
        self.assertEqual(self.subway_client.get_arrivals.call_count, 1)

    async def test_arrival_service_fault_tolerance(self):
        # API 장애가 발생하더라도 캐시 데이터를 대신 반환하는지 테스트
        self.subway_client.get_arrivals.return_value = self.mock_subway_response
        await self.service.get_subway_arrivals("판교")

        # 이제 mock이 Exception을 발생시키도록 설정
        self.subway_client.get_arrivals.side_effect = RuntimeError("OpenAPI Server Error")

        # 캐시가 존재하므로 RuntimeError가 밖으로 안 던져지고 캐시 데이터 복원 반환
        res = await self.service.get_subway_arrivals("판교")
        self.assertEqual(len(res.items), 1)
        self.assertEqual(res.items[0].station_or_stop_name, "강남")


if __name__ == "__main__":
    unittest.main()
