import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RoutineExecution(Base):
    # 하루 단위 실행 결과를 저장해 같은 루틴의 중복 갱신과 알림을 방지합니다.
    __tablename__ = "routine_executions"
    __table_args__ = (
        UniqueConstraint("routine_id", "execution_date", name="uq_routine_execution_day"),
    )

    execution_id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    routine_id: Mapped[str] = mapped_column(
        ForeignKey("routines.routine_id"),
        nullable=False,
        index=True,
    )
    execution_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="MONITORING")
    route_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    last_checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # 실시간 조회 결과로 계산한 사용자 행동 시각을 저장합니다.
    recommended_departure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_arrival_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    transfer_feasible: Mapped[bool | None] = mapped_column(nullable=True)
    transfer_details: Mapped[list | None] = mapped_column(JSON, nullable=True)
    calculation_basis: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    routine: Mapped["Routine"] = relationship(back_populates="executions")
    notifications: Mapped[list["RoutineNotification"]] = relationship(
        back_populates="execution",
        cascade="all, delete-orphan",
    )

    @property
    def route(self) -> dict:
        # 저장된 최신 JSON을 API 응답의 RouteResponse로 검증할 수 있게 노출합니다.
        return self.route_data