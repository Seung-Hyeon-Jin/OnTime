from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.clients.http_client import ExternalApiError
from app.models.routine import Routine
from app.models.routine_execution import RoutineExecution
from app.schemas.route import RouteResponse
from app.services.notification_service import NotificationService
from app.services.route_service import RouteService
from app.services.schedule_service import ScheduleService


class RoutineExecutionService:
    def __init__(
        self,
        route_service: RouteService,
        schedule_service: ScheduleService | None = None,
        notification_service: NotificationService | None = None,
    ):
        self.route_service = route_service
        self.schedule_service = schedule_service or ScheduleService()
        self.notification_service = notification_service or NotificationService()

    async def refresh(
        self,
        routine: Routine,
        db: Session,
        execution_date: date | None = None,
    ) -> RoutineExecution:
        # 등록 시 저장한 경로를 복원해 실행 시점의 실시간 정보만 새로 조회합니다.
        if routine.route_plan is None:
            raise ValueError("저장된 경로 계획이 없는 루틴은 실행할 수 없습니다.")

        route = RouteResponse.model_validate(routine.route_plan.route_data)
        try:
            refreshed_route = await self.route_service.refresh_arrivals(route)
        except (ExternalApiError, ValueError):
            # 실시간 provider가 실패해도 저장된 경로로 알림을 발송할 수 있습니다.
            refreshed_route = route
        checked_at = datetime.now().astimezone()
        estimate = self.schedule_service.estimate(routine, refreshed_route, checked_at)
        today = execution_date or datetime.now(timezone.utc).date()
        execution = (
            db.query(RoutineExecution)
            .filter(
                RoutineExecution.routine_id == routine.routine_id,
                RoutineExecution.execution_date == today,
            )
            .first()
        )
        if execution is None:
            # 하루에 하나의 실행 기록만 만들어 중복 갱신을 한 곳에서 관리합니다.
            execution = RoutineExecution(
                routine_id=routine.routine_id,
                execution_date=today,
                status="MONITORING",
                route_data=refreshed_route.model_dump(mode="json"),
                last_checked_at=checked_at,
                recommended_departure_at=estimate.recommended_departure_at,
                estimated_arrival_at=estimate.estimated_arrival_at,
                transfer_feasible=estimate.transfer_feasible,
                transfer_details=estimate.transfer_details,
                calculation_basis=estimate.calculation_basis,
            )
            db.add(execution)
        else:
            # 같은 날 다시 호출하면 최신 도착정보와 확인 시각만 갱신합니다.
            execution.status = "MONITORING"
            execution.route_data = refreshed_route.model_dump(mode="json")
            execution.last_checked_at = checked_at
            execution.recommended_departure_at = estimate.recommended_departure_at
            execution.estimated_arrival_at = estimate.estimated_arrival_at
            execution.transfer_feasible = estimate.transfer_feasible
            execution.transfer_details = estimate.transfer_details
            execution.calculation_basis = estimate.calculation_basis

        # 새 실행 ID가 생성된 뒤 알림 outbox에 한 건을 등록합니다.
        db.flush()
        self.notification_service.enqueue_departure(routine, execution, estimate, db)
        db.commit()
        db.refresh(execution)
        return execution