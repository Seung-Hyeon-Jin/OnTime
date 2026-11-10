from sqlalchemy import Boolean, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import uuid


class User(Base):
    __tablename__ = "users"

    # User 객체의 주요 속성 정의
    user_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)

    # 인증을 위한 비밀번호 해싱 저장 (보고서 4.2.4 보안 요구사항 반영)[cite: 1]
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    # 졸업작품 시연에서 사용할 단일 기기 token만 저장합니다.
    device_token: Mapped[str | None] = mapped_column(String, nullable=True)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # User와 Routine의 1:N 관계 설정[cite: 1]
    routines: Mapped[list["Routine"]] = relationship("Routine", back_populates="user", cascade="all, delete-orphan")

    # 토큰 버전 관리를 위한 필드
    token_version: Mapped[int] = mapped_column(Integer, default=1, nullable = False)