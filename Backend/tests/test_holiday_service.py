from datetime import date
import unittest

from app.services.holiday_service import HolidayService


class HolidayServiceTest(unittest.TestCase):
    def test_fixed_solar_holidays(self):
        # 신정, 삼일절, 광복절, 개천절, 한글날, 성탄절 등 고정 공휴일 검증
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 1, 1)))
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 3, 1)))
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 5, 5)))
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 6, 6)))
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 8, 15)))
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 10, 3)))
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 10, 9)))
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 12, 25)))

    def test_lunar_variable_holidays(self):
        # 2026년 설날 연휴 (2월 16, 17, 18일) 검증
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 2, 16)))
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 2, 17)))
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 2, 18)))

        # 2026년 추석 연휴 (9월 24, 25, 26일) 검증
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 9, 24)))
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 9, 25)))
        self.assertTrue(HolidayService.is_public_holiday(date(2026, 9, 26)))

    def test_substitute_holiday_calculation(self):
        # 2024년 설날 (2월 10일 토요일) -> 대체공휴일 2월 12일 월요일 생성 검증
        self.assertTrue(HolidayService.is_public_holiday(date(2024, 2, 12)))

        # 2025년 어린이날/부처님오신날 중복 (5월 5일 월요일) -> 대체공휴일 5월 6일 화요일 생성 검증
        self.assertTrue(HolidayService.is_public_holiday(date(2025, 5, 6)))

    def test_regular_workday_returns_false(self):
        # 일반 평일 검증
        self.assertFalse(HolidayService.is_public_holiday(date(2026, 3, 10)))
        self.assertFalse(HolidayService.is_public_holiday(date(2026, 7, 15)))


if __name__ == "__main__":
    unittest.main()
