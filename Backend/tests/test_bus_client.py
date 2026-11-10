import unittest

from app.clients.bus_client import BusClient
from app.clients.http_client import ExternalApiError, HttpClient


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
