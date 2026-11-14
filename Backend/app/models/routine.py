from sqlalchemy import String, Time, Boolean, ForeignKey, Integer, ARRAY, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import uuid
from datetime import time


class Routine(Base):
    __tablename__ = "routines"

    routine_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String, nullable=False)
    departure_stop: Mapped[str] = mapped_column(String, nullable=False)
    arrival_stop: Mapped[str] = mapped_column(String, nullable=False)

    # 루틴의 출발, 도착지 좌표
    departure_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    departure_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    departure_city_code: Mapped[str | None] = mapped_column(String, nullable=True)
    arrival_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    arrival_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    arrival_city_code: Mapped[str | None] = mapped_column(String, nullable=True)

    # 요일 목록 저장 
    scheduled_days: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    departure_time: Mapped[time] = mapped_column(Time, nullable=False)
    notify_mins_before: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    exclude_holidays: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)




    user: Mapped["User"] = relationship("User", back_populates="routines")
    # 루틴 하나에 현재 유효한 저장 경로 하나를 연결합니다.
    route_plan: Mapped["RoutePlan | None"] = relationship(
        back_populates="routine",
        cascade="all, delete-orphan",
        uselist=False,
    )
    
    executions: Mapped[list["RoutineExecution"]] = relationship(
        back_populates="routine",
        cascade="all, delete-orphan",
        order_by="RoutineExecution.execution_date.desc()",
    )
    notifications: Mapped[list["RoutineNotification"]] = relationship(
        back_populates="routine",
        cascade="all, delete-orphan",
    )




    @property
    def origin(self) -> dict | None:
        if self.departure_latitude is None or self.departure_longitude is None:
            return None
        return {
            "name": self.departure_stop,
            "latitude": self.departure_latitude,
            "longitude": self.departure_longitude,
            "city_code": self.departure_city_code,
        }

    @property
    def destination(self) -> dict | None:
        if self.arrival_latitude is None or self.arrival_longitude is None:
            return None
        return {
            "name": self.arrival_stop,
            "latitude": self.arrival_latitude,
            "longitude": self.arrival_longitude,
            "city_code": self.arrival_city_code,
        }