from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import (
	get_current_user,
	get_route_service,
	get_routine_execution_service,
)
from app.models.route_plan import RoutePlan
from app.models.routine import Routine
from app.models.routine_execution import RoutineExecution
from app.models.routine_notification import RoutineNotification
from app.models.user import User
from app.schemas.routine import (
	RoutineCreate,
	RoutineExecutionResponse,
	RoutineResponse,
	RoutineUpdate,
)
from app.schemas.route import RouteSearchRequest
from app.services.route_service import RouteService
from app.services.routine_execution_service import RoutineExecutionService
from app.services.notification_service import NotificationDeliveryError
from app.clients.http_client import ExternalApiError


# 모든 루틴 API에 공통 URL prefix와 Swagger 태그를 적용합니다.
router = APIRouter(prefix="/api/v1/routines", tags=["routines"])


# 로그인한 사용자의 새 루틴을 생성합니다.
@router.post("", response_model=RoutineResponse, status_code=status.HTTP_201_CREATED)
async def create_routine(
	routine_in: RoutineCreate,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
    route_service: RouteService = Depends(get_route_service),
) -> Routine:
	# 동일 사용자의 루틴 이름 중복 검증
	existing = (
		db.query(Routine)
		.filter(
			Routine.user_id == current_user.user_id,
			Routine.name == routine_in.name,
		)
		.first()
	)
	if existing is not None:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="이미 동일한 이름의 루틴이 존재합니다.",
		)

	# 좌표가 있는 요청은 저장 전에 기본 경로 계획을 계산합니다.
	route_response = await _build_route_plan(routine_in, route_service)
	if route_response is not None:
		route_response = _select_route_with_alternatives(
			route_response,
			routine_in.selected_route_index,
		)

	# user_id는 요청값이 아니라 인증된 사용자에서 가져와 소유자를 고정합니다.
	routine = Routine(user_id=current_user.user_id)
	_apply_routine_attributes(routine, routine_in)

	if route_response is not None:
		routine.route_plan = _to_route_plan(route_response)

	db.add(routine)
	db.commit()
	db.refresh(routine)
	return routine


# 로그인한 사용자가 소유한 루틴 목록만 조회합니다.
@router.get("", response_model=list[RoutineResponse])
def read_routines(
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
) -> list[Routine]:
	# 현재 사용자 ID로 필터링해 다른 사용자의 루틴이 노출되지 않도록 합니다.
	return (
		db.query(Routine)
		.filter(Routine.user_id == current_user.user_id)
		.all()
	)


# 로그인한 사용자의 특정 루틴을 조회합니다.
@router.get("/{routine_id}", response_model=RoutineResponse)
def read_routine(
	routine_id: str,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
) -> Routine:
	# 루틴 ID와 사용자 ID를 함께 확인해 소유권을 검증합니다.
	routine = _get_owned_routine(routine_id, current_user, db)
	return routine


# 로그인한 사용자의 특정 루틴을 전체 수정합니다.
@router.put("/{routine_id}", response_model=RoutineResponse)
async def update_routine(
	routine_id: str,
	routine_in: RoutineUpdate,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
    route_service: RouteService = Depends(get_route_service),
) -> Routine:
	# 본인 소유 루틴이 아니거나 존재하지 않으면 404 예외가 발생합니다.
	routine = _get_owned_routine(routine_id, current_user, db)

	# 다른 루틴과의 이름 중복 검증
	existing = (
		db.query(Routine)
		.filter(
			Routine.user_id == current_user.user_id,
			Routine.name == routine_in.name,
			Routine.routine_id != routine_id,
		)
		.first()
	)
	if existing is not None:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="이미 동일한 이름의 루틴이 존재합니다.",
		)
	_apply_routine_attributes(routine, routine_in)

	route_response = await _build_route_plan(routine_in, route_service)
	if route_response is None:
		routine.route_plan = None
	else:
		route_response = _select_route_with_alternatives(
			route_response,
			routine_in.selected_route_index,
		)
		if routine.route_plan is None:
			routine.route_plan = _to_route_plan(route_response)
		else:
			routine.route_plan.provider = route_response.provider
			routine.route_plan.total_duration_minutes = route_response.total_duration_minutes
			routine.route_plan.transfer_count = route_response.transfer_count
			routine.route_plan.fare = route_response.fare
			routine.route_plan.route_data = route_response.model_dump(mode="json")
			routine.route_plan.updated_at = datetime.now(timezone.utc)

	db.commit()
	db.refresh(routine)
	return routine


def _apply_routine_attributes(routine: Routine, routine_in: RoutineCreate | RoutineUpdate) -> None:
	routine.name = routine_in.name
	routine.departure_stop = routine_in.departure_stop
	routine.arrival_stop = routine_in.arrival_stop
	routine.departure_latitude = routine_in.origin.latitude if routine_in.origin else None
	routine.departure_longitude = routine_in.origin.longitude if routine_in.origin else None
	routine.departure_city_code = routine_in.origin.city_code if routine_in.origin else None
	routine.arrival_latitude = routine_in.destination.latitude if routine_in.destination else None
	routine.arrival_longitude = routine_in.destination.longitude if routine_in.destination else None
	routine.arrival_city_code = routine_in.destination.city_code if routine_in.destination else None
	routine.scheduled_days = routine_in.scheduled_days
	routine.departure_time = routine_in.departure_time
	routine.notify_mins_before = routine_in.notify_mins_before
	routine.enabled = routine_in.enabled
	routine.exclude_holidays = routine_in.exclude_holidays


async def _build_route_plan(
	routine_in: RoutineCreate | RoutineUpdate,
	route_service: RouteService,
):
	# 기존 좌표 없는 루틴도 사용할 수 있도록 경로 계획 생성을 선택적으로 처리합니다.
	if routine_in.origin is None or routine_in.destination is None:
		return None
	return await route_service.search(
		RouteSearchRequest(
			origin=routine_in.origin,
			destination=routine_in.destination,
		),
		include_arrivals=False,
	)


def _select_route_with_alternatives(route_response, selected_index: int):
	"""Keep the selected route primary while preserving all search alternatives."""
	all_routes = [route_response, *route_response.alternatives]
	if selected_index < 0 or selected_index >= len(all_routes):
		selected_index = 0
	selected = all_routes[selected_index]
	return selected.model_copy(
		update={
			"alternatives": [
				route for index, route in enumerate(all_routes) if index != selected_index
			]
		}
	)


def _to_route_plan(route_response) -> RoutePlan:
	# Pydantic 경로 응답을 DB JSON과 요약 필드로 변환합니다.
	now = datetime.now(timezone.utc)
	return RoutePlan(
		provider=route_response.provider,
		total_duration_minutes=route_response.total_duration_minutes,
		transfer_count=route_response.transfer_count,
		fare=route_response.fare,
		route_data=route_response.model_dump(mode="json"),
		created_at=now,
		updated_at=now,
	)


# 로그인한 사용자의 특정 루틴을 삭제합니다.
@router.delete("/{routine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_routine(
	routine_id: str,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
) -> Response:
	# 소유권이 확인된 루틴만 삭제할 수 있습니다.
	routine = _get_owned_routine(routine_id, current_user, db)
	db.delete(routine)
	db.commit()
	# 삭제 성공 시 응답 본문 없이 204 상태 코드를 반환합니다.
	return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{routine_id}/execute", response_model=RoutineExecutionResponse)
async def execute_routine(
	routine_id: str,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
	execution_service: RoutineExecutionService = Depends(get_routine_execution_service),
) -> RoutineExecution:
	# 저장된 경로를 현재 실시간 도착정보로 갱신하는 수동 실행 진입점입니다.
	routine = _get_owned_routine(routine_id, current_user, db)
	return await execution_service.refresh(routine, db)


@router.post("/{routine_id}/test-notification")
async def send_test_notification(
	routine_id: str,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db),
	execution_service: RoutineExecutionService = Depends(get_routine_execution_service),
):
	routine = _get_owned_routine(routine_id, current_user, db)
	if not current_user.device_token:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="등록된 기기 토큰이 없습니다. 앱을 다시 실행해 주세요.",
		)
	if not current_user.notifications_enabled:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="알림 설정이 꺼져 있습니다.",
		)

	try:
		execution = await execution_service.refresh(routine, db)
		notification = (
			db.query(RoutineNotification)
			.filter(RoutineNotification.execution_id == execution.execution_id)
			.order_by(RoutineNotification.created_at.desc())
			.first()
		)
		if notification is None:
			raise NotificationDeliveryError("테스트 알림을 생성하지 못했습니다.")
		await execution_service.notification_service.send_pending(
			notification, routine, db
		)
		if notification.status != "SENT":
			raise NotificationDeliveryError(
				notification.last_error or "테스트 알림 발송에 실패했습니다."
			)
	except NotificationDeliveryError as exc:
		raise HTTPException(
			status_code=status.HTTP_502_BAD_GATEWAY,
			detail=str(exc),
		) from exc
	except ValueError as exc:
		raise HTTPException(
			status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
			detail=str(exc),
		) from exc
	except ExternalApiError as exc:
		raise HTTPException(
			status_code=status.HTTP_502_BAD_GATEWAY,
			detail=exc.message,
		) from exc

	return {"message": f"'{routine.name}' 루틴 알림을 발송했습니다."}


# 루틴을 조회하면서 현재 사용자의 소유권까지 공통으로 확인합니다.
def _get_owned_routine(
	routine_id: str,
	current_user: User,
	db: Session,
) -> Routine:
	# routine_id와 user_id가 모두 일치하는 루틴만 검색합니다.
	routine = (
		db.query(Routine)
		.filter(
			Routine.routine_id == routine_id,
			Routine.user_id == current_user.user_id,
		)
		.first()
	)
	if routine is None:
		# 다른 사용자의 루틴도 존재 여부를 노출하지 않고 404로 처리합니다.
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="루틴을 찾을 수 없습니다.",
		)
	return routine
