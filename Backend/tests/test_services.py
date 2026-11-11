import asyncio
from datetime import date, datetime, time, timezone
from types import SimpleNamespace
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock

from app.clients.bus_client import BusClient
from app.clients.subway_client import SubwayClient
from app.core.redis_service import CacheService
from app.models.routine_notification import RoutineNotification
from app.models import routine as _routine_model  # noqa: F401
from app.models import user as _user_model  # noqa: F401
from app.models import route_plan as _route_plan_model  # noqa: F401
from app.models import routine_execution as _execution_model  # noqa: F401
from app.repositories.bus_stop_repository import BusStopRepository
from app.schemas.arrival import ArrivalItem, ArrivalResponse
from app.schemas.route import RouteResponse, RouteSegment, RouteStop
from app.schemas.transport import TransportType
from app.services.arrival_service import ArrivalService
from app.services.holiday_service import HolidayService
from app.services.notification_service import (
    FakeNotificationProvider,
    NotificationService,
)
from app.services.schedule_service import ScheduleService


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

        res1 = await self.service.get_subway_arrivals("강남역")
        self.assertEqual(len(res1.items), 1)
        self.assertEqual(res1.items[0].line_name, "2호선")
        self.assertEqual(self.subway_client.get_arrivals.call_count, 1)

        res2 = await self.service.get_subway_arrivals("강남역")
        self.assertEqual(len(res2.items), 1)
        self.assertEqual(res2.items[0].line_name, "2호선")
        self.assertEqual(self.subway_client.get_arrivals.call_count, 1)

    async def test_arrival_service_fault_tolerance(self):
        self.subway_client.get_arrivals.return_value = self.mock_subway_response
        await self.service.get_subway_arrivals("판교")

        self.subway_client.get_arrivals.side_effect = RuntimeError("OpenAPI Server Error")

        res = await self.service.get_subway_arrivals("판교")
        self.assertEqual(len(res.items), 1)
        self.assertEqual(res.items[0].station_or_stop_name, "강남")


class HolidayServiceTest(unittest.TestCase):
    def test_fixed_solar_holidays(self):
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 1, 1)))
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 3, 1)))
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 5, 5)))
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 6, 6)))
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 8, 15)))
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 10, 3)))
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 10, 9)))
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 12, 25)))

    def test_lunar_variable_holidays(self):
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 2, 16)))
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 2, 17)))
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 2, 18)))
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 9, 24)))
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 9, 25)))
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 9, 26)))

    def test_substitute_holiday_calculation(self):
        self.assertTrue(HolidayService.is_public_holiday(date(2024, 2, 12)))
        self.assertTrue(HolidayService.is_public_holiday(date(2025, 5, 6)))

    def test_regular_workday_returns_false(self):
        self.assertFalse(HolidayService.is_public_holiday(date(2026, 3, 10)))
        self.assertFalse(HolidayService.is_public_holiday(date(2026, 7, 15)))


class NotificationAndScheduleTest(unittest.TestCase):
    def _route(self):
        return RouteResponse(
            provider="fixture",
            total_duration_minutes=20,
            transfer_count=1,
            segments=[
                RouteSegment(
                    transport_type=TransportType.BUS,
                    line_name="17",
                    duration_minutes=10,
                    stops=[RouteStop(
                        name="첫 정류장", latitude=37, longitude=127, odsay_station_id="1",
                        arrivals=[ArrivalItem(
                            transport_type=TransportType.BUS,
                            station_or_stop_name="첫 정류장",
                            arrival_seconds=30,
                        )],
                    )],
                ),
                RouteSegment(
                    transport_type=TransportType.SUBWAY,
                    line_name="1호선",
                    duration_minutes=10,
                    stops=[RouteStop(
                        name="환승역", latitude=37, longitude=127, odsay_station_id="2",
                        arrivals=[ArrivalItem(
                            transport_type=TransportType.SUBWAY,
                            station_or_stop_name="환승역",
                            arrival_seconds=800,
                        )],
                    )],
                ),
            ],
        )

    def test_schedule_provider_and_transfer_details(self):
        estimate = ScheduleService().estimate(
            SimpleNamespace(departure_time=time(8, 0)),
            self._route(),
            datetime(2026, 10, 5, 7, 50, tzinfo=timezone.utc),
        )
        self.assertFalse(estimate.calculation_basis["schedule_data_available"])
        self.assertEqual(
            estimate.calculation_basis["fallback"],
            "odsay_duration_and_realtime_arrival",
        )
        self.assertEqual(estimate.transfer_details[0]["transfer_station"], "환승역")
        self.assertTrue(estimate.transfer_feasible)

    def test_fake_provider_success_and_failure_are_recorded(self):
        success = FakeNotificationProvider()
        service = NotificationService(success)
        notification = RoutineNotification(
            routine_id="r", execution_id="e", title="title", message="message",
            status="PENDING", created_at=datetime.now(timezone.utc),
        )
        db = SimpleNamespace(commit=lambda: None)
        routine = SimpleNamespace(user=SimpleNamespace(device_token="token"))
        asyncio.run(service.send_pending(notification, routine, db))
        self.assertEqual(notification.status, "SENT")

        failed = RoutineNotification(
            routine_id="r", execution_id="e2", title="title", message="message",
            status="PENDING", created_at=datetime.now(timezone.utc),
        )
        asyncio.run(NotificationService(FakeNotificationProvider(fail=True)).send_pending(
            failed, routine, db,
        ))
        self.assertEqual(failed.status, "FAILED")
        self.assertIn("failure", failed.last_error)
        self.assertIsNone(failed.sent_at)

    def test_build_realtime_status_message_uses_only_first_transit_segment(self):
        route = RouteResponse(
            provider="fixture",
            total_duration_minutes=30,
            transfer_count=1,
            segments=[
                RouteSegment(
                    transport_type=TransportType.BUS,
                    line_name="17",
                    duration_minutes=15,
                    stops=[RouteStop(
                        name="출발정류장", latitude=37, longitude=127, odsay_station_id="1",
                        arrivals=[ArrivalItem(
                            transport_type=TransportType.BUS,
                            station_or_stop_name="출발정류장",
                            arrival_seconds=600,
                        )],
                    )],
                ),
                RouteSegment(
                    transport_type=TransportType.SUBWAY,
                    line_name="수인분당선",
                    duration_minutes=15,
                    stops=[RouteStop(
                        name="환승역", latitude=37, longitude=127, odsay_station_id="2",
                        arrivals=[ArrivalItem(
                            transport_type=TransportType.SUBWAY,
                            station_or_stop_name="환승역",
                            arrival_seconds=30,
                        )],
                    )],
                ),
            ],
        )
        routine = SimpleNamespace(name="등교 루틴")
        execution = SimpleNamespace(route_data=route.model_dump(mode="json"))

        title, message = NotificationService.build_realtime_status_message(routine, execution)
        self.assertEqual(title, "등교 루틴")
        self.assertIn("17번", message)
        self.assertNotIn("수인분당선", message)


class BusStopRepositoryTest(unittest.TestCase):
    def test_loads_cp949_and_preserves_tago_fields(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "stops.csv"
            path.write_bytes(
                "정류장번호,정류장명,위도,경도,정보수집일,모바일단축번호,도시코드,도시명,관리도시명\n"
                "GGB1,철산역,37.4758667,126.8679667,2025-10-31,1,31060,경기도 광명시,광명BIS\n".encode("cp949")
            )
            stop = BusStopRepository(path).find_by_name(" 철산역 ", "31060")[0]
            self.assertEqual(stop.station_id, "GGB1")
            self.assertEqual(stop.city_code, "31060")
            self.assertEqual(stop.city_name, "경기도 광명시")
