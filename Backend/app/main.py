from fastapi import FastAPI, Depends, Request
from contextlib import asynccontextmanager
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse


from app.core.config import settings
from app.core.database import  engine, Base
from app.core.database import get_db
from app.models.route_plan import RoutePlan  # noqa: F401 - 테이블 등록을 위해 import
from app.models.routine_execution import RoutineExecution  # noqa: F401 - 테이블 등록을 위해 import
from app.models.routine_notification import RoutineNotification  # noqa: F401 - 테이블 등록을 위해 import

from app.routers import auth, routines, arrivals, routes, locations
from app.clients.bus_client import BusClient
from app.clients.http_client import ExternalApiError, HttpClient
from app.clients.odsay_client import OdsayClient
from app.clients.subway_client import SubwayClient
from app.clients.kakao_client import KakaoClient
from app.services.arrival_service import ArrivalService
from app.services.route_matching_service import RouteMatchingError, RouteStopMatcher
from app.services.route_service import RouteService
from app.services.routine_execution_service import RoutineExecutionService
from app.services.notification_service import NotificationService
from app.services.schedule_service import ScheduleService
from app.workers.routine_worker import RoutineWorker
from app.repositories.bus_stop_repository import BusStopRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    http_client = HttpClient(settings.API_TIMEOUT_SECONDS)

    app.state.kakao_client = KakaoClient(http_client)
    app.state.arrival_service = ArrivalService(
        subway_client= SubwayClient(http_client),
        bus_client= BusClient(http_client)
    )
    bus_client = app.state.arrival_service.bus_client
    subway_client = app.state.arrival_service.subway_client
    bus_stop_repository = BusStopRepository(settings.BUS_STOP_CSV_PATH)
    app.state.bus_stop_repository = bus_stop_repository
    app.state.route_service = RouteService(
        odsay_client=OdsayClient(http_client),
        matcher=RouteStopMatcher(bus_stop_repository),
        bus_client=bus_client,
        subway_client=subway_client,
        arrival_limit=settings.ROUTE_ARRIVAL_STOP_LIMIT,
    )
    # 실행 API가 저장 경로를 실시간 경로로 갱신할 수 있도록 서비스를 등록합니다.
    app.state.routine_execution_service = RoutineExecutionService(
        app.state.route_service,
        ScheduleService(),
        NotificationService(),
    )
    routine_worker = RoutineWorker(
        app.state.routine_execution_service,
        settings.ROUTINE_WORKER_INTERVAL_SECONDS,
        app.state.routine_execution_service.notification_service,
    )
    app.state.routine_worker = routine_worker
    await routine_worker.start()
    yield

    await routine_worker.stop()
    await http_client.close()

Base.metadata.create_all(bind=engine)

# PostgreSQL 마이그레이션: users 및 notification 외래키 제약조건(CASCADE DELETE) 자동 업데이트
try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS token_version INTEGER DEFAULT 1;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS device_token VARCHAR;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS notifications_enabled BOOLEAN NOT NULL DEFAULT TRUE;"))
        conn.execute(text("ALTER TABLE routine_notifications DROP CONSTRAINT IF EXISTS routine_notifications_execution_id_fkey;"))
        conn.execute(text("ALTER TABLE routine_notifications ADD CONSTRAINT routine_notifications_execution_id_fkey FOREIGN KEY (execution_id) REFERENCES routine_executions(execution_id) ON DELETE CASCADE;"))
        conn.commit()
except Exception as e:
    print(f"Auto migration note: {e}")

app = FastAPI(
    title= settings.PROJECT_NAME,
    description="임시",
    version="0.0.0",
    lifespan=lifespan
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(routines.router)
app.include_router(arrivals.router)
app.include_router(routes.router)
app.include_router(locations.router)


@app.exception_handler(ExternalApiError)
async def external_api_error_handler(
    request: Request,
    exc: ExternalApiError,
) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content={
            "detail": exc.message,
            "provider": exc.provider,
        },
    )


@app.exception_handler(RouteMatchingError)
async def route_matching_error_handler(
    request: Request,
    exc: RouteMatchingError,
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})



@app.get("/")
def read_root():
    return {"message":"정상 실행 중"}


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected", "message": "시스템과 DB 모두 건강합니다."}
    except Exception as e:
        # 연결 실패 시 에러 메시지 반환
        return {"status": "error", "database": "disconnected", "details": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app",host="127.0.0.1", port=8000, reload= True)