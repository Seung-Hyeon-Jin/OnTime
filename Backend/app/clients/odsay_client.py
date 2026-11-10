from app.clients.http_client import ExternalApiError
from app.schemas.route import Location, RouteResponse, RouteSegment, RouteStop
from app.schemas.transport import TransportType
from app.core.config import settings
from app.clients.http_client import HttpClient

class OdsayClient:
    BASE_URL = "https://api.odsay.com/v1/api/searchPubTransPathT"
    def __init__(self, http_client : HttpClient):
        self.http_client = http_client
    
    
    async def search_routes(
            self,
            origin: Location,
            destination : Location
    ) -> RouteResponse:
        if not settings.ODSAY_API_KEY:
            raise ValueError("ODsay Api key is not exist")

        params = {
            "apiKey" : settings.ODSAY_API_KEY,
            "SX" : str(origin.longitude),
            "SY" : str(origin.latitude),
            "EX" : str(destination.longitude),
            "EY" : str(destination.latitude),
            "SearchPathType" : 0,
            "OPT" : 1,
            "output" : "json"
        }

        data = await self.http_client.get_json(
            self.BASE_URL,
            params=params,
            provider="odsay",
        )

        return self._parse_route_response(data)
    def _parse_route_response(self, data: dict) -> RouteResponse:
        if not isinstance(data, dict):
            raise ExternalApiError("odsay", "ODsay 응답 구조가 올바르지 않습니다.")

        result = data.get("result")
        if not isinstance(result, dict):
            error = data.get("error", {})
            message = error.get("message") if isinstance(error, dict) else None
            raise ExternalApiError("odsay", message or "ODsay 경로를 찾지 못했습니다.")

        paths = result.get("path")
        if not isinstance(paths, list) or not paths:
            raise ExternalApiError("odsay", "ODsay 경로 결과가 없습니다.")

        parsed_paths = [self._parse_path(path) for path in paths if isinstance(path, dict)]
        if not parsed_paths:
            raise ExternalApiError("odsay", "ODsay 경로 형식이 올바르지 않습니다.")
        parsed_paths.sort(
            key=lambda route: (
                route.total_duration_minutes,
                route.transfer_count,
                route.fare if route.fare is not None else 10**9,
            )
        )
        selected = parsed_paths[0]
        return selected.model_copy(update={"alternatives": parsed_paths[1:]})

    def _parse_path(self, path: dict) -> RouteResponse:
        if not isinstance(path, dict):
            raise ExternalApiError("odsay", "ODsay 경로 형식이 올바르지 않습니다.")

        raw_sub_paths = path.get("subPath", [])
        if not isinstance(raw_sub_paths, list):
            raise ExternalApiError("odsay", "ODsay 이동 구간 형식이 올바르지 않습니다.")

        segments = [self._parse_segment(sub_path) for sub_path in raw_sub_paths]
        return RouteResponse(
            provider="odsay",
            total_duration_minutes=max(0, self._as_int(path.get("info", {}).get("totalTime")) // 1),
            transfer_count=max(0, self._as_int(path.get("info", {}).get("transferCount"))),
            fare=self._as_int(path.get("info", {}).get("payment")),
            segments=segments,
        )

    def _parse_segment(self, data: dict) -> RouteSegment:
        if not isinstance(data, dict):
            raise ExternalApiError("odsay", "ODsay 이동 구간 항목이 올바르지 않습니다.")

        traffic_type = {1: TransportType.SUBWAY, 2: TransportType.BUS, 3: TransportType.WALK}.get(data.get("trafficType"))
        if traffic_type is None:
            raise ExternalApiError("odsay", "지원하지 않는 ODsay 교통수단입니다.")

        stops = []
        pass_stop_list = data.get("passStopList", {})
        raw_stations = pass_stop_list.get("stations", pass_stop_list.get("station", []))
        if isinstance(raw_stations, dict):
            raw_stations = [raw_stations]
        for station in raw_stations if isinstance(raw_stations, list) else []:
            if not isinstance(station, dict):
                continue
            if station.get("stationName") is None or station.get("x") is None or station.get("y") is None:
                continue
            stops.append(
                RouteStop(
                    name=str(station["stationName"]),
                    latitude=float(station["y"]),
                    longitude=float(station["x"]),
                    odsay_station_id=str(station.get("stationID", "")),
                )
            )

        return RouteSegment(
            transport_type=traffic_type,
            line_name=self._as_text(data.get("lane", [{}])[0].get("busNo") if traffic_type == TransportType.BUS and isinstance(data.get("lane"), list) and data.get("lane") else data.get("lane", [{}])[0].get("name") if isinstance(data.get("lane"), list) and data.get("lane") else None),
            departure_stop=self._as_text(data.get("startName")),
            arrival_stop=self._as_text(data.get("endName")),
            duration_minutes=max(0, self._as_int(data.get("sectionTime"))),
            distance_meters=max(0, self._as_int(data.get("distance"))),
            stops=stops,
        )

    @staticmethod
    def _as_text(value: object) -> str | None:
        return None if value is None else str(value)

    @staticmethod
    def _as_int(value: object) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0
