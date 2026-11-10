import asyncio
import json
import unittest
from datetime import date, time
from pathlib import Path
from types import SimpleNamespace

from app.clients.odsay_client import OdsayClient
from app.models.route_plan import RoutePlan
from app.models.routine import Routine
from app.models.routine_execution import RoutineExecution
from app.models.routine_notification import RoutineNotification
from app.models.user import User
from app.routers.routines import create_routine
from app.schemas.routine import RoutineCreate
from app.schemas.route import Location, RouteResponse
from app.schemas.arrival import ArrivalItem
from app.services.notification_service import (
    FakeNotificationProvider,
    NotificationService,
)
from app.services.routine_execution_service import RoutineExecutionService
from app.services.schedule_service import ScheduleService


class InMemoryQuery:
    """통합 테스트에서 필요한 조회만 수행하는 간단한 메모리 query입니다."""

    def __init__(self, values: list[object]):
        self.values = values

    def filter(self, *conditions: object) -> "InMemoryQuery":
        # 테스트에서는 실행 기록을 항상 새로 만드는 경로를 사용하므로 조건식은 보관하지 않습니다.
        _ = conditions
        return self

    def first(self) -> object | None:
        return None


class InMemoryDatabase:
    """외부 DB 없이 router와 service 사이의 저장 흐름을 기록합니다."""

    def __init__(self):
        self.added: list[object] = []

    def query(self, model: object) -> InMemoryQuery:
        values = [value for value in self.added if isinstance(value, model)]
        return InMemoryQuery(values)

    def add(self, value: object) -> None:
        # SQLAlchemy default UUID가 DB flush에서 생성되는 부분을 테스트 저장소가 대신 처리합니다.
        if isinstance(value, Routine) and value.routine_id is None:
            value.routine_id = "routine-integration"
            if value.route_plan is not None:
                value.route_plan.routine_id = value.routine_id
        self.added.append(value)

    def flush(self) -> None:
        # 실행 ID가 있어야 알림이 execution과 연결되므로 flush 시 테스트 ID를 부여합니다.
        for value in self.added:
            if isinstance(value, RoutineExecution) and value.execution_id is None:
                value.execution_id = "execution-integration"

    def commit(self) -> None:
        # 메모리 저장소는 이미 객체를 보관했으므로 별도 commit 작업이 필요하지 않습니다.
        return None

    def refresh(self, value: object) -> None:
        # 실제 DB refresh와 달리 메모리 객체는 이미 최신 상태입니다.
        _ = value


class FixtureRouteService:
    """ODsay fixture 경로와 실시간 도착정보 fixture를 제공하는 테스트 client입니다."""

    def __init__(self, route: RouteResponse, fail_on_refresh: bool = False):
        self.route = route
        self.fail_on_refresh = fail_on_refresh
        self.search_include_arrivals: list[bool] = []

    async def search(self, request, *, include_arrivals: bool = True) -> RouteResponse:
        # 루틴 등록 시 실시간 조회 없이 저장 경로만 요청했는지 기록합니다.
        _ = request
        self.search_include_arrivals.append(include_arrivals)
        return self.route.model_copy(deep=True)

    async def refresh_arrivals(self, route: RouteResponse) -> RouteResponse:
        # 실행 실패 시나리오에서는 외부 도착정보 장애를 의도적으로 재현합니다.
        if self.fail_on_refresh:
            raise RuntimeError("fixture arrival provider failure")

        refreshed = route.model_copy(deep=True)
        for segment in refreshed.segments:
            for index, stop in enumerate(segment.stops):
                if segment.transport_type.value == "BUS":
                    refreshed.segments[refreshed.segments.index(segment)].stops[index] = (
                        stop.model_copy(
                            update={
                                "station_id": "fixture-bus-stop",
                                "city_code": "31060",
                                "arrivals": [
                                    ArrivalItem(
                                        transport_type="BUS",
                                        station_or_stop_name=stop.name,
                                        arrival_seconds=120,
                                    )
                                ],
                            }
                        )
                    )
        return refreshed


class EndToEndFlowTest(unittest.TestCase):
    """루틴 등록부터 Fake 알림 성공까지의 핵심 사용자 흐름을 검증합니다."""

    @staticmethod
    def _load_route_fixture() -> RouteResponse:
        # 프로젝트에 이미 있는 ODsay JSON fixture를 실제 parser로 변환합니다.
        fixture_path = Path(__file__).parent / "fixtures" / "odsay_route_response.json"
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        return OdsayClient(SimpleNamespace())._parse_route_response(payload)

    @staticmethod
    def _request() -> RoutineCreate:
        # 좌표를 포함해 루틴 등록 시 RoutePlan이 생성되는 입력을 구성합니다.
        return RoutineCreate(
            name="fixture 출근",
            departure_stop="출발지",
            arrival_stop="도착지",
            scheduled_days=["MON", "TUE", "WED", "THU", "FRI"],
            departure_time=time(8, 0),
            notify_mins_before=10,
            enabled=True,
            origin=Location(
                name="출발지",
                latitude=37.5,
                longitude=126.9,
                city_code="31060",
            ),
            destination=Location(
                name="도착지",
                latitude=37.6,
                longitude=126.95,
                city_code="31060",
            ),
        )

    def test_register_execute_and_send_fake_notification(self):
        # ODsay fixture를 경로 검색 결과로 사용해 외부 네트워크 없는 등록을 검증합니다.
        route = self._load_route_fixture()
        route_service = FixtureRouteService(route)
        database = InMemoryDatabase()
        user = User(
            user_id="user-integration",
            email="integration@example.com",
            name="통합테스트",
            hashed_password="hashed",
            device_token="fake-device-token",
        )

        routine = asyncio.run(
            create_routine(
                self._request(),
                current_user=user,
                db=database,
                route_service=route_service,
            )
        )
        routine.user = user

        # 등록 결과에 ODsay 경로가 RoutePlan으로 저장되었는지 확인합니다.
        self.assertIsNotNone(routine.route_plan)
        self.assertEqual(routine.route_plan.provider, "odsay")
        self.assertEqual(route_service.search_include_arrivals, [False])

        fake_provider = FakeNotificationProvider()
        execution_service = RoutineExecutionService(
            route_service=route_service,
            schedule_service=ScheduleService(),
            notification_service=NotificationService(fake_provider),
        )
        execution = asyncio.run(
            execution_service.refresh(
                routine,
                database,
                execution_date=date(2026, 10, 23),
            )
        )

        # 실행 시 실시간 fixture, 시간 계산, 환승 계산 결과가 저장되었는지 검증합니다.
        notifications = [
            value
            for value in database.added
            if isinstance(value, RoutineNotification)
        ]
        self.assertIsNotNone(execution.estimated_arrival_at)
        self.assertIsNotNone(execution.recommended_departure_at)
        self.assertIsNotNone(execution.calculation_basis)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].status, "PENDING")

        # 생성된 알림을 Fake provider로 전송하고 최종 SENT 상태를 확인합니다.
        sent = asyncio.run(
            execution_service.notification_service.send_pending(
                notifications[0],
                routine,
                database,
            )
        )
        self.assertEqual(sent.status, "SENT")
        self.assertEqual(len(fake_provider.sent), 1)
        self.assertEqual(fake_provider.sent[0]["token"], "fake-device-token")

    def test_external_arrival_failure_does_not_create_execution(self):
        # 실시간 fixture 조회 실패 시 실행 기록을 성공한 것처럼 저장하지 않는지 검증합니다.
        route_service = FixtureRouteService(
            self._load_route_fixture(),
            fail_on_refresh=True,
        )
        database = InMemoryDatabase()
        user = User(
            user_id="user-failure",
            email="failure@example.com",
            name="실패테스트",
            hashed_password="hashed",
            device_token="fake-device-token",
        )
        routine = asyncio.run(
            create_routine(
                self._request(),
                current_user=user,
                db=database,
                route_service=route_service,
            )
        )

        with self.assertRaisesRegex(RuntimeError, "fixture arrival provider failure"):
            asyncio.run(
                RoutineExecutionService(
                    route_service=route_service,
                    notification_service=NotificationService(FakeNotificationProvider()),
                ).refresh(
                    routine,
                    database,
                    execution_date=date(2026, 10, 23),
                )
            )

        self.assertFalse(
            any(isinstance(value, RoutineExecution) for value in database.added)
        )
        self.assertFalse(
            any(isinstance(value, RoutineNotification) for value in database.added)
        )


if __name__ == "__main__":
    unittest.main()
