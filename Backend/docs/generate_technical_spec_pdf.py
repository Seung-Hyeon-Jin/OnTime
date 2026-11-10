from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "transport_app_technical_specification.pdf"


def register_korean_font() -> str:
    candidates = [
        Path("C:/Windows/Fonts/malgun.ttf"),
        Path("C:/Windows/Fonts/NanumGothic.ttf"),
    ]
    for path in candidates:
        if path.exists():
            pdfmetrics.registerFont(TTFont("Korean", str(path)))
            return "Korean"
    return "Helvetica"


def build_styles(font: str):
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleKorean",
            parent=base["Title"],
            fontName=font,
            fontSize=25,
            leading=34,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#191F28"),
            spaceAfter=12,
        ),
        "subtitle": ParagraphStyle(
            "SubtitleKorean",
            parent=base["Normal"],
            fontName=font,
            fontSize=11,
            leading=18,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#4E5968"),
            spaceAfter=20,
        ),
        "h1": ParagraphStyle(
            "Heading1Korean",
            parent=base["Heading1"],
            fontName=font,
            fontSize=17,
            leading=24,
            textColor=colors.HexColor("#191F28"),
            spaceBefore=8,
            spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "Heading2Korean",
            parent=base["Heading2"],
            fontName=font,
            fontSize=12,
            leading=18,
            textColor=colors.HexColor("#3182F6"),
            spaceBefore=8,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "BodyKorean",
            parent=base["BodyText"],
            fontName=font,
            fontSize=9.2,
            leading=15,
            textColor=colors.HexColor("#333D4B"),
            spaceAfter=6,
        ),
        "small": ParagraphStyle(
            "SmallKorean",
            parent=base["BodyText"],
            fontName=font,
            fontSize=8,
            leading=12,
            textColor=colors.HexColor("#4E5968"),
        ),
        "callout": ParagraphStyle(
            "CalloutKorean",
            parent=base["BodyText"],
            fontName=font,
            fontSize=10,
            leading=16,
            textColor=colors.HexColor("#191F28"),
            leftIndent=8,
            rightIndent=8,
            spaceBefore=5,
            spaceAfter=8,
        ),
        "table": ParagraphStyle(
            "TableKorean",
            parent=base["BodyText"],
            fontName=font,
            fontSize=7.4,
            leading=10,
            textColor=colors.HexColor("#333D4B"),
        ),
    }


def p(text: str, style) -> Paragraph:
    return Paragraph(text, style)


def table(rows, styles, widths=None):
    converted = [
        [p(str(cell), styles["table"]) for cell in row]
        for row in rows
    ]
    result = Table(converted, colWidths=widths, repeatRows=1, hAlign="LEFT")
    result.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8F3FF")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#191F28")),
                ("FONTNAME", (0, 0), (-1, -1), styles["table"].fontName),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D9E2EC")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return result


def footer(canvas, document):
    canvas.saveState()
    canvas.setFont(document.font_name, 7.5)
    canvas.setFillColor(colors.HexColor("#8B95A1"))
    canvas.drawString(18 * mm, 10 * mm, "OnTime transport_app 기술 명세서")
    canvas.drawRightString(
        A4[0] - 18 * mm,
        10 * mm,
        f"{document.page}",
    )
    canvas.restoreState()


def make_story(styles):
    story = []
    story.extend(
        [
            Spacer(1, 32 * mm),
            p("OnTime", styles["title"]),
            p("대중교통 루틴 및 실시간 도착정보 서비스<br/>백엔드 · 프론트엔드 기술 명세서", styles["subtitle"]),
            Spacer(1, 8 * mm),
            p(
                "<b>발표용 문서</b><br/>"
                "작성 기준: 2026-11-05<br/>"
                "대상 저장소: Seung-Hyeon-Jin/transport_app",
                styles["callout"],
            ),
            Spacer(1, 20 * mm),
            p(
                "이 문서는 사용자가 출퇴근 루틴을 등록하고, 저장된 경로를 기반으로 "
                "버스·지하철 도착정보와 환승 가능성을 조회하는 전체 구현을 설명한다.",
                styles["body"],
            ),
            PageBreak(),
        ]
    )

    story += [
        p("1. 서비스 개요", styles["h1"]),
        p(
            "OnTime은 출발지·도착지와 반복 일정을 루틴으로 저장하고, "
            "사용자가 실시간 상태 조회를 누르면 저장된 경로의 도착정보를 다시 조회하는 서비스다.",
            styles["body"],
        ),
        table(
            [
                ["구분", "내용"],
                ["핵심 사용자 흐름", "회원가입/로그인 → 장소 선택 → 경로 검색 → 루틴 저장 → 실시간 상태 조회"],
                ["주요 교통수단", "버스, 지하철, 도보"],
                ["실시간 정보", "국토교통부 버스 도착정보, 서울시 지하철 실시간 도착정보"],
                ["경로 검색", "ODsay 대중교통 경로 API"],
                ["프론트엔드", "Flutter, Provider, HTTP, SharedPreferences"],
                ["백엔드", "FastAPI, Pydantic, SQLAlchemy, PostgreSQL 호환 DB"],
            ],
            styles,
            [38 * mm, 135 * mm],
        ),
        Spacer(1, 8),
        p("발표 핵심 메시지", styles["h2"]),
        p(
            "루틴 등록 시에는 비용이 큰 실시간 조회를 하지 않고 경로 계획만 저장한다. "
            "조회 시점에 저장된 기본 경로와 대체 경로를 모두 갱신한 후, "
            "도착정보 오류와 환승 불가를 우선 회피하여 최종 경로를 선택한다.",
            styles["callout"],
        ),
        p("2. 전체 아키텍처", styles["h1"]),
        table(
            [
                ["계층", "주요 구성", "책임"],
                ["Flutter UI", "HomeScreen, RoutineCard, ArrivalScreen", "입력, 상태 표시, 실시간 조회 버튼"],
                ["상태 관리", "AuthProvider, RoutineProvider, ArrivalProvider", "인증 토큰, 루틴, 조회 상태 관리"],
                ["API client", "ApiClient", "JSON HTTP, Bearer 인증, 오류 변환"],
                ["FastAPI router", "auth, locations, routes, routines, arrivals", "HTTP 계약과 사용자 권한 검증"],
                ["Service", "RouteService, ArrivalService, RoutineExecutionService", "경로·도착정보·실행 계산"],
                ["External clients", "OdsayClient, BusClient, SubwayClient, KakaoClient", "외부 API 호출 및 응답 파싱"],
                ["Persistence", "Routine, RoutePlan, RoutineExecution", "루틴·저장 경로·당일 실행 결과 보관"],
            ],
            styles,
            [30 * mm, 58 * mm, 85 * mm],
        ),
        p("핵심 사용자·시스템 흐름도", styles["h2"]),
        p(
            "<b>Flutter 화면</b> → <b>Provider</b> → <b>ApiClient</b> → "
            "<b>FastAPI Router</b> → <b>Service</b> → "
            "<b>외부 교통 API/DB</b><br/>"
            "회원가입·로그인 → JWT 발급·저장 → 장소 검색 → ODsay 경로 검색 → "
            "루틴 저장(RoutePlan) → 실행 버튼 → 도착정보 병렬 갱신 → "
            "환승 가능성 계산 → RoutineExecution/Notification 저장 → 화면 표시",
            styles["callout"],
        ),
        PageBreak(),
    ]

    story += [
        p("3. 백엔드 API 명세", styles["h1"]),
        p("공통 규칙: 보호된 API는 <b>Authorization: Bearer &lt;JWT&gt;</b>를 사용하며, JSON을 주고받는다.", styles["body"]),
        table(
            [
                ["Method", "Endpoint", "용도", "인증"],
                ["POST", "/api/v1/auth/register", "회원가입 및 access token 발급", "없음"],
                ["POST", "/api/v1/auth/login", "로그인 및 access token 발급", "없음"],
                ["GET", "/api/v1/auth/me", "현재 사용자 조회", "필요"],
                ["GET", "/api/v1/locations/search", "장소 검색", "필요"],
                ["GET", "/api/v1/locations/reverse-geocode", "좌표 → 주소/장소 변환", "필요"],
                ["POST", "/api/v1/routes/search", "출발지·도착지 경로 검색", "필요"],
                ["GET", "/api/v1/arrivals/subway?station_name=...", "역 실시간 도착정보", "필요"],
                ["GET", "/api/v1/arrivals/bus?city_code=...&station_id=...", "정류장 버스 도착정보", "필요"],
                ["GET", "/api/v1/routines", "내 루틴 목록", "필요"],
                ["POST", "/api/v1/routines", "루틴 생성 및 경로 계획 저장", "필요"],
                ["POST", "/api/v1/routines/{id}/execute", "실시간 갱신 및 실행 결과 생성", "필요"],
                ["DELETE", "/api/v1/routines/{id}", "루틴 삭제", "필요"],
            ],
            styles,
            [17 * mm, 58 * mm, 72 * mm, 22 * mm],
        ),
        p("실시간 실행 응답 핵심 필드", styles["h2"]),
        table(
            [
                ["필드", "설명"],
                ["route.segments[].transport_type", "BUS, SUBWAY, WALK 중 하나"],
                ["route.segments[].stops[].arrivals", "해당 정류장/역의 실시간 도착 항목"],
                ["arrival_seconds", "도착까지 남은 초"],
                ["arrival_message", "API가 제공하는 안내 문구"],
                ["recommended_departure_at", "루틴 출발시간과 첫 도보 구간을 고려한 권장 출발 시각"],
                ["estimated_arrival_at", "현재 시각 기준 경로 완료 예상 시각"],
                ["transfer_feasible", "환승 가능 여부"],
            ],
            styles,
            [58 * mm, 111 * mm],
        ),
        p("4. 외부 API 및 데이터 파싱", styles["h1"]),
        table(
            [
                ["연동 대상", "클라이언트", "사용 목적", "주요 변환"],
                ["ODsay", "OdsayClient", "대중교통 경로 및 대체 경로", "trafficType 1/2/3 → SUBWAY/BUS/WALK"],
                ["국토교통부 공공데이터", "BusClient", "버스 정류장 도착정보", "arrtime → arrival_seconds, routeno → line_name"],
                ["서울 열린데이터", "SubwayClient", "서울 지하철 도착정보", "barvlDt → arrival_seconds, subwayId → 노선명"],
                ["Kakao", "KakaoClient", "장소 검색 및 역지오코딩", "검색 결과를 Location으로 정규화"],
            ],
            styles,
            [42 * mm, 35 * mm, 55 * mm, 37 * mm],
        ),
        PageBreak(),
    ]

    story += [
        p("5. 루틴 저장 및 실시간 실행 알고리즘", styles["h1"]),
        p("5.1 루틴 등록", styles["h2"]),
        p(
            "좌표가 포함된 루틴 생성 요청은 ODsay 경로를 검색하고, "
            "실시간 도착정보는 조회하지 않은 채 RoutePlan.route_data에 경로 JSON을 저장한다. "
            "이렇게 하면 등록 시 외부 실시간 API를 불필요하게 호출하지 않는다.",
            styles["body"],
        ),
        p("5.2 실시간 상태 조회", styles["h2"]),
        table(
            [
                ["단계", "처리"],
                ["1", "프론트 RoutineCard가 POST /routines/{id}/execute 호출"],
                ["2", "백엔드가 루틴 소유권과 저장된 route_plan 확인"],
                ["3", "기본 경로와 alternatives를 모두 후보로 수집"],
                ["4", "각 후보의 버스 경계 정류장과 지하철 경계 역을 선택"],
                ["5", "asyncio.gather로 버스·지하철 도착 API를 병렬 호출"],
                ["6", "각 stop에 arrivals 또는 arrival_error를 반영"],
                ["7", "모든 후보가 갱신된 뒤 최종 경로를 선택"],
                ["8", "당일 RoutineExecution을 생성하거나 최신 결과로 갱신"],
                ["9", "프론트가 transport_type과 line_name을 기준으로 실제 결과만 표시"],
            ],
            styles,
            [18 * mm, 151 * mm],
        ),
        p("5.3 경로 선택 점수", styles["h2"]),
        p(
            "각 경로는 다음 우선순위의 튜플로 비교한다: "
            "<b>(도착정보 오류 여부, 환승 불가 여부, 총 소요시간, 환승 횟수, 요금)</b>. "
            "파이썬 튜플의 오름차순 비교를 이용하므로 오류가 없는 경로, 환승 가능한 경로가 먼저 선택된다.",
            styles["body"],
        ),
        p("5.4 도착정보 표시 필터", styles["h2"]),
        p(
            "프론트는 실행 경로의 모든 stop을 순회하되, "
            "<b>transport_type == BUS</b>인 항목만 버스 영역으로 보낸다. "
            "주 노선은 노선명 trim 후 정확히 일치하는 항목으로 분류하고, "
            "나머지 버스만 대체 버스로 표시한다. 데이터가 없을 때는 임의의 도착시간을 만들지 않고 빈 상태를 표시한다.",
            styles["body"],
        ),
        p("6. 시간 계산 및 환승 판정", styles["h1"]),
        table(
            [
                ["계산", "현재 구현"],
                ["첫 대기시간", "첫 BUS/SUBWAY 구간 첫 정류장의 arrival_seconds 최솟값"],
                ["권장 출발", "루틴 departure_time - 첫 WALK 구간 시간"],
                ["환승 가능", "이동·도보·버퍼 후 도착 가능한 다음 차량이 존재하는지 판정"],
                ["예상 도착", "현재 시각 + 첫 대기 + 환승 도보시간 + ODsay 총 소요시간"],
                ["시간표", "현재 EmptyScheduleProvider이며 실시간 도착정보 기반 fallback 사용"],
            ],
            styles,
            [42 * mm, 129 * mm],
        ),
        p(
            "주의: 화면의 ‘예상 도착’은 첫 버스가 도착하는 시각이 아니라 "
            "현재 시각을 기준으로 계산한 전체 경로 완료 예상 시각이다.",
            styles["callout"],
        ),
        PageBreak(),
    ]

    story += [
        p("7. 프론트엔드 명세", styles["h1"]),
        table(
            [
                ["구성", "역할"],
                ["AuthProvider", "JWT 저장/복원, 로그인, 현재 사용자 조회"],
                ["RoutineProvider", "루틴 목록, 생성/삭제, execute 결과 보관"],
                ["ArrivalProvider", "역/정류장 직접 조회 화면의 로딩·오류·결과 상태"],
                ["ApiClient", "기본 URL 구성, JSON encode/decode, timeout, ApiException 변환"],
                ["RoutineCard", "루틴별 실행 버튼, 환승 상태, 주/대체 버스 표시"],
                ["ArrivalScreen", "지하철 실시간/버스 정류장 직접 검색 UI"],
                ["RouteResponseModel", "segments, stops, arrivals, alternatives 역직렬화"],
            ],
            styles,
            [45 * mm, 126 * mm],
        ),
        p("인증 및 네트워크 처리", styles["h2"]),
        p(
            "ApiClient는 토큰이 있을 때 Authorization 헤더에 실제 JWT를 "
            "<b>Bearer $token</b> 형식으로 넣는다. HTTP 2xx가 아니면 서버 detail을 우선 추출하고, "
            "네트워크·timeout은 사용자에게 표시 가능한 ApiException으로 변환한다.",
            styles["body"],
        ),
        p("8. 데이터 모델 및 저장 전략", styles["h1"]),
        table(
            [
                ["모델", "저장 내용", "목적"],
                ["Routine", "이름, 출발/도착, 요일, 출발시간, 알림 설정", "사용자 루틴 정의"],
                ["RoutePlan", "provider, duration, transfer_count, route_data JSON", "등록 당시의 경로 계획 재사용"],
                ["RoutineExecution", "execution_date, 갱신 route_data, 계산 결과", "당일 최신 실시간 결과 보관"],
                ["RoutineNotification", "실행 결과에 대한 알림 outbox", "알림 전송 이력/재시도 기반"],
            ],
            styles,
            [39 * mm, 78 * mm, 54 * mm],
        ),
        p(
            "RoutePlan은 루틴당 하나의 현재 계획을 갖고, RoutineExecution은 루틴과 날짜의 조합으로 "
            "하루 한 건을 갱신한다. 이 구조로 같은 날 반복 조회해도 실행 기록이 중복 생성되지 않는다.",
            styles["body"],
        ),
        p("9. 오류 처리 및 보안", styles["h1"]),
        table(
            [
                ["영역", "처리 방식"],
                ["인증", "JWT sub와 token version을 사용자 DB와 비교"],
                ["소유권", "routine_id와 현재 user_id를 함께 조회"],
                ["외부 API", "응답 헤더/구조/결과코드 검증 후 도메인 응답으로 변환"],
                ["정류장 매칭", "이름 후보를 찾고 좌표 거리 1,000m 이내 최단 후보 선택"],
                ["부분 장애", "stop별 arrival_error를 남기고 다른 후보/교통수단 조회는 계속"],
                ["프론트 빈 상태", "실제 정보가 없으면 ‘정보 없음’을 표시하며 임의 샘플을 사용하지 않음"],
            ],
            styles,
            [35 * mm, 136 * mm],
        ),
        PageBreak(),
    ]

    story += [
        p("10. 검증 결과", styles["h1"]),
        table(
            [
                ["검증 대상", "결과"],
                ["Python 전체 테스트", "20개 테스트 통과"],
                ["실시간 경로 재현 테스트", "대체 경로도 arrivals를 가진 상태에서 선택되는 것을 확인"],
                ["변경 Dart 파일 분석", "api_client.dart, routine_card.dart: No issues found"],
                ["인증 헤더 검증", "placeholder ****** 대신 Bearer $token 생성 확인"],
                ["가짜 표시 검증", "8분/2분/5분 고정 fallback 제거 확인"],
                ["실사용 확인", "백엔드 실행 후 API 응답이 화면에 도착정보로 반영되는 흐름 확인"],
            ],
            styles,
            [60 * mm, 111 * mm],
        ),
        p("11. 현재 범위와 발표 시 설명할 한계", styles["h1"]),
        table(
            [
                ["항목", "현재 상태 / 후속 개선"],
                ["자동 polling", "현재는 사용자가 버튼을 눌러 1회 갱신. 주기적 갱신은 후속 기능"],
                ["시간표 provider", "EmptyScheduleProvider. 정식 시간표 저장소 연동 필요"],
                ["대체 버스 의미", "현재 같은 갱신 정류장에서 받은 다른 BUS 노선을 표시. 방면/승차 가능성 정밀 판정은 확장 대상"],
                ["정류장 조회 범위", "구간별 경계 정류장 중심. 모든 경유 정류장 조회는 API 비용과 응답시간 고려 필요"],
                ["예상 도착 문구", "전체 경로 완료 예상 시각임을 UI에서 더 명확히 구분할 수 있음"],
            ],
            styles,
            [43 * mm, 128 * mm],
        ),
        p("12. 발표용 데모 시나리오", styles["h1"]),
        table(
            [
                ["순서", "시연 내용", "강조 포인트"],
                ["1", "로그인", "JWT 기반 보호 API"],
                ["2", "출발지·도착지 검색", "Kakao 장소/역지오코딩"],
                ["3", "경로 확인 및 루틴 저장", "ODsay 경로와 alternatives 저장"],
                ["4", "루틴 카드의 실시간 상태 조회 클릭", "POST execute 진입"],
                ["5", "도착정보와 환승 상태 확인", "버스 타입 필터링, 실제 arrival_seconds 표시"],
                ["6", "재조회", "동일 날짜 RoutineExecution 갱신, 중복 생성 없음"],
            ],
            styles,
            [18 * mm, 78 * mm, 75 * mm],
        ),
        Spacer(1, 10),
        p(
            "<b>최종 요약:</b> 경로 검색과 루틴 저장은 계획 데이터로 분리하고, "
            "실시간 실행 시점에 외부 도착정보를 병렬 갱신한다. "
            "모든 후보 경로를 갱신한 뒤 오류·환승 가능성·시간을 기준으로 선택하며, "
            "프론트는 교통수단 타입을 확인해 실제 도착정보만 표시한다.",
            styles["callout"],
        ),
    ]
    return story


def main():
    font = register_korean_font()
    styles = build_styles(font)
    document = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="OnTime transport_app 기술 명세서",
        author="OnTime",
    )
    document.font_name = font
    document.build(
        make_story(styles),
        onFirstPage=footer,
        onLaterPages=footer,
    )
    print(OUTPUT)


if __name__ == "__main__":
    main()
