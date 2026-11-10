from datetime import date, timedelta
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class HolidayService:
    """
    대한민국 법정 공휴일 및 대체공휴일을 동적으로 판정하는 서비스입니다.
    - 양력 고정 공휴일 (신정, 삼일절, 어린이날, 현충일, 광복절, 개천절, 한글날, 성탄절)
    - 음력 가변 공휴일 (설날 3일 연휴, 부처님오신날, 추석 3일 연휴)
    - 대통령령 '관공서의 공휴일에 관한 규정'에 따른 대체공휴일 동적 계산
    """

    # 한국천문연구원 음력 절기 기반 설날(음 1/1), 부처님오신날(음 4/8), 추석(음 8/15) 양력 날짜 테이블
    LUNAR_HOLIDAYS_TABLE: dict[int, dict[str, tuple[int, int]]] = {
        2020: {"seollal": (1, 25), "buddha": (4, 30), "chuseok": (10, 1)},
        2021: {"seollal": (2, 12), "buddha": (5, 19), "chuseok": (9, 21)},
        2022: {"seollal": (2, 1), "buddha": (5, 8), "chuseok": (9, 10)},
        2023: {"seollal": (1, 22), "buddha": (5, 27), "chuseok": (9, 29)},
        2024: {"seollal": (2, 10), "buddha": (5, 15), "chuseok": (9, 17)},
        2025: {"seollal": (1, 29), "buddha": (5, 5), "chuseok": (10, 6)},
        2026: {"seollal": (2, 17), "buddha": (5, 24), "chuseok": (9, 25)},
        2027: {"seollal": (2, 6), "buddha": (5, 13), "chuseok": (9, 15)},
        2028: {"seollal": (1, 27), "buddha": (5, 2), "chuseok": (10, 3)},
        2029: {"seollal": (2, 13), "buddha": (5, 20), "chuseok": (9, 22)},
        2030: {"seollal": (2, 3), "buddha": (5, 9), "chuseok": (9, 12)},
        2031: {"seollal": (1, 23), "buddha": (5, 28), "chuseok": (10, 1)},
        2032: {"seollal": (2, 11), "buddha": (5, 16), "chuseok": (9, 19)},
        2033: {"seollal": (1, 31), "buddha": (5, 6), "chuseok": (10, 7)},
        2034: {"seollal": (2, 19), "buddha": (5, 25), "chuseok": (9, 27)},
        2035: {"seollal": (2, 8), "buddha": (5, 15), "chuseok": (9, 16)},
    }

    # 양력 고정 공휴일 (월, 일) -> (명칭, 대체공휴일 적용여부)
    FIXED_SOLAR_HOLIDAYS: dict[tuple[int, int], tuple[str, bool]] = {
        (1, 1): ("신정", False),
        (3, 1): ("삼일절", True),
        (5, 5): ("어린이날", True),
        (6, 6): ("현충일", False),
        (8, 15): ("광복절", True),
        (10, 3): ("개천절", True),
        (10, 9): ("한글날", True),
        (12, 25): ("성탄절", True),
    }

    @classmethod
    @lru_cache(maxsize=32)
    def get_holidays_for_year(cls, year: int) -> dict[date, list[str]]:
        """특정 연도의 모든 공휴일(고정, 가변, 대체공휴일 포함) 목록을 동적으로 반환합니다."""
        raw_holidays: dict[date, list[str]] = {}

        def add_holiday(d: date, name: str):
            if d not in raw_holidays:
                raw_holidays[d] = []
            raw_holidays[d].append(name)

        # 1. 양력 고정 공휴일 추가
        for (month, day), (name, _) in cls.FIXED_SOLAR_HOLIDAYS.items():
            add_holiday(date(year, month, day), name)

        # 2. 음력 가변 공휴일 추가 (설날 연휴 3일, 부처님오신날, 추석 연휴 3일)
        lunar_data = cls.LUNAR_HOLIDAYS_TABLE.get(year)
        if lunar_data:
            # 설날 (전날, 당일, 다음날)
            s_m, s_d = lunar_data["seollal"]
            seollal_day = date(year, s_m, s_d)
            add_holiday(seollal_day - timedelta(days=1), "설날 전날")
            add_holiday(seollal_day, "설날")
            add_holiday(seollal_day + timedelta(days=1), "설날 다음날")

            # 부처님오신날
            b_m, b_d = lunar_data["buddha"]
            add_holiday(date(year, b_m, b_d), "부처님오신날")

            # 추석 (전날, 당일, 다음날)
            c_m, c_d = lunar_data["chuseok"]
            chuseok_day = date(year, c_m, c_d)
            add_holiday(chuseok_day - timedelta(days=1), "추석 전날")
            add_holiday(chuseok_day, "추석")
            add_holiday(chuseok_day + timedelta(days=1), "추석 다음날")

        # 3. 대체공휴일(Substitute Holidays) 동적 계산
        substitutes: dict[date, list[str]] = {}

        for holiday_date, names in list(raw_holidays.items()):
            # 한 날짜에 여러 공휴일이 겹친 경우 첫번째 공휴일 외 남은 공휴일에 대한 대체공휴일 생성
            for idx, name in enumerate(names):
                is_substitute_eligible = False
                if name in ("설날 전날", "설날", "설날 다음날", "추석 전날", "추석", "추석 다음날", "부처님오신날"):
                    is_substitute_eligible = True
                elif (holiday_date.month, holiday_date.day) in cls.FIXED_SOLAR_HOLIDAYS:
                    _, is_substitute_eligible = cls.FIXED_SOLAR_HOLIDAYS[(holiday_date.month, holiday_date.day)]

                if not is_substitute_eligible:
                    continue

                is_weekend = holiday_date.weekday() in (5, 6)
                has_multiple = len(names) > 1 and idx > 0

                if is_weekend or has_multiple:
                    sub_date = holiday_date + timedelta(days=1)
                    while sub_date.weekday() in (5, 6) or sub_date in raw_holidays or sub_date in substitutes:
                        sub_date += timedelta(days=1)
                    if sub_date not in substitutes:
                        substitutes[sub_date] = []
                    substitutes[sub_date].append(f"대체공휴일({name})")

        for d, names in substitutes.items():
            if d not in raw_holidays:
                raw_holidays[d] = []
            raw_holidays[d].extend(names)

        return raw_holidays

    @classmethod
    def is_public_holiday(cls, check_date: date) -> bool:
        """지정한 날짜가 공휴일(대체공휴일 포함)인지 판정합니다."""
        year_holidays = cls.get_holidays_for_year(check_date.year)
        return check_date in year_holidays
