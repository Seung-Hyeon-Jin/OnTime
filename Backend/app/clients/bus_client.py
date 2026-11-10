from datetime import datetime, timezone

from app.clients.http_client import ExternalApiError, HttpClient
from app.core.config import settings
from app.schemas.arrival import ArrivalItem, ArrivalResponse
from app.schemas.transport import TransportType


class BusClient:
    NATIONAL_BASE_URL = (
        "https://apis.data.go.kr/1613000/"
        "ArvlInfoInqireService/"
        "getSttnAcctoArvlPrearngeInfoList"
    )
    GBIS_BASE_URL = (
        "https://apis.data.go.kr/6410000/"
        "busarrivalservice/v2/"
        "getBusArrivalListv2"
    )

    def __init__(self, http_client: HttpClient):
        self.http_client = http_client

    async def get_arrivals(
        self,
        city_code: str,
        station_id: str,
    ) -> ArrivalResponse:
        # 경기도 지역 정류장 여부 확인 (도시코드 31xxx 또는 정류장 ID가 GGB로 시작하는 경우)
        is_gyeonggi = (
            city_code.startswith("31")
            or station_id.startswith("GGB")
            or station_id.startswith("213")
        )

        gbis_items: list[ArrivalItem] = []
        if is_gyeonggi:
            try:
                gbis_items = await self._get_gbis_arrivals(station_id)
            except Exception:
                # 경기도 버스 API 키가 없거나 미승인 상태인 경우 국토교통부 표준 API로 세이프티 폴백
                gbis_items = []

        # 국토교통부 표준 버스 도착 API 호출
        national_response = await self._get_national_arrivals(city_code, station_id)

        if not gbis_items:
            return national_response

        # 경기도 API 결과와 국토교통부 API 결과를 병합 (중복 노선 및 도착 정보 정리)
        combined_items = list(gbis_items)
        existing_lines = {
            self._normalize_bus_line_name(item.line_name)
            for item in gbis_items
            if item.line_name
        }

        for item in national_response.items:
            normalized_line = self._normalize_bus_line_name(item.line_name)
            if normalized_line not in existing_lines:
                combined_items.append(item)

        return ArrivalResponse(
            provider="gyeonggi-and-public-bus",
            queried_at=datetime.now(timezone.utc),
            items=combined_items,
        )

    async def _get_national_arrivals(
        self,
        city_code: str,
        station_id: str,
    ) -> ArrivalResponse:
        if not settings.BUS_SERVICE_KEY:
            raise ValueError("버스 API 키가 설정되지 않았습니다.")

        params = {
            "serviceKey": settings.BUS_SERVICE_KEY,
            "cityCode": city_code,
            "nodeId": station_id,
            "numOfRows": 100,
            "pageNo": 1,
            "_type": "json",
        }

        data = await self.http_client.get_json(
            self.NATIONAL_BASE_URL,
            params=params,
            provider="public-bus",
        )

        return self._parse_national_response(data)

    async def _get_gbis_arrivals(self, station_id: str) -> list[ArrivalItem]:
        service_key = settings.GYEONGGI_BUS_SERVICE_KEY or settings.BUS_SERVICE_KEY
        if not service_key:
            return []

        # GGB 접두어 제거 (GBIS API는 순수 숫자 정류장 ID 사용)
        clean_station_id = station_id.replace("GGB", "").strip()

        params = {
            "serviceKey": service_key,
            "stationId": clean_station_id,
            "format": "json",
        }

        data = await self.http_client.get_json(
            self.GBIS_BASE_URL,
            params=params,
            provider="gyeonggi-bus",
        )

        return self._parse_gbis_response(data, clean_station_id)



    def _parse_national_response(self, data: dict) -> ArrivalResponse:
        items = []

        response = data.get("response")
        if not isinstance(response, dict):
            raise ExternalApiError(
                "public-bus",
                "버스 API 응답 구조가 올바르지 않습니다.",
            )

        header = response.get("header")
        if not isinstance(header, dict):
            raise ExternalApiError(
                "public-bus",
                "버스 API 응답 헤더가 없습니다.",
            )

        result_code = str(header.get("resultCode", ""))
        if result_code not in {"00", "0000"}:
            result_message = header.get("resultMsg") or "알 수 없는 오류"
            raise ExternalApiError(
                "public-bus",
                f"버스 API 오류({result_code}): {result_message}",
            )

        body = response.get("body", {})
        if not isinstance(body, dict):
            raise ExternalApiError(
                "public-bus",
                "버스 API 응답 본문이 올바르지 않습니다.",
            )

        raw_items = body.get("items", {})
        if raw_items in (None, "", "null"):
            response_items = []
        elif isinstance(raw_items, dict):
            response_items = raw_items.get("item", [])
        else:
            raise ExternalApiError(
                "public-bus",
                "버스 API 정류장 도착정보 형식이 올바르지 않습니다.",
            )

        if response_items in (None, "", "null"):
            response_items = []

        if isinstance(response_items, dict):
            response_items = [response_items]
        elif not isinstance(response_items, list):
            raise ExternalApiError(
                "public-bus",
                "버스 API 도착정보 목록 형식이 올바르지 않습니다.",
            )

        for item in response_items:
            if not isinstance(item, dict):
                raise ExternalApiError(
                    "public-bus",
                    "버스 API 도착정보 항목 형식이 올바르지 않습니다.",
                )

            items.append(
                ArrivalItem(
                    transport_type=TransportType.BUS,
                    station_or_stop_name=self._as_text(item.get("nodenm")),
                    line_name=self._as_text(item.get("routeno")),
                    arrival_seconds=self._parse_seconds(item.get("arrtime")),
                    arrival_message=self._as_text(
                        item.get("arrmsg1") or item.get("arrmsg2")
                    ),
                    direction=self._as_text(item.get("routedest")),
                    vehicle_number=self._as_text(item.get("vehicleno")),
                )
            )

        return ArrivalResponse(
            provider="public-bus",
            queried_at=datetime.now(timezone.utc),
            items=items,
        )

    def _parse_gbis_response(self, data: dict, station_id: str) -> list[ArrivalItem]:
        items = []
        if not isinstance(data, dict):
            return items

        response = data.get("response", {})
        if not isinstance(response, dict):
            return items

        msg_header = response.get("msgHeader", {})
        if isinstance(msg_header, dict):
            result_code = str(msg_header.get("resultCode", ""))
            if result_code not in {"0", "00", "0000"}:
                return items

        msg_body = response.get("msgBody", {})
        if not isinstance(msg_body, dict):
            return items

        bus_arrival_list = msg_body.get("busArrivalList", [])
        if bus_arrival_list in (None, "", "null"):
            bus_arrival_list = []
        elif isinstance(bus_arrival_list, dict):
            bus_arrival_list = [bus_arrival_list]

        for item in bus_arrival_list:
            if not isinstance(item, dict):
                continue

            route_name = item.get("routeName") or item.get("routeName1")
            if not route_name:
                continue

            has_valid_vehicle = False

            # 차량 1
            predict_time1 = item.get("predictTime1")
            if predict_time1 is not None and str(predict_time1).isdigit():
                mins1 = int(predict_time1)
                loc1 = item.get("locationNo1")
                msg1 = f"{mins1}분[{loc1}개 전거장]" if loc1 else f"{mins1}분 후"
                items.append(
                    ArrivalItem(
                        transport_type=TransportType.BUS,
                        station_or_stop_name=station_id,
                        line_name=str(route_name),
                        arrival_seconds=mins1 * 60,
                        arrival_message=msg1,
                        vehicle_number=self._as_text(item.get("plateNo1")),
                    )
                )
                has_valid_vehicle = True

            # 차량 2
            predict_time2 = item.get("predictTime2")
            if predict_time2 is not None and str(predict_time2).isdigit():
                mins2 = int(predict_time2)
                loc2 = item.get("locationNo2")
                msg2 = f"{mins2}분[{loc2}개 전거장]" if loc2 else f"{mins2}분 후"
                items.append(
                    ArrivalItem(
                        transport_type=TransportType.BUS,
                        station_or_stop_name=station_id,
                        line_name=str(route_name),
                        arrival_seconds=mins2 * 60,
                        arrival_message=msg2,
                        vehicle_number=self._as_text(item.get("plateNo2")),
                    )
                )
                has_valid_vehicle = True

            # 운행 종료 / 차점 등 수신 시간이 없는 경우 처리
            if not has_valid_vehicle:
                flag = item.get("flag", "")
                msg = "운행종료" if flag == "PASS" else "도착 정보 없음"
                items.append(
                    ArrivalItem(
                        transport_type=TransportType.BUS,
                        station_or_stop_name=station_id,
                        line_name=str(route_name),
                        arrival_seconds=None,
                        arrival_message=msg,
                        vehicle_number=None,
                    )
                )

        return items

    @staticmethod
    def _normalize_bus_line_name(value: str | None) -> str:
        if not value:
            return ""
        compact = "".join(value.split()).removesuffix("번")
        prefixes = ["마을", "일반", "지선", "간선", "직행", "좌석", "광역", "시내", "농어촌", "급행", "순환", "맞춤"]
        for prefix in prefixes:
            if compact.startswith(prefix):
                compact = compact[len(prefix):]
        return compact.strip()

    @staticmethod
    def _as_text(value: object) -> str | None:
        if value is None:
            return None
        return str(value)

    @staticmethod
    def _parse_seconds(value: str | int | None) -> int | None:
        if value is None:
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None
