import unittest

from app.clients.http_client import ExternalApiError, HttpClient
from app.clients.subway_client import SubwayClient


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
