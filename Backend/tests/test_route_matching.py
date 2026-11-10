import unittest
from pathlib import Path

from app.core.config import settings
from app.repositories.bus_stop_repository import BusStopRepository
from app.schemas.route import RouteStop
from app.services.route_matching_service import RouteMatchingError, RouteStopMatcher


class RouteMatchingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matcher = RouteStopMatcher(BusStopRepository(settings.BUS_STOP_CSV_PATH))

    def test_matches_철산역_by_coordinate(self):
        stop = RouteStop(
            name="철산역",
            latitude=37.4758667,
            longitude=126.8679667,
            odsay_station_id="OD123",
        )
        matched = self.matcher.match(stop, "31060")
        self.assertEqual(matched.station_id, "GGB213000128")
        self.assertNotEqual(stop.odsay_station_id, matched.station_id)

    def test_matches_odsay_lotte_mall_name_to_csv_lotte_outlet_name(self):
        stop = RouteStop(
            name="이케아.롯데몰광명점",
            latitude=37.422617,
            longitude=126.884183,
            odsay_station_id="165797",
        )
        matched = self.matcher.match(stop, "31060")
        self.assertEqual(matched.name, "이케아.롯데아울렛광명점")

    def test_matches_similar_bus_stop_name_on_mismatch(self):
        stop = RouteStop(
            name="이케아.롯데몰",
            latitude=37.422617,
            longitude=126.884183,
            odsay_station_id="165797",
        )
        matched = self.matcher.match(stop, "31060")
        self.assertIn("롯데아울렛", matched.name)

    def test_rejects_unknown_stop(self):
        stop = RouteStop(
            name="존재하지 않는 정류장",
            latitude=37.0,
            longitude=127.0,
            odsay_station_id="OD404",
        )
        with self.assertRaises(RouteMatchingError):
            self.matcher.match(stop)
