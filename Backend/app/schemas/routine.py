from pydantic import BaseModel, ConfigDict
from datetime import date, datetime, time

from app.schemas.route import Location, RouteResponse

# 루틴 생성 및 수정 요청을 검증할 스키마
class RoutineBase(BaseModel):
    name: str
    departure_stop: str
    arrival_stop: str
    scheduled_days: list[str]  # 예: ["MON", "TUE", "WED", "THU", "FRI"]
    departure_time: time
    notify_mins_before: int
    enabled: bool = True
    exclude_holidays: bool = False
    origin: Location | None = None
    destination: Location | None = None
    selected_route_index: int = 0

class RoutineCreate(RoutineBase):
    pass

class RoutineUpdate(RoutineBase):
    pass



class RoutineResponse(RoutineBase):
    routine_id: str
    user_id: str
    route_plan: "RoutePlanResponse | None" = None

    model_config = ConfigDict(from_attributes=True)


class RoutePlanResponse(BaseModel):
    route_plan_id: str
    routine_id: str
    provider: str
    total_duration_minutes: int
    transfer_count: int
    fare: int | None
    route: RouteResponse

    model_config = ConfigDict(from_attributes=True)


class RoutineExecutionResponse(BaseModel):
    execution_id: str
    routine_id: str
    execution_date: date
    status: str
    route: RouteResponse
    last_checked_at: datetime
    recommended_departure_at: datetime | None
    estimated_arrival_at: datetime | None
    transfer_feasible: bool | None
    transfer_details: list[dict] | None = None
    calculation_basis: dict | None = None

    model_config = ConfigDict(from_attributes=True)