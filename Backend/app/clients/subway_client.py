import re
from datetime import datetime, timezone

from app.clients.http_client import ExternalApiError, HttpClient
from app.core.config import settings
from app.schemas.arrival import ArrivalItem, ArrivalResponse
from app.schemas.transport import TransportType


class SubwayClient:
    BASE_URL = "http://swopenAPI.seoul.go.kr/api/subway"
    LINE_NAMES = {
        "1001": "1호선",
        "1002": "2호선",
        "1003": "3호선",
        "1004": "4호선",
        "1005": "5호선",
        "1006": "6호선",
        "1007": "7호선",
        "1008": "8호선",
        "1009": "9호선",
        "1063": "경의중앙선",
        "1065": "공항철도",
        "1067": "경춘선",
        "1075": "수인분당선",
        "1077": "신분당선",
        "1092": "우이신설선",
        "1093": "서해선",
    }

    def __init__(self, http_client: HttpClient):
        self.http_client = http_client

    async def get_arrivals(
        self,
        station_name: str,
    ) -> ArrivalResponse:
        if not settings.SUBWAY_SERVICE_KEY:
            raise ValueError("서울 지하철 API 키가 설정되지 않았습니다.")

        requested_name = self._normalize_station_name(station_name)
        url = (
            f"{self.BASE_URL}/"
            f"{settings.SUBWAY_SERVICE_KEY}/"
            f"json/realtimeStationArrival/0/100/"
            f"{requested_name}"
        )

        data = await self.http_client.get_json(
            url,
            provider="seoul-subway",
        )
        response = self._parse_response(data)
        response.items = [
            item
            for item in response.items
            if self._normalize_station_name(item.station_or_stop_name)
            == requested_name
        ]
        return response



    def _parse_response(self, data: dict) -> ArrivalResponse:
        self._raise_for_api_error(data)
        items = []

        for item in data.get("realtimeArrivalList", []) or []:
            if not isinstance(item, dict):
                continue

            msg = (item.get("arvlMsg2") or item.get("arvlMsg3") or "").strip()
            msg = msg.replace("전역 후", "전역")
            msg = re.sub(r'\[(\d+)\]번째\s*전역', r'\1전역', msg)

            items.append(
                ArrivalItem(
                    transport_type=TransportType.SUBWAY,
                    station_or_stop_name=item.get("statnNm", ""),
                    line_name=self._get_line_name(item),
                    direction=(
                        item.get("trainLineNm")
                        or item.get("bstatnNm")
                        or item.get("updnLine")
                    ),
                    arrival_seconds=self._parse_seconds(
                        item.get("barvlDt")
                    ),
                    arrival_message=msg,
                    vehicle_number=item.get("btrainNo"),
                )
            )

        return ArrivalResponse(
            provider="seoul-subway",
            queried_at=datetime.now(timezone.utc),
            items=items,
        )

    @classmethod
    def _get_line_name(cls, item: dict) -> str | None:
        subway_id = item.get("subwayId")
        if subway_id is not None:
            line_name = cls.LINE_NAMES.get(str(subway_id))
            if line_name:
                return line_name
        return item.get("subwayNm")

    @staticmethod
    def _raise_for_api_error(data: dict) -> None:
        payload = data.get("errorMessage")
        if not isinstance(payload, dict):
            payload = data
        code = str(payload.get("code") or "")
        if code in {"", "INFO-000", "INFO-200"}:
            return
        message = payload.get("message") or "지하철 도착정보를 조회하지 못했습니다."
        raise ExternalApiError("seoul-subway", f"지하철 API 오류({code}): {message}")

    @staticmethod
    def _parse_seconds(value: str | None) -> int | None:
        if value is None or not str(value).isdigit():
            return None
        seconds = int(value)
        return seconds if seconds >= 0 else None

    @staticmethod
    def _normalize_station_name(value: str) -> str:
        return value.replace(" ", "").removesuffix("역")
