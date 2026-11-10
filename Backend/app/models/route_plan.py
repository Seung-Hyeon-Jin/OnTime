import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RoutePlan(Base):
    # 루틴 등록 시 계산한 경로를 보존해 실행 시 다시 경로를 검색하지 않도록 합니다.
    __tablename__ = "route_plans"

    route_plan_id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    routine_id: Mapped[str] = mapped_column(
        ForeignKey("routines.routine_id"),
        unique=True,
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String, nullable=False)
    total_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    transfer_count: Mapped[int] = mapped_column(Integer, nullable=False)
    fare: Mapped[int | None] = mapped_column(Integer, nullable=True)
    route_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    routine: Mapped["Routine"] = relationship(back_populates="route_plan")

    @property
    def route(self) -> dict:
        # 응답 스키마가 저장된 JSON을 RouteResponse로 검증할 수 있게 노출합니다.
        return self.route_data