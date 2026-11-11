# OnTime Backend 🚀

FastAPI 기반의 OnTime 대중교통 루틴 및 실시간 정보 제공 REST API 서버

---

## 📌 주요 특징
- **FastAPI 기반 고성능 비동기 API:** Uvicorn 및 Pydantic을 활용한 엄격한 데이터 검증 및 빠른 응답 속도
- **SQLAlchemy ORM:** PostgreSQL 및 SQLite 호환 데이터 모델링 및 자동 마이그레이션 지원
- **외부 교통 API 연동:** ODsay 길찾기, 국토교통부 버스 도착정보, 서울시 지하철 실시간 정보 클라이언트 통합
- **백그라운드 루틴 워커:** 주기적인 스케줄 검사 및 알림 생성 워커 탑재

---

## ⚙️ 환경 설정 및 설치

### 1. 가상환경 생성 및 활성화
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 2. 의존성 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정 (`.env`)
`.env.example` 파일을 참고하여 `.env` 파일을 생성하고 필요한 API Key 및 데이터베이스 URL을 설정합니다.
```env
DATABASE_URL=sqlite:///./ontime.db # 또는 PostgreSQL 연결 문자열
ODSAY_API_KEY= #https://lab.odsay.com/contact/contact
SUBWAY_SERVICE_KEY= #https://data.seoul.go.kr/dataList/OA-12764/F/1/datasetView.do
BUS_SERVICE_KEY= #https://www.data.go.kr/iim/api/selectAPIAcountView.do
KAKAO_REST_API_KEY= #KAKAO LOCAL API
GYEONGGI_BUS_SERVICE_KEY= #https://www.data.go.kr/iim/api/selectAPIAcountView.do
FIREBASE_SERVICE_ACCOUNT_PATH= #푸쉬 알림을 위함, 없어도 동작 가능
SECRET_KEY= #개인의 Private한 충분한 길이의 SECRET_KEY

```

---

## ▶️ 서버 실행

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```



