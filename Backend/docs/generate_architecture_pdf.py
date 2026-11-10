from pathlib import Path
import textwrap

from fpdf import FPDF


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "transport_app_architecture.pdf"
FONT = Path(r"C:\Windows\Fonts\malgun.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\malgunbd.ttf")


class ArchitecturePdf(FPDF):
    def header(self):
        self.set_font("Malgun", "B", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 7, "Transport App - 프로젝트 구조 문서", align="R")
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Malgun", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, f"{self.page_no()} / {{nb}}", align="C")

    def document_title(self, text: str):
        self.set_font("Malgun", "B", 20)
        self.set_text_color(30, 55, 85)
        self._write_wrapped(text, 12)
        self.ln(3)

    def section(self, text: str):
        self.ln(4)
        self.set_fill_color(30, 95, 135)
        self.set_text_color(255, 255, 255)
        self.set_font("Malgun", "B", 12)
        self.cell(0, 9, text, fill=True)
        self.ln(12)
        self.set_text_color(35, 35, 35)

    def paragraph(self, text: str):
        self.set_font("Malgun", "", 9.5)
        self.set_text_color(35, 35, 35)
        self._write_wrapped(text, 5.5)
        self.ln(2)

    def code_block(self, text: str):
        self.set_fill_color(245, 247, 249)
        self.set_draw_color(215, 220, 225)
        self.set_text_color(40, 40, 40)
        self.set_font("Malgun", "", 8.2)
        self._write_wrapped(text, 4.5, border=1, fill=True)
        self.ln(3)

    def bullet(self, text: str):
        self.set_font("Malgun", "", 9.5)
        self._write_wrapped(f"- {text}", 5.5)

    def _write_wrapped(self, text: str, height: float, border: int = 0, fill: bool = False):
        for line in text.splitlines() or [""]:
            lines = textwrap.wrap(
                line,
                width=72,
                break_long_words=True,
                break_on_hyphens=False,
            ) or [""]
            for wrapped_line in lines:
                self.multi_cell(
                  0,
                  height,
                  wrapped_line,
                  border=border,
                  fill=fill,
                  new_x="LMARGIN",
                  new_y="NEXT",
                )


def build_pdf():
    pdf = ArchitecturePdf()
    pdf.alias_nb_pages()
    pdf.set_margins(18, 18, 18)
    pdf.set_auto_page_break(True, margin=20)
    pdf.add_font("Malgun", "", str(FONT))
    pdf.add_font("Malgun", "B", str(FONT_BOLD))
    pdf.add_page()

    pdf.document_title("Transport App 프로젝트 구조도")
    pdf.paragraph("문서 목적: FastAPI 기반 교통정보 백엔드의 현재 폴더 구조, 요청 흐름, 계층별 책임을 한눈에 확인하기 위한 문서입니다.")
    pdf.paragraph("작성 기준: 2026-11-05 / 현재 구현 상태")

    pdf.section("1. 전체 폴더 구조")
    pdf.code_block("""transport_app/
|-- .env
|-- requirements.txt
|-- 전국 버스정류장 위치정보 CSV
|-- app/
|   |-- main.py
|   |-- routers/       API 진입점
|   |-- services/      업무 흐름 조합
|   |-- clients/       외부 API 통신
|   |-- repositories/  로컬 데이터 조회
|   |-- schemas/       요청/응답 모델
|   |-- models/        DB 테이블 모델
|   `-- core/          설정, DB, 인증, 의존성
`-- tests/             단위 및 응답 파싱 테스트""")

    pdf.section("2. Flutter 프론트엔드 파일 구조")
    pdf.code_block("""frontend/
|-- lib/
|   |-- main.dart                 Provider 조립 및 앱 테마
|   |-- core/
|   |   |-- config/api_config.dart API 경로·환경별 서버 주소
|   |   `-- network/api_client.dart JSON HTTP·JWT·예외 변환
|   |-- providers/                ChangeNotifier 상태 관리
|   |   |-- auth_provider.dart
|   |   |-- routine_provider.dart
|   |   |-- route_search_provider.dart
|   |   `-- arrival_provider.dart
|   |-- screens/                  화면·사용자 흐름
|   |   |-- login/splash/home/main_navigation
|   |   |-- location_search/routine_add/routine_edit
|   |   |-- arrival/profile
|   |   `-- ...
|   |-- models/                   API JSON 역직렬화 모델
|   `-- widgets/                  루틴·구간·도착 항목 재사용 위젯
|-- android/ ios/ web/ windows/   플랫폼 실행 래퍼
`-- pubspec.yaml                  Flutter 의존성·자산 선언""")
    pdf.paragraph("프론트엔드는 main.dart에서 AuthProvider를 먼저 구성하고, 인증 토큰을 RoutineProvider·RouteSearchProvider·ArrivalProvider에 전달합니다. 화면은 Provider의 상태를 구독하고 ApiClient를 통해 백엔드 계약을 호출합니다.")

    pdf.section("3. 계층 구조")
    pdf.code_block("""HTTP Client
    |
    v
Router
    |
    v
Service
    |----------------------|
    v                      v
External Client       Repository
    |                      |
    v                      v
외부 API              로컬 CSV / DB
    |
    v
Schema 응답""")
    pdf.paragraph("Router는 HTTP 요청을 받고, Service는 업무 순서를 조합합니다. Client는 외부 API 형식을 내부 Schema로 변환하며, Repository는 로컬 데이터 조회를 담당합니다.")

    pdf.section("4. 앱 시작과 의존성 구성")
    pdf.code_block("""app/main.py
  |
  |-- FastAPI 앱 생성
  |-- auth / arrivals / routes / routines 라우터 등록
  |-- lifespan 시작
       |-- HttpClient 생성
       |-- ArrivalService 생성
       |     |-- SubwayClient
       |     `-- BusClient
       `-- RouteService 생성
             |-- OdsayClient
             |-- RouteStopMatcher
             |-- BusClient
             `-- BusStopRepository (CSV 캐시)
  |
  `-- lifespan 종료: HttpClient.close()""")

    pdf.section("5. 도착정보 API 흐름")
    pdf.code_block("""GET /api/v1/arrivals/subway?station_name=강남
클라이언트
  -> arrivals.py
  -> ArrivalService
  -> SubwayClient
  -> 서울 지하철 API
  -> ArrivalResponse

GET /api/v1/arrivals/bus?city_code=31060&station_id=GGB213000129
클라이언트
  -> arrivals.py
  -> ArrivalService
  -> BusClient
  -> TAGO 버스 API
  -> resultCode 검사 / 응답 필드 변환
  -> ArrivalResponse""")
    pdf.paragraph("버스 응답은 routeno, arrtime, vehicleno, routedest, arrmsg1/2를 각각 line_name, arrival_seconds, vehicle_number, direction, arrival_message로 변환합니다.")

    pdf.section("6. ODsay 경로 검색 흐름")
    pdf.code_block("""POST /api/v1/routes/search
  |
  v
routes.py
  |
  v
RouteService
  |
  +-> OdsayClient
  |     -> ODsay searchPubTransPathT
  |     -> result.path[0].subPath 파싱
  |     -> RouteResponse / RouteSegment / RouteStop
  |
  +-> 버스 구간 정류장 추출
        -> RouteStopMatcher
        -> BusStopRepository
        -> CP949 전국 정류장 CSV
        -> TAGO station_id, city_code 확정
        -> 버스 구간 첫/마지막 정류장 중심
        -> 최대 4개 TAGO 도착정보 조회
        -> RouteStop.arrivals 또는 arrival_error 추가""")

    pdf.section("7. ODsay ID와 TAGO ID의 분리")
    pdf.paragraph("두 정류장 식별자는 같은 값이라고 가정하지 않습니다.")
    pdf.code_block("""ODsay stationID
  예: OD123
  용도: ODsay 경로 응답 내부 식별자

정류장 CSV의 정류장번호 / TAGO nodeId
  예: GGB213000129
  용도: TAGO 도착정보 API 요청값

ODsay 이름 + 좌표 + 도시정보
  -> RouteStopMatcher
  -> CSV 후보 검색
  -> 좌표 거리 비교
  -> TAGO station_id 확정""")

    pdf.section("8. CSV 저장소와 정류장 매칭")
    pdf.code_block("""BusStopRepository
  1. CP949로 CSV 로드
  2. 정류장번호, 정류장명, 위도, 경도, 도시코드, 도시명 보존
  3. 결측 식별자/좌표 행 제외
  4. lru_cache로 파일 재로딩 방지

RouteStopMatcher
  1. 정류장명 공백 정규화
  2. 도시코드로 후보 우선 축소
  3. 위도/경도 하버사인 거리 계산
  4. 500m 초과: 매칭 실패
  5. 10m 이내 동률 후보: 모호한 매칭으로 실패""")

    pdf.section("9. 인증과 루틴")
    pdf.code_block("""auth.py
  -> 회원가입 / 로그인
  -> bcrypt 비밀번호 해시
  -> JWT 발급
  -> Bearer Token 검증
  -> User 모델 조회

routines.py
  -> 인증된 사용자 확인
  -> user_id 기준 루틴 생성/조회/수정/삭제
  -> SQLAlchemy
  -> PostgreSQL users / routines 테이블""")

    pdf.section("10. 오류 처리")
    pdf.code_block("""외부 API timeout / HTTP 오류 / JSON 오류
  -> HttpClient
  -> ExternalApiError
  -> main.py 예외 핸들러
  -> HTTP 502

ODsay 또는 TAGO 경로 응답 파싱 오류
  -> ExternalApiError
  -> HTTP 502

정류장 매칭 실패 또는 모호한 후보
  -> RouteMatchingError
  -> HTTP 422

경로 일부 정류장의 TAGO 조회 실패
  -> 전체 경로는 유지
  -> 해당 RouteStop에 arrival_error 기록""")

    pdf.section("11. 핵심 파일별 책임")
    responsibilities = [
        "main.py: 앱 생성, 라우터 등록, 시작/종료 시 객체 구성, 전역 예외 처리",
        "routers/*.py: HTTP 경로와 입력 모델 연결",
        "services/*.py: 교통정보 조회와 정류장 매칭 업무 흐름",
        "clients/*.py: ODsay, TAGO, 지하철 API 호출 및 응답 파싱",
        "repositories/bus_stop_repository.py: CP949 정류장 CSV 로딩 및 캐시",
        "schemas/*.py: API 요청/응답 데이터 계약",
        "models/*.py: 사용자와 루틴의 DB 테이블 구조",
        "core/*.py: 환경설정, SQLAlchemy, JWT 인증, FastAPI 의존성",
        "tests/*.py: CSV, 정류장 매칭, 외부 API 파싱, timeout 회귀 검증",
    ]
    for item in responsibilities:
        pdf.bullet(item)

    pdf.section("12. 현재 구조에서 기억할 점")
    for item in [
        "직접 버스 도착정보 API는 이미 TAGO station_id를 받은 뒤 조회합니다.",
        "경로 검색 API는 먼저 ODsay 정류장을 받고, CSV 매칭 후 TAGO 도착정보를 추가합니다.",
        "ODsay stationID와 TAGO 정류장번호는 서로 다른 식별자입니다.",
        "경로 검색에서는 외부 API 호출 수를 줄이기 위해 버스 구간의 첫/마지막 정류장 중심으로 조회합니다.",
        "비밀값은 설정에서만 읽고 응답이나 로그에 출력하지 않습니다.",
    ]:
        pdf.bullet(item)

    pdf.output(str(OUTPUT))
    print(OUTPUT)


if __name__ == "__main__":
    build_pdf()