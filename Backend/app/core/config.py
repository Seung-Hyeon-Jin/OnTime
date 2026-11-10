import os
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Settings(BaseSettings):
    PROJECT_NAME: str = "Transport API"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str
    SECRET_KEY: str
    ODSAY_API_KEY: str | None = None
    SUBWAY_SERVICE_KEY: str | None = None
    BUS_SERVICE_KEY: str | None = None
    GYEONGGI_BUS_SERVICE_KEY: str | None = None
    KAKAO_REST_API_KEY: str | None = None
    API_TIMEOUT_SECONDS: float = 10.0
    BUS_STOP_CSV_PATH: str = os.path.join(
        BASE_DIR,
        "국토교통부_전국 버스정류장 위치정보_20251031.csv",
    )
    ROUTE_ARRIVAL_STOP_LIMIT: int = 4
    # 실행 예정 루틴을 확인하는 worker의 주기입니다.
    ROUTINE_WORKER_INTERVAL_SECONDS: int = 60
    FIREBASE_SERVICE_ACCOUNT_PATH: str | None = None
    REDIS_URL: str | None = "redis://localhost:6379/0"
    ARRIVAL_CACHE_TTL_SECONDS: int = 20

    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

settings = Settings()