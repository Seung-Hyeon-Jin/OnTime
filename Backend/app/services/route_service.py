import asyncio
import re

from app.clients.odsay_client import OdsayClient
from app.clients.bus_client import BusClient
from app.clients.subway_client import SubwayClient
from app.schemas.route import RouteResponse, RouteSearchRequest, RouteStop
from app.services.route_matching_service import RouteMatchingError, RouteStopMatcher

class RouteService:
    def __init__(
        self,
        odsay_client: OdsayClient,
        matcher: RouteStopMatcher,
        bus_client: BusClient,
        subway_client: SubwayClient | None = None,
        arrival_limit: int = 4,
        subway_arrival_limit: int = 2,
    ):
        self.odsay_client = odsay_client
        self.matcher = matcher
        self.bus_client = bus_client
        self.subway_client = subway_client
        self.arrival_limit = arrival_limit
        self.subway_arrival_limit = subway_arrival_limit

    async def search(
            self,
            request: RouteSearchRequest,
            *,
            include_arrivals: bool = True,
    ) -> RouteResponse:
        response = await self.odsay_client.search_routes(
            origin=request.origin,
            destination=request.destination
        )
        arrival_candidates: list[RouteStop] = []
        for segment in response.segments:
            if segment.transport_type.value != "BUS":
                continue
            for index, stop in enumerate(segment.stops):
                try:
                    candidate = self.matcher.match(stop, request.origin.city_code)
                    matched = stop.model_copy(
                        update={
                            "station_id": candidate.station_id,
                            "city_code": candidate.city_code,
                            "city_name": candidate.city_name,
                        }
                    )
                    segment.stops[index] = matched
                    if index in (0, len(segment.stops) - 1):
                        if matched.station_id not in {item.station_id for item in arrival_candidates}:
                            arrival_candidates.append(matched)
                except RouteMatchingError:
                    pass

        if not include_arrivals:
            return response

        return await self.refresh_arrivals(response, arrival_candidates)

    async def refresh_arrivals(
        self,
        response: RouteResponse,
        bus_candidates: list[RouteStop] | None = None,
    ) -> RouteResponse:
        refreshed_route = await self._refresh_route_arrivals(response)
        refreshed_alternatives = await asyncio.gather(
            *(
                self._refresh_route_arrivals(alternative)
                for alternative in response.alternatives
            )
        )
        # 실시간 갱신은 저장된 메인 경로를 유지해야 합니다.
        # 대안 경로가 더 짧더라도 사용자가 선택한 루틴의 지정 노선을
        # 다른 경로로 승격시키지 않습니다.
        return refreshed_route.model_copy(update={
            "alternatives": list(refreshed_alternatives),
        })

    async def _refresh_route_arrivals(self, response: RouteResponse) -> RouteResponse:
        for segment in response.segments:
            if segment.transport_type.value == "BUS":
                for index, stop in enumerate(segment.stops):
                    if not stop.station_id or stop.station_id.startswith("SEB"):
                        try:
                            candidate = self.matcher.match(stop, stop.city_code)
                            segment.stops[index] = stop.model_copy(
                                update={
                                    "station_id": candidate.station_id,
                                    "city_code": candidate.city_code,
                                    "city_name": candidate.city_name,
                                }
                            )
                        except RouteMatchingError:
                            pass

        # 매칭으로 갱신된 response.segments에서 버스 정류장 후보를 새로 수집합니다.
        bus_candidates = (
            self._collect_first_bus_candidate(response)
            if self._first_transit_type(response) == "BUS"
            else []
        )
        selected_bus_stops = bus_candidates[: self.arrival_limit]
        allowed_bus_lines = self.same_destination_bus_lines(response)
        destination_stop = self._first_bus_arrival_name(response)
        subway_segments = [
            segment
            for segment in response.segments
            if segment.transport_type.value == "SUBWAY"
            and segment.stops
            and segment.departure_stop != segment.arrival_stop
        ][: self.subway_arrival_limit]

        bus_arrivals, subway_arrivals = await asyncio.gather(
            asyncio.gather(
                *(
                    self._get_arrivals(
                        stop,
                        allowed_lines=allowed_bus_lines,
                        destination_name=destination_stop,
                    )
                    for stop in selected_bus_stops
                )
            ),
            asyncio.gather(
                *(
                    self._get_subway_arrivals(
                        segment.stops[0],
                        segment.line_name,
                        arrival_stop_name=segment.arrival_stop or (segment.stops[-1].name if segment.stops else None),
                        segment_stops=segment.stops,
                    )
                    for segment in subway_segments
                )
            ),
        )
        arrivals_by_station = {station_id: value for station_id, value in bus_arrivals}
        arrivals_by_subway = {
            (station_name, line_name): value
            for station_name, line_name, value in subway_arrivals
        }

        for segment in response.segments:
            for index, stop in enumerate(segment.stops):
                if stop.station_id in arrivals_by_station:
                    segment.stops[index] = stop.model_copy(update=arrivals_by_station[stop.station_id])
            if (
                segment.transport_type.value == "SUBWAY"
                and segment.stops
                and segment.departure_stop != segment.arrival_stop
            ):
                subway_key = (
                    self._subway_lookup_name(segment.stops[0].name),
                    segment.line_name,
                )
                if subway_key in arrivals_by_subway:
                    segment.stops[0] = segment.stops[0].model_copy(
                        update=arrivals_by_subway[subway_key]
                    )
        return response

    @staticmethod
    def _first_transit_type(response: RouteResponse) -> str:
        for segment in response.segments:
            if segment.transport_type.value in {"BUS", "SUBWAY"}:
                return segment.transport_type.value
        return "WALK"

    @staticmethod
    def _first_bus_segment(response: RouteResponse):
        for segment in response.segments:
            if segment.transport_type.value == "BUS":
                return segment
        return None

    @staticmethod
    def _first_bus_arrival_name(response: RouteResponse) -> str | None:
        segment = RouteService._first_bus_segment(response)
        if segment is None:
            return None
        if segment.arrival_stop and segment.arrival_stop.strip():
            return segment.arrival_stop
        if segment.stops:
            return segment.stops[-1].name
        return None

    @staticmethod
    def _get_base_bus_number(line_name: str | None) -> str:
        if not line_name:
            return ""
        normalized = RouteService._normalize_bus_line(line_name)
        match = re.match(r'^([A-Za-z]*\d+)', normalized)
        if match:
            return match.group(1)
        return normalized

    @staticmethod
    def filter_bus_arrivals(
        arrivals: list,
        allowed_lines: set[str] | None = None,
    ) -> list:
        if not arrivals:
            return []
        if allowed_lines:
            lines_to_keep = {RouteService._normalize_bus_line(l) for l in allowed_lines}
            base_lines_to_keep = {RouteService._get_base_bus_number(l) for l in allowed_lines if l}

            filtered = [
                item
                for item in arrivals
                if item.line_name
                and (
                    RouteService._normalize_bus_line(item.line_name) in lines_to_keep
                    or RouteService._get_base_bus_number(item.line_name) in base_lines_to_keep
                )
            ]
            if filtered:
                filtered.sort(
                    key=lambda item: (
                        item.arrival_seconds is None,
                        item.arrival_seconds if item.arrival_seconds is not None else 10**9,
                    )
                )
                return filtered

            return []

        return list(arrivals)

    @staticmethod
    def _normalize_stop_name(value: str | None) -> str:
        if not value:
            return ""
        compact = "".join(value.split())
        return compact.removesuffix("역")

    @staticmethod
    def _normalize_bus_line(value: str | None) -> str:
        if not value:
            return ""
        compact = "".join(value.split())
        compact = compact.removesuffix("번")
        prefixes = ["마을", "일반", "지선", "간선", "직행", "좌석", "광역", "시내", "농어촌", "급행", "순환", "맞춤"]
        for prefix in prefixes:
            if compact.startswith(prefix):
                compact = compact[len(prefix):]
        return compact.strip()



    def _collect_first_bus_candidate(self, response: RouteResponse) -> list[RouteStop]:
        for segment in response.segments:
            if segment.transport_type.value == "BUS" and segment.stops:
                stop = segment.stops[0]
                if stop.station_id:
                    return [stop]
                return []
        return []


    @staticmethod
    def _subway_lookup_name(name: str) -> str:
        return name.removesuffix("역")

    @staticmethod
    def _is_opposite_subway_direction(
        direction: str | None,
        departure_name: str,
        arrival_name: str | None,
        segment_stops: list[RouteStop] | None = None,
    ) -> bool:
        if not direction:
            return False

        dep_clean = RouteService._subway_lookup_name(departure_name)
        arr_clean = RouteService._subway_lookup_name(arrival_name) if arrival_name else ""

        # 1. segment_stops 정보가 존재하고 2개 이상의 역 정보가 있는 경우 (동적 경로 기반 판단)
        if segment_stops and len(segment_stops) >= 2:
            next_stop_name = RouteService._subway_lookup_name(segment_stops[1].name)
            downstream_stop_names = {
                RouteService._subway_lookup_name(s.name)
                for s in segment_stops[1:]
            }

            # direction 텍스트에서 "~방면" 추출 (예: "수원행 - 관악방면" -> "관악", "외선순환 - 교대방면" -> "교대")
            waypoint_match = re.search(r'([가-힣0-9a-zA-Z]+)\s*방면', direction)
            if waypoint_match:
                waypoint_station = RouteService._subway_lookup_name(waypoint_match.group(1))
                if waypoint_station == next_stop_name or waypoint_station in downstream_stop_names:
                    return False  # 목적지/진행 방향 역과 일치함 -> 정상 (반대 방향 아님)
                else:
                    return True   # 진행 방향과 다른 역 (예: "구로방면") -> 반대 방향

            # direction 텍스트에서 "~행" 추출 (예: "수원행", "죽전행")
            dest_match = re.search(r'([가-힣0-9a-zA-Z]+)\s*행', direction)
            if dest_match:
                dest_station = RouteService._subway_lookup_name(dest_match.group(1))
                if dest_station == next_stop_name or dest_station in downstream_stop_names or dest_station == arr_clean:
                    return False  # 목적지 방향 종착역 -> 정상 (반대 방향 아님)

        # 2. segment_stops가 없거나 도착역 정보만 있는 경우 fallback
        if arr_clean:
            if arr_clean in direction:
                return False

        return False

    async def _get_arrivals(
        self,
        stop: RouteStop,
        allowed_lines: set[str] | None = None,
        destination_name: str | None = None,
    ) -> tuple[str, dict]:
        try:
            response = await asyncio.wait_for(
                self.bus_client.get_arrivals(stop.city_code or "", stop.station_id or ""),
                timeout=3.5,
            )
            arrivals = self.filter_bus_arrivals(
                response.items,
                allowed_lines=allowed_lines,
            )
            return stop.station_id or "", {"arrivals": arrivals}
        except Exception as exc:
            return stop.station_id or "", {"arrival_error": "도착정보를 조회하지 못했습니다."}

    async def _get_subway_arrivals(
        self,
        stop: RouteStop,
        line_name: str | None,
        arrival_stop_name: str | None = None,
        segment_stops: list[RouteStop] | None = None,
    ) -> tuple[str, str | None, dict]:
        lookup_name = self._subway_lookup_name(stop.name)
        if self.subway_client is None:
            return (
                lookup_name,
                line_name,
                {"arrival_error": "지하철 도착정보 클라이언트가 설정되지 않았습니다."},
            )
        try:
            response = await asyncio.wait_for(
                self.subway_client.get_arrivals(lookup_name),
                timeout=3.5,
            )
            line_matched_arrivals = [
                item
                for item in response.items
                if (
                    not line_name
                    or item.line_name is None
                    or self._same_subway_line(item.line_name, line_name)
                )
            ]
            arrivals = [
                item
                for item in line_matched_arrivals
                if not self._is_opposite_subway_direction(
                    direction=item.direction,
                    departure_name=stop.name,
                    arrival_name=arrival_stop_name,
                    segment_stops=segment_stops,
                )
            ]
            if not arrivals and line_matched_arrivals:
                arrivals = line_matched_arrivals
            return lookup_name, line_name, {"arrivals": arrivals}
        except Exception:
            return (
                lookup_name,
                line_name,
                {"arrival_error": "지하철 도착정보를 조회하지 못했습니다."},
            )

    @classmethod
    def same_destination_bus_lines(cls, response: RouteResponse) -> set[str]:
        primary_segment = cls._first_bus_segment(response)
        target = cls._normalize_stop_name(cls._first_bus_arrival_name(response))
        origin = cls._normalize_stop_name(
            primary_segment.departure_stop
            if primary_segment is not None
            else None
        )
        lines: set[str] = set()
        primary = cls._first_bus_segment(response)
        if primary is not None and primary.line_name:
            lines.add(cls._normalize_bus_line(primary.line_name))
        if not target:
            return lines

        candidates = [response, *response.alternatives]
        for route in candidates:
            segment = cls._first_bus_segment(route)
            if segment is None or not segment.line_name:
                continue
            arrival_name = cls._normalize_stop_name(
                segment.arrival_stop or (segment.stops[-1].name if segment.stops else None)
            )
            departure_name = cls._normalize_stop_name(
                segment.departure_stop
                or (segment.stops[0].name if segment.stops else None)
            )
            if (
                arrival_name
                and target
                and departure_name
                and origin
                and cls._is_same_stop_name(arrival_name, target)
                and cls._is_same_stop_name(departure_name, origin)
            ):
                lines.add(cls._normalize_bus_line(segment.line_name))

        return lines

    @staticmethod
    def _is_same_stop_name(left: str, right: str) -> bool:
        if not left or not right:
            return False
        return left in right or right in left

    @staticmethod
    def _same_subway_line(left: str, right: str) -> bool:
        clean_left = left.replace("수도권", "").replace(" ", "").replace(".", "").removesuffix("선")
        clean_right = right.replace("수도권", "").replace(" ", "").replace(".", "").removesuffix("선")
        return clean_left in clean_right or clean_right in clean_left
