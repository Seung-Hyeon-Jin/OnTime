import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.core.database import SessionLocal
from app.models.routine import Routine
from app.models.routine_notification import RoutineNotification
from app.clients.http_client import ExternalApiError
from app.services.notification_service import NotificationService
from app.services.routine_execution_service import RoutineExecutionService

from app.services.holiday_service import HolidayService

logger = logging.getLogger(__name__)


class RoutineWorker:
    def __init__(
        self,
        execution_service: RoutineExecutionService,
        interval_seconds: int = 60,
        notification_service: NotificationService | None = None,
    ):
        self.execution_service = execution_service
        self.interval_seconds = interval_seconds
        self._task: asyncio.Task | None = None
        self._run_lock = asyncio.Lock()
        self.notification_service = notification_service or execution_service.notification_service

    async def start(self) -> None:
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        # 서버가 종료될 때 백그라운드 작업 정리
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def run_due_once(self, now: datetime | None = None) -> None:
        # 테스트와 수동 실행에서 같은 스케줄 판정 로직을 재사용할 수 있게 한 번만 검사합니다.
        if self._run_lock.locked():
            return
        async with self._run_lock:
            await self._run_due_once(now)

    @staticmethod
    def _is_public_holiday(check_date) -> bool:
        return HolidayService.is_public_holiday(check_date)

    async def _run_due_once(self, now: datetime | None = None) -> None:
        current_time = now or datetime.now(timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)
        current_time = current_time.astimezone()
        weekday = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")[current_time.weekday()]
        db = SessionLocal()
        try:
            routines = db.query(Routine).filter(Routine.enabled.is_(True)).all()
            for routine in routines:
                if not getattr(routine.user, "notifications_enabled", True):
                    continue
                if weekday not in routine.scheduled_days or routine.route_plan is None:
                    continue

                # 공휴일 알림 스킵 옵션 처리
                if getattr(routine, "exclude_holidays", False) and self._is_public_holiday(current_time.date()):
                    logger.info("루틴(%s) 공휴일 알림 스킵", routine.name)
                    continue

                scheduled_at = current_time.replace(
                    hour=routine.departure_time.hour,
                    minute=routine.departure_time.minute,
                    second=0,
                    microsecond=0,
                )
                notify_start_at = scheduled_at - timedelta(minutes=routine.notify_mins_before)

                # N분 전부터 출발 정시까지 5분 간격 실시간 푸시 알림 발송
                if notify_start_at <= current_time <= scheduled_at:
                    try:
                        execution = await self.execution_service.refresh(
                            routine,
                            db,
                            current_time.date(),
                        )

                        last_notif = (
                            db.query(RoutineNotification)
                            .filter(RoutineNotification.execution_id == execution.execution_id)
                            .order_by(RoutineNotification.created_at.desc())
                            .first()
                        )

                        should_send = False
                        if last_notif is None:
                            should_send = True
                        else:
                            last_time = (
                                last_notif.created_at.astimezone()
                                if last_notif.created_at.tzinfo
                                else last_notif.created_at.replace(tzinfo=timezone.utc).astimezone()
                            )
                            if (current_time - last_time).total_seconds() >= 270:
                                should_send = True

                        if should_send and last_notif is not None:
                            await self.notification_service.send_pending(last_notif, routine, db)
                    except asyncio.CancelledError:
                        raise
                    except Exception as exc:
                        category = exc.category if isinstance(exc, ExternalApiError) else "unexpected"
                        logger.exception(
                            "루틴 갱신 실패(%s, category=%s): %s",
                            routine.routine_id,
                            category,
                            exc,
                        )
        finally:
            db.close()

    async def _run_loop(self) -> None:
        while True:
            try:
                await self.run_due_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                # DB 오류 등 전체 검사 실패도 다음 주기에 자동으로 재시도합니다.
                logger.exception("루틴 worker 검사 실패")
            await asyncio.sleep(self.interval_seconds)