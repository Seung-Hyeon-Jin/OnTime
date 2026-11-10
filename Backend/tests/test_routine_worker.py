import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.services.notification_service import FakeNotificationProvider, NotificationService
from app.workers.routine_worker import RoutineWorker


class RoutineWorkerTest(unittest.IsolatedAsyncioTestCase):
    async def test_start_and_stop_cancel_background_loop(self):
        execution_service = SimpleNamespace(
            notification_service=NotificationService(FakeNotificationProvider()),
        )
        worker = RoutineWorker(execution_service, interval_seconds=3600)
        worker._run_loop = AsyncMock()
        await worker.start()
        await asyncio.sleep(0)
        await worker.stop()
        worker._run_loop.assert_awaited_once()
