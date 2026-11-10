from math import asin, cos, radians, sin, sqrt

from app.repositories.bus_stop_repository import BusStop, BusStopRepository
from app.schemas.route import RouteStop


class RouteMatchingError(Exception):
    pass


class RouteStopMatcher:
    def __init__(self, repository: BusStopRepository):
        self.repository = repository

    def match(self, stop: RouteStop, city_code: str | None = None) -> BusStop:
        # 1. 전국 버스 정류소 이름으로 정확한 매칭 시도
        candidates = self.repository.find_by_name(stop.name, None)

        # 2. 정확한 이름 매칭 실패(mismatch) 시 유사 정류장 검색 (difflib 유사도 + GPS 거리)
        if not candidates:
            similar_items = self.repository.find_similar(
                name=stop.name,
                city_code=None,
                lat=stop.latitude,
                lng=stop.longitude,
            )
            if not similar_items:
                raise RouteMatchingError(f"정류장 매칭 실패: {stop.name}")

            # GGB ID 우선, 문자열 유사도 내림차순, GPS 거리 오름차순 정렬
            ranked_similar = sorted(
                similar_items,
                key=lambda item: (
                    0 if item[2].station_id.startswith("GGB") else 1,
                    -item[0],
                    item[1],
                ),
            )
            ratio, distance, candidate = ranked_similar[0]
            if distance > 1500 and ratio < 0.4:
                raise RouteMatchingError(f"정류장 좌표 매칭 실패: {stop.name}")

            return candidate

        # 경기도/국토부 버스 정류소 고유 ID(GGB...) 우선 후 GPS 거리 순 정렬
        ranked = sorted(
            (
                (
                    0 if candidate.station_id.startswith("GGB") else 1,
                    self._distance_meters(stop, candidate),
                    candidate,
                )
                for candidate in candidates
            ),
            key=lambda item: (item[0], item[1]),
        )
        _, distance, candidate = ranked[0]
        if distance > 1000:
            raise RouteMatchingError(f"정류장 좌표 매칭 실패: {stop.name}")

        return candidate

    @staticmethod
    def _distance_meters(stop: RouteStop, candidate: BusStop) -> float:
        latitude_delta = radians(candidate.latitude - stop.latitude)
        longitude_delta = radians(candidate.longitude - stop.longitude)
        latitude_a = radians(stop.latitude)
        latitude_b = radians(candidate.latitude)
        value = (
            sin(latitude_delta / 2) ** 2
            + cos(latitude_a) * cos(latitude_b) * sin(longitude_delta / 2) ** 2
        )
        return 6_371_000 * 2 * asin(sqrt(value))
