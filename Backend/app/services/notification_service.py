import asyncio
from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.routine import Routine
from app.models.routine_execution import RoutineExecution
from app.models.routine_notification import RoutineNotification
from app.services.schedule_service import TimingEstimate


class NotificationProvider(Protocol):
    async def send(self, *, token: str, title: str, message: str) -> str:
        ...


class NotificationDeliveryError(Exception):
    """시연용 알림 전송 실패를 호출부에 전달합니다."""


class FakeNotificationProvider:
    """실제 푸시 자격증명 없이 발표와 테스트에서 사용하는 알림 provider입니다."""

    def __init__(self, fail: bool = False):
        self.fail = fail
        self.sent: list[dict[str, str]] = []

    async def send(self, *, token: str, title: str, message: str) -> str:
        if self.fail:
            raise NotificationDeliveryError("fake provider failure")
        self.sent.append({"token": token, "title": title, "message": message})
        return "fake-message-id"


class FirebaseNotificationProvider:
    def __init__(self, service_account_path: str):
        import firebase_admin
        from firebase_admin import credentials

        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.Certificate(service_account_path))

    async def send(self, *, token: str, title: str, message: str) -> str:
        from firebase_admin import messaging

        def send_message() -> str:
            return messaging.send(
                messaging.Message(
                    token=token,
                    notification=messaging.Notification(title=title, body=message),
                )
            )

        try:
            return await asyncio.to_thread(send_message)
        except Exception as exc:
            raise NotificationDeliveryError(f"Firebase 전송 실패: {exc}") from exc


class NotificationService:
    def __init__(self, provider: NotificationProvider | None = None):
        if provider is not None:
            self.provider = provider
            return

        service_account_path = settings.FIREBASE_SERVICE_ACCOUNT_PATH
        self.provider = (
            FirebaseNotificationProvider(service_account_path)
            if service_account_path
            else FakeNotificationProvider()
        )

    @staticmethod
    def _normalize_line(name: str) -> str:
        if not name:
            return ""
        cleaned = "".join(name.split()).removesuffix("번")
        prefixes = ["마을", "일반", "지선", "간선", "직행", "좌석", "광역", "시내"]
        for prefix in prefixes:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):]
        return cleaned.strip()

    @classmethod
    def _arrival_text(cls, arrival: dict) -> str:
        raw_message = str(arrival.get("arrival_message") or "").strip()
        seconds = arrival.get("arrival_seconds")

        # 1. arrival_seconds가 숫자로 존재하는 경우
        if seconds is not None:
            minutes = max(0, seconds // 60)
            return "곧 도착" if minutes == 0 else f"{minutes}분 후"

        # 2. arrival_seconds가 없지만 raw_message가 유효한 도착 메시지인 경우 (예: "전역 진입", "당역 도착", "곧 도착", "3분[2개 전거장]")
        if raw_message and not any(k in raw_message for k in ("운행종료", "운행 종료", "정보 없음", "정보없음")):
            return raw_message

        return "도착정보없음"

    @classmethod
    def _has_valid_arrival_info(cls, arrival: dict) -> bool:
        return cls._arrival_text(arrival) != "도착정보없음"

    @classmethod
    def build_realtime_status_message(cls, routine: Routine, execution: RoutineExecution) -> tuple[str, str]:
        """실시간 대중교통(지정 버스/지하철) 도착 정보를 바탕으로
        사용자 스마트폰 알림창에 표출할 푸시 메시지를 동적으로 생성합니다.
        (첫 번째 대중교통 구간 기준)
        """
        route_data = execution.route_data or {}
        segments = route_data.get("segments", [])

        title = routine.name

        first_transit_segment = None
        for segment in segments:
            if segment.get("transport_type") in {"BUS", "SUBWAY"}:
                first_transit_segment = segment
                break

        if not first_transit_segment:
            return title, "도착정보없음"

        segment_line = first_transit_segment.get("line_name") or ""
        arrivals = []
        for stop in first_transit_segment.get("stops", []):
            for arrival in stop.get("arrivals", []):
                item = dict(arrival)
                if not item.get("line_name"):
                    item["line_name"] = segment_line
                item.setdefault("transport_type", first_transit_segment.get("transport_type"))
                arrivals.append(item)
        ordered_arrivals = sorted(
            arrivals,
            key=lambda arrival: (
                not cls._has_valid_arrival_info(arrival),
                arrival.get("arrival_seconds") is None,
                arrival.get("arrival_seconds") or 0,
            ),
        )
        arrival_lines = []
        seen_arrivals = set()
        for arrival in ordered_arrivals:
            line = arrival.get("line_name") or "대중교통"
            if (
                arrival.get("transport_type") == "BUS"
                and not line.endswith("번")
            ):
                line = f"{line}번"
            arrival_str = cls._arrival_text(arrival)
            item = f"{line}, {arrival_str}"
            if item in seen_arrivals:
                continue
            seen_arrivals.add(item)
            arrival_lines.append(item)
            if len(arrival_lines) == 2:
                break

        valid_lines = [l for l in arrival_lines if not l.endswith("도착정보없음")]
        if valid_lines:
            return title, "\n".join(valid_lines)
        elif arrival_lines:
            return title, "\n".join(arrival_lines)

        message = "도착정보없음"
        return title, message

    def enqueue_departure(
        self,
        routine: Routine,
        execution: RoutineExecution,
        estimate: TimingEstimate,
        db: Session,
    ) -> RoutineNotification:
        title, message = self.build_realtime_status_message(routine, execution)

        notification = RoutineNotification(
            routine_id=routine.routine_id,
            execution_id=execution.execution_id,
            title=title,
            message=message,
            status="PENDING",
            created_at=datetime.now(timezone.utc),
        )
        db.add(notification)
        return notification

    async def send_pending(
        self,
        notification: RoutineNotification,
        routine: Routine,
        db: Session,
    ) -> RoutineNotification:
        if notification.status == "SENT":
            return notification

        user = getattr(routine, "user", None)
        if user is not None and getattr(user, "notifications_enabled", True) is False:
            notification.status = "SKIPPED"
            notification.last_error = "사용자가 알림을 껐습니다."
            db.commit()
            return notification
        token = getattr(user, "device_token", None)
        if not token:
            notification.status = "FAILED"
            notification.last_error = "사용자 기기 토큰이 없습니다."
            db.commit()
            return notification

        try:
            await self.provider.send(
                token=token,
                title=notification.title,
                message=notification.message,
            )
        except NotificationDeliveryError as exc:
            notification.status = "FAILED"
            notification.last_error = str(exc)
        else:
            notification.status = "SENT"
            notification.sent_at = datetime.now(timezone.utc)
            notification.last_error = None
        db.commit()
        return notification
