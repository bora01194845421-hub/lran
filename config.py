"""
config.py — 전체 설정
이란-미국 전쟁 민생 이슈 발굴 에이전트 v2 (28개 소스)
수원시정연구원
"""
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR     = Path(__file__).parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)
# IRAN_DATA_DIR 환경변수로 데이터 루트 전환 가능 (V2=data_v2)
DATA_DIR     = BASE_DIR / os.getenv("IRAN_DATA_DIR", "data")
RAW_DIR      = DATA_DIR / "raw"
CLEAN_DIR    = DATA_DIR / "clean"
ANALYZED_DIR = DATA_DIR / "analyzed"
REPORTS_DIR  = DATA_DIR / "reports"
INTL_DIR     = DATA_DIR / "intl"
RESEARCH_DIR = DATA_DIR / "research"
DOMESTIC_DIR = DATA_DIR / "domestic"
PARADIGM_DIR          = DATA_DIR / "paradigm"
POLICY_DIR            = DATA_DIR / "policy"
YT_DIR                = DATA_DIR / "youtube"
COUNTRY_RESPONSE_DIR  = DATA_DIR / "country_response"
DB_PATH      = BASE_DIR / "iran_news.db"
LOG_PATH     = BASE_DIR / "iran_agent.log"


def get_collection_days(target_date_str: str) -> int:
    """발행 요일에 따른 수집 기간 반환
    월요일 발행: 금·토·일·월 = 4일
    목요일 발행: 화·수·목 = 3일
    기타: 5일 (fallback)
    """
    weekday = datetime.strptime(target_date_str, "%Y-%m-%d").weekday()
    if weekday == 0:    # 월요일
        return 4
    elif weekday == 3:  # 목요일
        return 3
    return 5

FACT_CHECK_DIR = DATA_DIR / "fact_check"

for d in [RAW_DIR, CLEAN_DIR, ANALYZED_DIR, REPORTS_DIR,
          INTL_DIR, RESEARCH_DIR, DOMESTIC_DIR,
          PARADIGM_DIR, POLICY_DIR, YT_DIR, COUNTRY_RESPONSE_DIR,
          FACT_CHECK_DIR]:
    d.mkdir(parents=True, exist_ok=True)

ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY", "")
NEWSAPI_KEY        = os.getenv("NEWSAPI_KEY", "")
GUARDIAN_API_KEY   = os.getenv("GUARDIAN_API_KEY", "")
NYT_API_KEY        = os.getenv("NYT_API_KEY", "")
BRAVE_API_KEY      = os.getenv("BRAVE_API_KEY", "")
OPINET_API_KEY     = os.getenv("OPINET_API_KEY", "")
KOSIS_API_KEY      = os.getenv("KOSIS_API_KEY", "")   # kosis.kr/openapi 무료 발급
YT_API_KEY         = os.getenv("YOUTUBE_API_KEY", "")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")  # 사실검증 모듈용 (선택)

KEYWORDS_EN = [
    # ── 이란 직접 (단독 포함)
    "iran",
    "iran war", "iran us war", "hormuz", "hormuz blockade",
    "tehran", "irgc", "iranian", "iran ceasefire",
    "iran nuclear", "iran missile", "hezbollah iran",
    "strait of hormuz", "iran oil", "iran blockade",
    "iran sanction", "iran attack", "iran deal",
    # ── 중동 지역 정세
    "middle east war", "middle east conflict", "persian gulf",
    "gulf crisis", "red sea", "houthi", "hezbollah",
    "israel iran", "israel strike", "israel war",
    "gaza war", "west bank", "hamas",
    # ── 에너지·유가 (간접 영향)
    "oil price", "crude oil", "oil market", "opec cut",
    "energy crisis", "energy security", "oil supply",
    "lng price", "gas price spike", "fuel price",
    "oil sanction", "energy sanction",
    # ── 경제·공급망 (간접 영향)
    "shipping disruption", "suez canal", "supply chain",
    "tanker attack", "naval blockade", "oil tanker",
    "global inflation", "war economy",

    # ══ 신규 추가 키워드 ══

    # ── 한국 지자체 실제 대응 (벤치마킹 사실 기반 수집용)
    "Suwon city energy policy", "Gyeonggi energy support",
    "Korea local government oil price support",
    "Seoul small business energy subsidy",
    "Korea municipality Iran war response",

    # ── 교통·물류·해운
    "cape of good hope rerouting", "war risk insurance marine",
    "container freight surge", "freight rate Iran",
    "shipping surcharge gulf", "hormuz shipping lane",
    "port congestion diversion", "SCFI freight index",
    "multimodal transport Iran", "air cargo disruption",

    # ── 금융·통화·외환
    "war risk premium", "capital outflow Iran war",
    "CDS spread emerging market", "oil shock currency",
    "Iran sanctions cryptocurrency", "petrodollar",
    "sovereign wealth fund Gulf", "war bond",

    # ── 식량·농업
    "urea fertilizer Iran war", "ammonia shortage",
    "food security hormuz", "fertilizer price spike",
    "nitrogen fertilizer shortage", "food inflation Iran",
    "wheat corn supply disruption", "Ras Laffan fertilizer",

    # ── 반도체·첨단산업
    "helium shortage semiconductor", "ras laffan helium",
    "bromine photoresist supply", "specialty gas chip",
    "neon krypton xenon chip", "semiconductor supply Iran",
    "Korea fab helium procurement",

    # ── 사이버·안보
    "Iran cyber attack", "IRGC cyber", "CyberAv3ngers",
    "critical infrastructure attack Iran",
    "ICS SCADA Iran", "Iran drone technology",
    "Iran Russia drone transfer",

    # ── 의료·보건
    "pharmaceutical supply chain Iran",
    "API active pharmaceutical Iran",
    "medicine price inflation Iran war",
    "medical device shortage Iran",

    # ── 환경·기후
    "Persian Gulf oil spill", "iran war oil spill satellite",
    "renewable energy acceleration Iran",
    "Bushehr nuclear radiation risk",
    "energy transition Iran war",

    # ── 관광·항공
    "Korean Air emergency jet fuel", "jet fuel shortage Iran",
    "Middle East airspace closure",
    "war risk insurance aviation",
    "Dubai Doha hub disruption",

    # ── 외교·다자관계
    "China Iran support proxy", "Russia Iran drone 2026",
    "India oil waiver Iran war", "Turkey Iran refugee NATO",
    "THAAD redeployment Korea",
    "India Russia oil Iran war",
    "Qatar mediation Iran deal",

    # ── 노동·산업·원자재
    "aluminum shortage Iran war", "tungsten price Iran",
    "manufacturing cost Iran war Korea",
    "Iran humanitarian crisis IDP",
    "global recession Iran war OECD",
]

KEYWORDS_KO = [
    # ── 이란 직접 (단독 포함 — 제목에 "이란"만 있어도 수집)
    "이란",
    "이란 전쟁", "이란 미국", "호르무즈", "이란 핵",
    "이란 봉쇄", "테헤란", "이란 휴전", "이란전", "이란 공격",
    # ── 중동 지역 (단독 포함)
    "중동", "걸프",
    "중동전쟁", "중동 분쟁", "페르시아만", "홍해", "후티",
    "헤즈볼라", "이스라엘 이란", "가자", "하마스",
    # ── 원전·에너지 시설
    "원전 폭격", "원전 공격", "부셰르", "바라카",
    # ── 에너지·유가
    "유가", "원유", "에너지 위기", "에너지 안보",
    "유류비", "난방비", "도시가스", "LNG 가격",
    # ── 경제·물가
    "물가", "인플레", "공급망", "해운 운임",
    # ── 한국 부처 대응 (이란·중동 사태 관련 정부 발표 수집용)
    "외교부 이란", "외교부 중동", "산업부 에너지", "산업부 LNG",
    "기재부 유가", "기재부 물가", "기재부 비상", "유류세 인하",
    "식약처 원료", "식약처 수급", "농림부 곡물", "농림부 식량",
    "에너지 비상대책", "에너지 수급 비상", "LNG 수입 다변화",
    "에너지 긴급", "원유 비축", "전략비축유", "수입 다변화",
    "중동 사태 대응", "에너지 대응", "정부 긴급 대책",

    # ══ 신규 추가 키워드 ══

    # ── 한국 지자체·정부 실제 대응 (벤치마킹 사실 기반 수집용)
    "수원시 에너지", "수원시 소상공인", "수원시 지원",
    "경기도 에너지 지원", "경기도 소상공인",
    "서울시 에너지 바우처", "서울시 유류비",
    "지자체 유가 대응", "지자체 에너지 긴급",
    "소상공인 유류비 지원 지자체",
    "에너지 바우처 지자체", "난방비 지원 지자체",
    "도시가스 요금 지원", "도시가스 요금경감",
    "에너지 취약계층 지원", "전기요금 지원",
    "소상공인 긴급지원", "소상공인 경영 안정",
    "유류세 인하 지자체", "착한가격업소",
    "중기부 소상공인", "중소벤처기업부 지원",
    "에너지 복지 사업", "난방비 긴급복지",

    # ── 교통·물류·해운
    "희망봉 우회", "컨테이너 운임 급등", "해운 전쟁할증료",
    "부산항 중동 물동량", "해상 전쟁보험", "항공화물 운임",
    "이란 전쟁 해운지수", "복합운송 우회항로",

    # ── 금융·통화·외환
    "원달러 자본유출", "이란 전쟁 환율", "전쟁 리스크 프리미엄",
    "이란 암호화폐 제재", "코스피 이란 전쟁",
    "걸프 국부펀드 한국", "전쟁채권 신흥국",

    # ── 식량·농업
    "요소 비료 이란 전쟁", "암모니아 가격 이란",
    "식량안보 호르무즈", "비료 가격 급등 중동",
    "라스라판 비료 생산", "이란 전쟁 식량 위기",
    "밀 옥수수 공급 이란", "식용유 이란 전쟁",

    # ── 반도체·첨단산업
    "헬륨 반도체 이란 전쟁", "라스라판 헬륨 공급",
    "브롬 포토레지스트 한국", "반도체 특수가스 이란",
    "삼성전자 헬륨 공급망", "SK하이닉스 특수가스",
    "데이터센터 에너지 이란",

    # ── 사이버·안보
    "이란 사이버 공격", "IRGC 해킹 인프라",
    "이란 드론 러시아 기술", "이란 사이버 한국 금융",
    "산업제어시스템 이란 공격",

    # ── 의료·보건
    "원료의약품 이란 전쟁", "제약 공급망 중동",
    "이란 전쟁 의약품 가격", "API 수입 차질",

    # ── 환경·기후
    "페르시아만 원유 유출", "이란 전쟁 환경오염",
    "재생에너지 이란 전쟁 가속", "에너지 전환 중동 전쟁",
    "부세르 핵발전소 방사능",

    # ── 관광·항공
    "대한항공 이란 전쟁 비상", "항공유 이란 전쟁",
    "중동 항공노선 운휴", "두바이 도하 환승 중단",
    "항공 전쟁보험료",

    # ── 외교·다자관계
    "중국 이란 군사지원", "러시아 드론 이란 공급",
    "인도 러시아 석유 이란", "터키 이란 난민",
    "주한미군 THAAD 중동 재배치", "카타르 이란 중재",

    # ── 노동·산업·원자재
    "알루미늄 이란 전쟁 한국", "텅스텐 가격 이란",
    "이란 인도주의 이재민", "중소기업 원자재 이란",
    "이란 전쟁 글로벌 경기침체",
]
KEYWORDS_MINSEANG_KO = [
    "유가", "물가", "에너지", "난방비", "전기료", "도시가스",
    "소상공인", "민생", "장바구니", "생활비", "인플레",
    "수원시", "경기도", "취약계층",
]
PARADIGM_KEYWORDS = [
    "energy security", "energy transition", "supply diversification",
    "strategic reserve", "energy partnership", "reliability",
    "recession", "growth forecast", "inflation outlook",
    "trade disruption", "supply chain", "shipping route",
    "price cap", "export controls", "hoarding", "emergency",
    "paradigm", "fragmentation", "geopolitical", "decoupling",
    "에너지안보", "패러다임", "공급망재편", "무역질서",
]

ISSUE_CATEGORIES = [
    "military",          # 군사·전황
    "diplomacy",         # 외교·협상
    "energy",            # 에너지·유가
    "economy",           # 경제·금융·무역
    "humanitarian",      # 인도주의·난민
    "nuclear",           # 핵·원전
    "korea",             # 한국 국내 정책·대응
    "paradigm",          # 패러다임 변화·구조 전환
    "country_response",  # 각국 대응 방안
    "transport",         # 교통·물류·해운·항공
    "food_security",     # 식량·농업·비료
    "semiconductor",     # 반도체·첨단산업·특수가스
    "cyber",             # 사이버·안보
    "environment",       # 환경·기후·원유유출
]

# ── 각국 대응 추적 대상 국가·세력
TREND_COUNTRIES = [
    "미국", "이스라엘", "사우디아라비아", "UAE", "카타르",
    "중국", "러시아", "EU", "영국", "한국", "일본", "인도",
    "튀르키예", "파키스탄", "이라크", "시리아",
]

# ── 한국 중앙정부 부처별 대응 추적 대상
KR_MINISTRIES = [
    "외교부", "산업부", "기재부", "국토부", "기후에너지부",
    "식약처", "농림부",
]

SUWON_CONTEXT = """
수원시 기본 정보:
- 인구: 약 119만 명 (경기도 최대 도시)
- 주요 산업: 삼성전자 본사 소재, IT·제조업 중심
- 에너지: 도시가스·전기 의존, 중동산 LNG 간접 영향
- 취약계층: 기초생활수급자·차상위·노인1인가구·외국인근로자
- 소상공인: 음식점·배달·운수업 에너지비 민감
- 재정자립도: 약 40% (경기도 지원사업 연계 중요)
- 반도체 공급망: 삼성전자 반도체 라인 카타르 라스라판산 헬륨·브롬 의존
  → 호르무즈 봉쇄 시 특수가스 수급 위기 직접 영향
- 물류·수출: 삼성전자 수출 기업 운임 상승 + 전쟁보험료 급등 이중 부담
- 항공: 대한항공·아시아나 중동 노선 운휴 → 수원 기업 해외출장·물류 차질
- 식량: 요소·암모니아 비료 가격 급등 → 지역 농업 생산비 상승
- 의료: API(원료의약품) 인도→한국 공급망 운임 상승 → 지역 약가 압박
"""

YOUTUBE_CHANNELS = {
    "AlJazeera_EN": {
        "channel_id": "UCNye-wNBqNL5ZzHSJj3l8Bg",
        "name": "Al Jazeera English",
        "lang": "en", "credibility": 8.0,
    },
    "DW_News": {
        "channel_id": "UCknLrEdhRCp1aegoMqRaCZg",
        "name": "DW News",
        "lang": "en", "credibility": 8.5,
    },
    "Yonhap_TV": {
        "channel_id": "UCTHCOPwqNfZ0uiKOvFyhGwg",
        "name": "연합뉴스TV",
        "lang": "ko", "credibility": 8.0,
    },
}
YOUTUBE_SCHEDULE_DAYS = [0, 1, 2, 3, 4]   # 월~금 매일 수집 (주말 이슈 포함)

CLAUDE_MODEL        = "claude-sonnet-4-5-20250929"
ANALYZER_MODEL      = "claude-haiku-4-5"          # Analyzer 전용 (비용 절감)
ANALYZER_BATCH_SIZE = 20                            # 배치 크기 10→20 (API 호출 횟수 절반)
REQUEST_DELAY       = 2.0
SCHEDULE_TIMES      = ["07:00", "19:00"]
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
