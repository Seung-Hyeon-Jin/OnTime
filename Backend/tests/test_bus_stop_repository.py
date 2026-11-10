import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.repositories.bus_stop_repository import BusStopRepository


class BusStopRepositoryTest(unittest.TestCase):
    def test_loads_cp949_and_preserves_tago_fields(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "stops.csv"
            path.write_bytes(
                "정류장번호,정류장명,위도,경도,정보수집일,모바일단축번호,도시코드,도시명,관리도시명\n"
                "GGB1,철산역,37.4758667,126.8679667,2025-10-31,1,31060,경기도 광명시,광명BIS\n".encode("cp949")
            )
            stop = BusStopRepository(path).find_by_name(" 철산역 ", "31060")[0]
            self.assertEqual(stop.station_id, "GGB1")
            self.assertEqual(stop.city_code, "31060")
            self.assertEqual(stop.city_name, "경기도 광명시")
