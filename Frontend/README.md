# OnTime Frontend 

Flutter로 제작된 OnTime 대중교통 루틴 및 실시간 도착 정보 모바일 애플리케이션입니다.

---

## 🛠️ 기술스택 + 라이브러리
- **Framework:** Flutter (SDK `>=3.0.0 <4.0.0`)
- **State Management:** `provider`
- **Networking:** `http`
- **Location:** `geolocator`
- **Local Storage:** `shared_preferences`
- **Notifications:** `firebase_core`, `firebase_messaging`, `flutter_local_notifications`
- **UI Styling:** `google_fonts`, Material Design 3

---

## 📂 디렉토리 (`lib/`)

```text
lib/
├── core/                  # 환경 설정, 네트워크 API 클라이언트 등
├── models/                # 데이터 모델 (루틴, 경로, 도착정보, 사용자 등)
├── providers/             # 상태 관리 프로바이더 (Auth, Routine, RouteSearch)
├── screens/               # 주요 화면 (Login, Home, RoutineAdd/Edit, Profile)
├── services/              # 푸시 알림 및 외부 서비스 연동
├── utils/                 # 버스/지하철 실시간 정규화 및 필터 유틸리티
└── widgets/               # 공통 위젯 및 카드 컴포넌트
```

---

## 🚀 실행

### Before(필수)
Flutter SDK 및 안드로이드 스튜디오 설치

### 1. 의존성 패키지 다운로드
```bash
flutter pub get
```

### 2. 애플리케이션 실행
연결된 에뮬레이터 또는 실제 기기에서 실행합니다.
> **💡 주의:** 본 프로젝트는 로컬 백엔드 서버 연동 특성상 테스트 시 **PC와 모바일 기기가 동일한 Wi-Fi 네트워크**에 연결되어 있어야 합니다.  
또한, Frontend/lib/core/config/api_config.dart의 physicalPhoneIp를 실행하는 PC의 ip로 할당해야합니다.
```bash
flutter run
```


---

## ✨ 주요 화면 흐름
1. **스플래시 / 로그인 화면 (`splash_screen.dart`, `login_screen.dart`):** 사용자 인증 및 토큰 관리
2. **메인 홈 화면 (`home_screen.dart`):** 등록된 출퇴근 루틴 카드 목록 확인, 실시간 버스·지하철 도착 정보 및 환승 가능 여부 모니터링
3. **루틴 추가/수정 화면 (`routine_add_screen.dart`, `routine_edit_screen.dart`):** 출발지·도착지 검색 및 대중교통 경로 선택/수정
