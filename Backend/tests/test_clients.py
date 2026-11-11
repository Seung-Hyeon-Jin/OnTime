import asyncio
import json
import unittest
from pathlib import Path

import httpx

from app.clients.bus_client import BusClient
from app.clients.http_client import ExternalApiError, HttpClient
from app.clients.odsay_client import OdsayClient
from app.clients.subway_client import SubwayClient
from app.schemas.arrival import ArrivalResponse
from app.schemas.transport import TransportType


class HttpClientTest(unittest.IsolatedAsyncioTestCase):
    async def test_timeout_becomes_external_api_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("timed out", request=request)

        client = HttpClient()
        await client.client.aclose()
        client.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            with self.assertRaises(ExternalApiError) as context:
                await client.get_json("https://example.test", provider="odsay")
            self.assertEqual(context.exception.provider, "odsay")
        finally:
            await client.close()


class BusClientTest(unittest.TestCase):
    def setUp(self):
        self.client = BusClient(HttpClient())

    def test_parses_numeric_fields_and_messages(self):
        response = self.client._parse_national_response(
            {
                "response": {
                    "header": {"resultCode": "00"},
                    "body": {
                        "items": {
                            "item": {
                                "nodenm": "철산역",
                                "routeno": 11,
                                "arrtime": "90",
                                "vehicleno": 123,
                                "routedest": "광명",
                                "arrmsg1": "곧 도착",
                            }
                        }
                    },
                }
            }
        )
        item = response.items[0]
        self.assertEqual(item.line_name, "11")
        self.assertEqual(item.arrival_seconds, 90)
        self.assertEqual(item.vehicle_number, "123")
        self.assertEqual(item.direction, "광명")
        self.assertEqual(item.arrival_message, "곧 도착")

    def test_empty_items(self):
        response = self.client._parse_national_response(
            {"response": {"header": {"resultCode": "00"}, "body": {"items": ""}}}
        )
        self.assertEqual(response.items, [])

    def test_result_code_error(self):
        with self.assertRaises(ExternalApiError):
            self.client._parse_national_response(
                {"response": {"header": {"resultCode": "99", "resultMsg": "bad"}}}
            )

    def test_parse_gbis_response(self):
        mock_data = {
            "response": {
                "msgHeader": {"resultCode": 0, "resultMessage": "정상 처리"},
                "msgBody": {
                    "busArrivalList": [
                        {
                            "routeName": "1-3",
                            "predictTime1": "4",
                            "locationNo1": "2",
                            "plateNo1": "경기78아1234",
                            "predictTime2": "14",
                            "locationNo2": "7",
                            "plateNo2": "경기78아5678",
                        }
                    ]
                }
            }
        }
        items = self.client._parse_gbis_response(mock_data, "213000367")
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].line_name, "1-3")
        self.assertEqual(items[0].arrival_seconds, 240)
        self.assertEqual(items[0].vehicle_number, "경기78아1234")
        self.assertEqual(items[1].arrival_seconds, 840)


class OdsayClientTest(unittest.TestCase):
    def test_parses_recorded_route_response_without_reusing_odsay_id_as_tago_id(self):
        fixture_path = Path(__file__).parent / "fixtures" / "odsay_route_response.json"
        with fixture_path.open(encoding="utf-8") as file:
            fixture = json.load(file)

        response = OdsayClient(HttpClient())._parse_route_response(fixture)

        bus_segment = next(segment for segment in response.segments if segment.line_name == "17")
        self.assertEqual(response.total_duration_minutes, 42)
        self.assertEqual(len(bus_segment.stops), 20)
        self.assertEqual(bus_segment.stops[0].odsay_station_id, "101537")
        self.assertEqual(bus_segment.stops[-1].odsay_station_id, "82386")
        self.assertIsNone(bus_segment.stops[0].station_id)


class SubwayClientTest(unittest.TestCase):
    def setUp(self):
        self.client = SubwayClient(HttpClient())

    def test_uses_train_line_name_as_direction(self):
        response = self.client._parse_response(
            {
                "errorMessage": {"code": "INFO-000", "message": "정상 처리되었습니다."},
                "realtimeArrivalList": [
                    {
                        "statnNm": "석수",
                        "subwayId": "1001",
                        "updnLine": "상행",
                        "trainLineNm": "청량리행 - 금천구청방면",
                        "bstatnNm": "청량리",
                        "barvlDt": "90",
                        "arvlMsg2": "[2]번째 전역 (관악)",
                        "btrainNo": "1234",
                    }
                ],
            }
        )
        item = response.items[0]
        self.assertEqual(item.line_name, "1호선")
        self.assertEqual(item.direction, "청량리행 - 금천구청방면")
        self.assertEqual(item.arrival_seconds, 90)

    def test_empty_list_is_not_an_error(self):
        response = self.client._parse_response(
            {
                "status": 500,
                "code": "INFO-200",
                "message": "해당하는 데이터가 없습니다.",
                "total": 0,
            }
        )
        self.assertEqual(response.items, [])

    def test_auth_error_is_raised(self):
        with self.assertRaises(ExternalApiError):
            self.client._parse_response(
                {
                    "code": "ERROR-300",
                    "message": "필수 값이 누락되어 있습니다.",
                }
            )

    def test_station_name_drops_suffix_before_lookup(self):
        self.assertEqual(self.client._normalize_station_name("석수역"), "석수")
        self.assertEqual(self.client._normalize_station_name("강남"), "강남")

    def test_zero_barvl_dt_returns_0_seconds(self):
        self.assertEqual(self.client._parse_seconds("0"), 0)
        self.assertEqual(self.client._parse_seconds("120"), 120)


class SubwayResponseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        response_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "gangnma.json"
        )
        with response_path.open(encoding="utf-8") as response_file:
            cls.response = ArrivalResponse.model_validate(
                json.load(response_file)
            )

    def test_response_metadata(self):
        self.assertEqual(self.response.provider, "seoul-subway")
        self.assertEqual(self.response.queried_at.tzinfo is not None, True)
        self.assertGreater(len(self.response.items), 0)

    def test_arrival_items(self):
        for item in self.response.items:
            self.assertEqual(item.transport_type, TransportType.SUBWAY)
            self.assertEqual(item.station_or_stop_name, "강남")
            self.assertIsInstance(item.arrival_seconds, int)
            self.assertGreaterEqual(item.arrival_seconds, 0)
            self.assertTrue(item.arrival_message)

    def test_expected_arrival_count(self):
        self.assertEqual(len(self.response.items), 7)

    def test_print_response_summary(self):
        print("\n=== Subway Arrival Summary ===")
        print(f"provider: {self.response.provider}")
        print(f"queried_at: {self.response.queried_at.isoformat()}")

        for index, item in enumerate(self.response.items, start=1):
            line_name = item.line_name or "unknown line"
            direction = item.direction or "unknown direction"
            print(
                f"{index}. station={item.station_or_stop_name}, "
                f"line={line_name}, direction={direction}, "
                f"arrival_seconds={item.arrival_seconds}, "
                f"message={item.arrival_message}, "
                f"train={item.vehicle_number}"
            )


if __name__ == "__main__":
    unittest.main()
