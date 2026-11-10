BEGIN;

-- 기존 루틴에 ODsay 경로 계획을 만들기 위한 출발지·도착지 좌표를 추가합니다.
ALTER TABLE routines ADD COLUMN IF NOT EXISTS departure_latitude DOUBLE PRECISION;
ALTER TABLE routines ADD COLUMN IF NOT EXISTS departure_longitude DOUBLE PRECISION;
ALTER TABLE routines ADD COLUMN IF NOT EXISTS departure_city_code VARCHAR;
ALTER TABLE routines ADD COLUMN IF NOT EXISTS arrival_latitude DOUBLE PRECISION;
ALTER TABLE routines ADD COLUMN IF NOT EXISTS arrival_longitude DOUBLE PRECISION;
ALTER TABLE routines ADD COLUMN IF NOT EXISTS arrival_city_code VARCHAR;

-- 루틴 등록 시 계산한 경로 JSON과 요약 정보를 저장합니다.
CREATE TABLE IF NOT EXISTS route_plans (
    route_plan_id VARCHAR PRIMARY KEY,
    routine_id VARCHAR NOT NULL UNIQUE REFERENCES routines(routine_id),
    provider VARCHAR NOT NULL,
    total_duration_minutes INTEGER NOT NULL,
    transfer_count INTEGER NOT NULL,
    fare INTEGER,
    route_data JSON NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

-- 실행 시점의 최신 도착정보와 확인 시각을 하루 단위로 저장합니다.
CREATE TABLE IF NOT EXISTS routine_executions (
    execution_id VARCHAR PRIMARY KEY,
    routine_id VARCHAR NOT NULL REFERENCES routines(routine_id),
    execution_date DATE NOT NULL,
    status VARCHAR NOT NULL,
    route_data JSON NOT NULL,
    last_checked_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_routine_execution_day UNIQUE (routine_id, execution_date)
);

-- 실행 결과에 출발·도착 예상시각과 환승 가능성을 저장합니다.
ALTER TABLE routine_executions ADD COLUMN IF NOT EXISTS recommended_departure_at TIMESTAMPTZ;
ALTER TABLE routine_executions ADD COLUMN IF NOT EXISTS estimated_arrival_at TIMESTAMPTZ;
ALTER TABLE routine_executions ADD COLUMN IF NOT EXISTS transfer_feasible BOOLEAN;
ALTER TABLE routine_executions ADD COLUMN IF NOT EXISTS transfer_details JSON;
ALTER TABLE routine_executions ADD COLUMN IF NOT EXISTS calculation_basis JSON;

-- 외부 푸시 전송을 위한 알림 대기열을 저장합니다.
CREATE TABLE IF NOT EXISTS routine_notifications (
    notification_id VARCHAR PRIMARY KEY,
    routine_id VARCHAR NOT NULL REFERENCES routines(routine_id),
    execution_id VARCHAR NOT NULL UNIQUE REFERENCES routine_executions(execution_id),
    title VARCHAR NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    sent_at TIMESTAMPTZ,
    last_error TEXT
);
ALTER TABLE routine_notifications ADD COLUMN IF NOT EXISTS last_error TEXT;

COMMIT;
