import json
import unittest
from pathlib import Path

from app.schemas.arrival import ArrivalResponse
from app.schemas.transport import TransportType


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
