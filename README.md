# OnTime 

> 사용자 맞춤형 대중교통 출퇴근 루틴 및 실시간 도착/환승 정보 연동 서비스

사용자의 반복적인 이동 일정(루틴)을 등록하고, 출발 시점에 맞춰 최적의 대중교통 경로와 실시간 버스·지하철 도착 정보를 제공하여 지각을 방지하고 원활한 이동을 돕는 통합 대중교통 솔루션

---

## 🛠️ 기술스택

### Backend
- **Framework:** Python, FastAPI
- **Database / ORM:** PostgreSQL / SQLite (SQLAlchemy), Pydantic
- **Async Server:** Uvicorn
- **External APIs:** ODsay API (대중교통 길찾기), 국토교통부 버스정류장/도착정보, 서울시 지하철 실시간 도착정보, Kakao Local API

### Frontend
- **Framework:** Flutter (Dart 3.x)
- **State Management:** Provider
- **Networking:** HTTP Client
- **Push Notification:** Firebase Cloud Messaging (FCM), flutter_local_notifications
- **Location:** Geolocator

---

## 📂 프로젝트 구조

```text
OnTime/
├── Backend/                 # FastAPI 백엔드 서버
│   ├── app/                 # 핵심 애플리케이션 로직 (routers, services, models 등)
│   ├── tests/               # Pytest 통합 및 단위 테스트
│   ├── requirements.txt     # Python 패키지 의존성
│   └── migrations/          # 데이터베이스 마이그레이션 SQL
├── Frontend/                # Flutter 프론트엔드 앱
│   ├── lib/                 # 화면(screens), 위젯(widgets), 프로바이더(providers), 모델(models)
│   ├── test/                # Flutter 단위 및 위젯 테스트
│   └── pubspec.yaml         # Flutter 의존성 설정
└── README.md                # 전체 프로젝트 문서
```

---

## ✨ 특징
1. **사용자 인증 및 관리:** JWT 기반 회원가입, 로그인 및 토큰 보안 관리
2. **장소 및 경로 검색:** Kakao 로컬 API 및 ODsay 대중교통 길찾기 API를 통한 최적 경로 탐색
3. **루틴(Routine) 관리:** 출퇴근 등 반복 일정을 시간/요일별로 설정 및 저장
4. **실시간 도착 정보 및 환승 계산:** 저장된 경로의 버스·지하철 실시간 도착 정보를 병렬 조회하고 환승 가능성 계산
5. **푸시 알림 및 백그라운드 실행:** 정해진 시간에 루틴을 실행하고 사용자에게 알림 전달 (FCM 연동)

---

## 🚀 실행

### ⚠️ 네트워크 요구사항 (동일 무선 네트워크 필수)
- **로컬 백엔드 연동 제약:** 개발 환경에서 백엔드 서버가 로컬 PC에서 구동되므로, **앱(에뮬레이터 또는 USB 디버깅 중인 실기기)과 백엔드 서버를 실행 중인 PC가 반드시 동일한 무선 네트워크(Wi-Fi)**에 연결되어 있어야 API 통신이 정상적으로 동작합니다.
- (대안) 동일 Wi-Fi 사용이 어려운 경우, 아래의 ADB 포트 포워딩을 활용할 수 있습니다.
  ```bash
  adb reverse tcp:8000 tcp:8000
  ```

### 1. Backend 실행
```bash
cd Backend
python -m venv venv
# Windows: venv\Scripts\activate / macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
# .env 설정 후
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend 실행
```bash
cd Frontend
flutter pub get
flutter run
```
