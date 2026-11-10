from dataclasses import dataclass
from datetime import datetime, timedelta

from app.models.routine import Routine
from app.schemas.route import RouteResponse


@dataclass(frozen=True)
class ScheduleEntry:
    service_date_type: str
    first_departure: str | None = None
    last_departure: str | None = None
    interval_seconds: int | None = None


class EmptyScheduleProvider:
    """시간표 저장소가 연결되지 않은 상태를 명시적으로 나타내는 fallback입니다."""

    reason = "schedule_data_unconfigured"

    def get(self, *, transport_type: str, line_name: str | None, at: datetime) -> ScheduleEntry | None:
        _ = (transport_type, line_name, at)
        return None


@dataclass(frozen=True)
class TimingEstimate:
    recommended_departure_at: datetime
    estimated_arrival_at: datetime
    transfer_feasible: bool
    transfer_details: list[dict]
    calculation_basis: dict


class ScheduleService:
    def __init__(
        self,
        transfer_buffer_seconds: int = 30,
    ):
        self.provider = EmptyScheduleProvider()
        self.transfer_buffer_seconds = transfer_buffer_seconds

    def estimate(self, routine: Routine, route: RouteResponse, now: datetime) -> TimingEstimate:
        first_walk_minutes = self._first_walk_minutes(route)
        schedule_entry = self._first_schedule_entry(route, now)
        first_wait_seconds = (
            schedule_entry.interval_seconds
            if schedule_entry and schedule_entry.interval_seconds is not None
            else self._first_wait_seconds(route)
        )
        scheduled_departure = now.replace(
            hour=routine.departure_time.hour,
            minute=routine.departure_time.minute,
            second=0,
            microsecond=0,
        )
        recommended_departure = scheduled_departure - timedelta(minutes=first_walk_minutes)
        transfer_details = self._transfers(route, now, first_wait_seconds)
        estimated_arrival = now + timedelta(
            seconds=first_wait_seconds + sum(item["walking_seconds"] for item in transfer_details)
        ) + timedelta(minutes=route.total_duration_minutes)
        return TimingEstimate(
            recommended_departure_at=recommended_departure,
            estimated_arrival_at=estimated_arrival,
            transfer_feasible=all(item["transfer_feasible"] for item in transfer_details),
            transfer_details=transfer_details,
            calculation_basis={
                "calculated_at": now.isoformat(),
                "transfer_buffer_seconds": self.transfer_buffer_seconds,
                "schedule_data_available": schedule_entry is not None,
                "schedule_date_type": schedule_entry.service_date_type if schedule_entry else None,
                "schedule_provider_status": getattr(self.provider, "reason", "available"),
                "fallback": None if schedule_entry else "odsay_duration_and_realtime_arrival",
            },
        )

    def _first_schedule_entry(self, route: RouteResponse, now: datetime) -> ScheduleEntry | None:
        for segment in route.segments:
            if segment.transport_type.value in {"BUS", "SUBWAY"}:
                return self.provider.get(
                    transport_type=segment.transport_type.value,
                    line_name=segment.line_name,
                    at=now,
                )
        return None

    def _transfers(self, route: RouteResponse, now: datetime, first_wait_seconds: int) -> list[dict]:
        details: list[dict] = []
        elapsed = first_wait_seconds
        transit_seen = False
        previous_transport = None
        last_transit_index: int | None = None
        for index, segment in enumerate(route.segments):
            is_transit = segment.transport_type.value in {"BUS", "SUBWAY"}
            if is_transit and transit_seen and segment.stops:
                station = segment.stops[0]
                walking_seconds = sum(
                    route.segments[position].duration_minutes * 60
                    for position in range((last_transit_index or 0) + 1, index)
                    if route.segments[position].transport_type.value == "WALK"
                )
                arrivals = sorted(
                    item.arrival_seconds for item in station.arrivals
                    if item.arrival_seconds is not None
                )
                ready_at = elapsed + self.transfer_buffer_seconds + walking_seconds
                next_arrival = next((value for value in arrivals if value >= ready_at), None)
                missed = bool(arrivals) and next_arrival is None
                details.append({
                    "transfer_station": station.name,
                    "previous_arrival_at": (now + timedelta(seconds=elapsed)).isoformat(),
                    "walking_seconds": walking_seconds,
                    "next_vehicle_arrival_at": (
                        (now + timedelta(seconds=next_arrival)).isoformat()
                        if next_arrival is not None else None
                    ),
                    "waiting_seconds": (
                        next_arrival - elapsed if next_arrival is not None else None
                    ),
                    "transfer_feasible": not missed and (not arrivals or next_arrival >= ready_at),
                    "previous_transport": previous_transport,
                    "next_transport": segment.transport_type.value,
                })
            if is_transit:
                transit_seen = True
                previous_transport = segment.transport_type.value
                last_transit_index = index
            elapsed += segment.duration_minutes * 60
        return details

    @staticmethod
    def _first_walk_minutes(route: RouteResponse) -> int:
        if route.segments and route.segments[0].transport_type.value == "WALK":
            return route.segments[0].duration_minutes
        return 0

    @staticmethod
    def _first_wait_seconds(route: RouteResponse) -> int:
        for segment in route.segments:
            if segment.transport_type.value not in {"BUS", "SUBWAY"} or not segment.stops:
                continue
            seconds = [
                item.arrival_seconds for item in segment.stops[0].arrivals
                if item.arrival_seconds is not None
            ]
            if seconds:
                return max(0, min(seconds))
        return 0
