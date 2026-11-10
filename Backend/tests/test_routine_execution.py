import asyncio
import unittest
from datetime import datetime, time, timezone
from types import SimpleNamespace

import app.main
from app.schemas.arrival import ArrivalItem
from app.schemas.route import RouteResponse, RouteSegment, RouteStop
from app.schemas.transport import TransportType
from app.services.notification_service import NotificationService
from app.services.routine_execution_service import RoutineExecutionService
from app.services.schedule_service import ScheduleService


class FakeRouteService:
    async def refresh_arrivals(self, route):
        return route


class FakeQuery:
    def filter(self, *conditions):
        return self

    def first(self):
        return None


class FakeDatabase:
    def __init__(self):
        self.added = []

    def query(self, model):
        return FakeQuery()

    def add(self, value):
        self.added.append(value)

    def flush(self):
        for value in self.added:
            if getattr(value, "execution_id", None) is None:
                value.execution_id = "execution-test"

    def commit(self):
        pass

    def refresh(self, value):
        pass


class RoutineExecutionTest(unittest.TestCase):
    def _route(self):
        return RouteResponse(
            provider="odsay",
            total_duration_minutes=30,
            transfer_count=1,
            fare=1500,
            segments=[
                RouteSegment(
                    transport_type=TransportType.WALK,
                    duration_minutes=5,
                    stops=[],
                ),
                RouteSegment(
                    transport_type=TransportType.BUS,
                    line_name="17",
                    duration_minutes=15,
                    stops=[
                        RouteStop(
                            name="버스정류장",
                            latitude=37.0,
                            longitude=127.0,
                            odsay_station_id="OD1",
                            station_id="TAGO1",
                            city_code="31060",
                            arrivals=[
                                ArrivalItem(
                                    transport_type=TransportType.BUS,
                                    station_or_stop_name="버스정류장",
                                    arrival_seconds=120,
                                )
                            ],
                        )
                    ],
                )
            ],
        )

    def test_schedule_estimate_uses_walk_and_realtime_wait(self):
        route = self._route()
        routine = SimpleNamespace(departure_time=time(8, 0))
        now = datetime(2026, 10, 5, 7, 50, tzinfo=timezone.utc)

        estimate = ScheduleService().estimate(routine, route, now)

        self.assertEqual(estimate.recommended_departure_at.hour, 7)
        self.assertEqual(estimate.recommended_departure_at.minute, 55)
        self.assertEqual(estimate.estimated_arrival_at.minute, 22)
        self.assertTrue(estimate.transfer_feasible)

    def test_execution_refresh_persists_route_and_notification(self):
        route = self._route()
        routine = SimpleNamespace(
            routine_id="routine-test",
            name="출근",
            departure_time=time(8, 0),
            route_plan=SimpleNamespace(route_data=route.model_dump(mode="json")),
        )
        database = FakeDatabase()
        service = RoutineExecutionService(
            FakeRouteService(),
            ScheduleService(),
            NotificationService(),
        )

        execution = asyncio.run(
            service.refresh(
                routine,
                database,
                execution_date=datetime(2026, 10, 5, tzinfo=timezone.utc).date(),
            )
        )

        notifications = [value for value in database.added if value.__class__.__name__ == "RoutineNotification"]
        self.assertEqual(execution.status, "MONITORING")
        self.assertIsNotNone(execution.estimated_arrival_at)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].status, "PENDING")
