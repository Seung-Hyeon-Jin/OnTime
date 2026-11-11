import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class BusStop:
    station_id: str
    name: str
    latitude: float
    longitude: float
    city_code: str
    city_name: str


@lru_cache(maxsize=8)
def _load_stops(path: str) -> tuple[BusStop, ...]:
    stops: list[BusStop] = []
    with Path(path).open("r", encoding="cp949", newline="") as file:
        for row in csv.DictReader(file):
            if not all(row.get(field, "").strip() for field in ("정류장번호", "정류장명", "위도", "경도", "도시코드", "도시명")):
                continue
            try:
                stops.append(
                    BusStop(
                        station_id=row["정류장번호"].strip(),
                        name=row["정류장명"].strip(),
                        latitude=float(row["위도"]),
                        longitude=float(row["경도"]),
                        city_code=row["도시코드"].strip(),
                        city_name=row["도시명"].strip(),
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError("버스 정류장 CSV에 유효하지 않은 행이 있습니다.") from exc
    return tuple(stops)


class BusStopRepository:
    def __init__(self, csv_path: str | Path):
        self.csv_path = str(csv_path)
        self._stops = _load_stops(self.csv_path)
        self._name_index: dict[str, list[BusStop]] = {}
        for stop in self._stops:
            norm = _normalize_name(stop.name)
            self._name_index.setdefault(norm, []).append(stop)

    def find_by_name(self, name: str, city_code: str | None = None) -> list[BusStop]:
        normalized_name = _normalize_name(name)
        candidates = self._name_index.get(normalized_name, [])
        if city_code is None:
            return candidates
        return [stop for stop in candidates if stop.city_code == city_code]

    def search_by_name(
        self,
        query: str,
        city_code: str | None = None,
        limit: int = 20,
    ) -> list[BusStop]:
        normalized_query = _normalize_name(query)
        if not normalized_query:
            return []

        matches = [
            stop
            for stop in self._stops
            if normalized_query in _normalize_name(stop.name)
            and (city_code is None or stop.city_code == city_code)
        ]
        return matches[:limit]

    def find_similar(
        self,
        name: str,
        city_code: str | None = None,
        lat: float | None = None,
        lng: float | None = None,
        max_distance_meters: float = 2000.0,
        min_similarity: float = 0.35,
    ) -> list[tuple[float, float, BusStop]]:
        import difflib
        from math import asin, cos, radians, sin, sqrt

        norm_query = _normalize_name(name)
        if not norm_query:
            return []

        results = []
        has_coords = lat is not None and lng is not None and (lat != 0.0 or lng != 0.0)

        for stop in self._stops:
            if city_code and stop.city_code != city_code:
                continue

            if has_coords:
                if abs(stop.latitude - lat) > 0.035 or abs(stop.longitude - lng) > 0.04:
                    continue

            norm_cand = _normalize_name(stop.name)
            ratio = difflib.SequenceMatcher(None, norm_query, norm_cand).ratio()

            if norm_query in norm_cand or norm_cand in norm_query:
                ratio = max(ratio, 0.6)

            dist = 0.0
            if has_coords:
                d_lat = radians(stop.latitude - lat)
                d_lng = radians(stop.longitude - lng)
                a = (
                    sin(d_lat / 2) ** 2
                    + cos(radians(lat)) * cos(radians(stop.latitude)) * sin(d_lng / 2) ** 2
                )
                dist = 6_371_000 * 2 * asin(sqrt(a))
                if dist > max_distance_meters:
                    continue

            if ratio >= min_similarity:
                results.append((ratio, dist, stop))

        return results


def _normalize_name(value: str) -> str:
    return "".join(value.split()).replace("·", ".")