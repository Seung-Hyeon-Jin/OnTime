import unittest
import json
from pathlib import Path

from app.clients.http_client import HttpClient
from app.clients.odsay_client import OdsayClient


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
