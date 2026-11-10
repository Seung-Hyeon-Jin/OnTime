import asyncio
import unittest
from datetime import datetime, time, timezone
from types import SimpleNamespace

from app.models.routine_notification import RoutineNotification
from app.models import routine as _routine_model  # noqa: F401
from app.models import user as _user_model  # noqa: F401
from app.models import route_plan as _route_plan_model  # noqa: F401
from app.models import routine_execution as _execution_model  # noqa: F401
from app.schemas.arrival import ArrivalItem
from app.schemas.route import RouteResponse, RouteSegment, RouteStop
from app.schemas.transport import TransportType
from app.services.notification_service import (
    FakeNotificationProvider,
    NotificationDeliveryError,
    NotificationService,
)
from app.services.schedule_service import ScheduleService


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
