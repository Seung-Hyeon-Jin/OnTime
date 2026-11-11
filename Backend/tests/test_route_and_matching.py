import asyncio
import unittest
from types import SimpleNamespace

from app.core.config import settings
from app.repositories.bus_stop_repository import BusStopRepository
from app.schemas.arrival import ArrivalItem
from app.schemas.route import RouteResponse, RouteSegment, RouteStop
from app.schemas.transport import TransportType
from app.services.route_matching_service import RouteMatchingError, RouteStopMatcher
from app.services.route_service import RouteService


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


def _stop(name: str) -> RouteStop:
    return RouteStop(
        name=name,
        latitude=37.4,
        longitude=126.9,
        odsay_station_id="OD1",
    )


def _bus_route(line_name: str, arrival_stop: str) -> RouteResponse:
    return RouteResponse(
        provider="odsay",
        total_duration_minutes=20,
        transfer_count=0,
        fare=1500,
        segments=[
            RouteSegment(
                transport_type=TransportType.BUS,
                line_name=line_name,
                departure_stop="광명역세권1단지후문",
                arrival_stop=arrival_stop,
                duration_minutes=15,
                stops=[_stop("광명역세권1단지후문"), _stop(arrival_stop)],
            )
        ],
    )


class RouteServiceFilterTest(unittest.TestCase):
    def test_same_destination_bus_lines_exclude_unrelated_alternatives(self):
        primary = _bus_route("1", "석수역")
        primary = primary.model_copy(
            update={
                "alternatives": [
                    _bus_route("3001", "석수역"),
                    _bus_route("22", "철산역"),
                    _bus_route("11-2", "광명사거리"),
                ]
            }
        )
        lines = RouteService.same_destination_bus_lines(primary)
        self.assertEqual(lines, {"1", "3001"})

    def test_same_destination_bus_lines_require_same_departure_stop(self):
        primary = _bus_route("1", "석수역")
        different_departure = _bus_route("88", "석수역").model_copy(
            update={
                "segments": [
                    _bus_route("88", "석수역").segments[0].model_copy(
                        update={"departure_stop": "철산역"}
                    )
                ]
            }
        )
        primary = primary.model_copy(update={"alternatives": [different_departure]})
        self.assertEqual(RouteService.same_destination_bus_lines(primary), {"1"})

    def test_gwangmyeong_commute_lines_exclude_unrelated_bus(self):
        primary = _bus_route("3001", "석수역")
        primary = primary.model_copy(
            update={
                "alternatives": [
                    _bus_route("88", "철산역"),
                    _bus_route("1-3", "석수역"),
                ]
            }
        )
        lines = RouteService.same_destination_bus_lines(primary)
        self.assertEqual(lines, {"3001", "1-3"})

    def test_same_destination_bus_lines_keep_lettered_alternatives(self):
        primary = _bus_route("1", "석수역")
        primary = primary.model_copy(
            update={
                "alternatives": [
                    _bus_route("1A", "석수역"),
                ]
            }
        )
        self.assertEqual(RouteService.same_destination_bus_lines(primary), {"1", "1A"})

    def test_filter_bus_arrivals_keeps_only_allowed_or_destination_lines(self):
        items = [
            ArrivalItem(
                transport_type=TransportType.BUS,
                station_or_stop_name="광명역세권1단지후문",
                line_name="22",
                direction="철산",
            ),
            ArrivalItem(
                transport_type=TransportType.BUS,
                station_or_stop_name="광명역세권1단지후문",
                line_name="11-2",
                direction="광명사거리",
            ),
            ArrivalItem(
                transport_type=TransportType.BUS,
                station_or_stop_name="광명역세권1단지후문",
                line_name="1",
                direction="석수역",
            ),
        ]
        filtered = RouteService.filter_bus_arrivals(
            items,
            allowed_lines={"1", "3001"},
            destination_name="석수역",
        )
        self.assertEqual([item.line_name for item in filtered], ["1"])

    def test_filter_bus_arrivals_includes_branch_variant_lines(self):
        items = [
            ArrivalItem(
                transport_type=TransportType.BUS,
                station_or_stop_name="광명역세권1단지후문",
                line_name="1-3",
                direction="석수역",
            ),
            ArrivalItem(
                transport_type=TransportType.BUS,
                station_or_stop_name="광명역세권1단지후문",
                line_name="1A",
                direction="석수역",
            ),
            ArrivalItem(
                transport_type=TransportType.BUS,
                station_or_stop_name="광명역세권1단지후문",
                line_name="88",
                direction="철산",
            ),
        ]
        filtered = RouteService.filter_bus_arrivals(
            items,
            allowed_lines={"1", "3001"},
            destination_name="석수역",
        )
        self.assertEqual([item.line_name for item in filtered], ["1-3", "1A"])

    def test_filter_bus_arrivals_does_not_fallback_to_unrelated_lines(self):
        items = [
            ArrivalItem(
                transport_type=TransportType.BUS,
                station_or_stop_name="광명역세권1단지후문",
                line_name="88",
                direction="철산",
            ),
        ]
        filtered = RouteService.filter_bus_arrivals(
            items,
            allowed_lines={"1", "1-3", "1A", "3001"},
            destination_name="석수역",
        )
        self.assertEqual(filtered, [])

    def test_dynamic_subway_direction_filtering(self):
        seoksu_segment_stops = [_stop("석수역"), _stop("관악역"), _stop("안양역"), _stop("수원역")]
        self.assertFalse(
            RouteService._is_opposite_subway_direction(
                direction="수원행 - 관악방면",
                departure_name="석수역",
                arrival_name="수원역",
                segment_stops=seoksu_segment_stops,
            )
        )
        self.assertTrue(
            RouteService._is_opposite_subway_direction(
                direction="청량리행 - 구로방면",
                departure_name="석수역",
                arrival_name="수원역",
                segment_stops=seoksu_segment_stops,
            )
        )

        suwon_segment_stops = [_stop("수원역"), _stop("매교역"), _stop("죽전역")]
        self.assertFalse(
            RouteService._is_opposite_subway_direction(
                direction="왕십리행 - 매교방면",
                departure_name="수원역",
                arrival_name="죽전역",
                segment_stops=suwon_segment_stops,
            )
        )
        self.assertTrue(
            RouteService._is_opposite_subway_direction(
                direction="인천행 - 고색방면",
                departure_name="수원역",
                arrival_name="죽전역",
                segment_stops=suwon_segment_stops,
            )
        )

        gangnam_segment_stops = [_stop("강남역"), _stop("교대역")]
        self.assertFalse(
            RouteService._is_opposite_subway_direction(
                direction="외선순환 - 교대방면",
                departure_name="강남역",
                arrival_name="교대역",
                segment_stops=gangnam_segment_stops,
            )
        )
        self.assertTrue(
            RouteService._is_opposite_subway_direction(
                direction="내선순환 - 역삼방면",
                departure_name="강남역",
                arrival_name="교대역",
                segment_stops=gangnam_segment_stops,
            )
        )

    def test_subway_arrivals_fall_back_when_direction_filter_removes_all(self):
        class FakeSubwayClient:
            async def get_arrivals(self, station_name):
                if station_name != "석수":
                    raise AssertionError(f"unexpected station: {station_name}")
                return SimpleNamespace(
                    items=[
                        ArrivalItem(
                            transport_type=TransportType.SUBWAY,
                            station_or_stop_name="석수",
                            line_name="1호선",
                            direction="청량리행 - 구로방면",
                            arrival_seconds=90,
                        )
                    ]
                )

        service = RouteService(
            odsay_client=None,
            matcher=None,
            bus_client=None,
            subway_client=FakeSubwayClient(),
        )
        stop = _stop("석수역")
        key, line_name, update = asyncio.run(
            service._get_subway_arrivals(
                stop,
                "1호선",
                arrival_stop_name="수원역",
                segment_stops=[
                    _stop("석수역"),
                    _stop("관악역"),
                    _stop("수원역"),
                ],
            )
        )

        self.assertEqual((key, line_name), ("석수", "1호선"))
        self.assertEqual(len(update["arrivals"]), 1)
