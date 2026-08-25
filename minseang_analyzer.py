"""
Minseang Analyzer (수원시 민생 영향 분석기)
Claude API로 수원시 민생 영향 분석 + 정책 제언 생성

입력: analyzed, domestic, paradigm, yt_summary JSON
출력: data/policy/minseang_YYYYMMDD.json
"""
import json, logging
from datetime import date, datetime, timedelta
from pathlib import Path
import anthropic
from config import (
    ANTHROPIC_API_KEY, CLAUDE_MODEL, POLICY_DIR,
    ANALYZED_DIR, DOMESTIC_DIR, PARADIGM_DIR, YT_DIR, SUWON_CONTEXT,
    FACT_CHECK_DIR, get_collection_days,
)
logger = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM = f"""당신은 수원시정연구원의 민생정책 전문 분석가입니다.
이란-미국 전쟁(2026)이 수원시 시민 생활에 미치는 영향을 분석하고
수원시가 취할 수 있는 민생안정 정책을 제언합니다.

{SUWON_CONTEXT}

★★ 우선_대응과제 작성 규칙 (절대 준수):
- 이 섹션은 "수원시에 제언하는 정책 방향"입니다.
- title과 description 모두에서 아래 항목을 절대 만들어 쓰지 마세요:
  × 수원시가 결정·발표·시행하지 않은 날짜 (예: "6/10 전", "6/15까지")
  × 수원시의 미발표 수치 (예: "500개소", "20만원→30만원", "3일→1일")
  × 실제 존재하지 않는 사업명 (예: "원자재비 긴급 융자", "긴급 점검반 구성")
- 허용: 수집된 기사에서 직접 인용한 수치·날짜 (반드시 출처 명시)
- description은 반드시 "~검토 필요", "~고려 가능", "~제언" 형식.
  "수원시가 X를 했다/할 것이다" 형식 금지.

★ 반드시 준수할 사실 기반 원칙:
1. 타지자체_현황·타지자체_벤치마킹·lga_responses는
   반드시 [국제 전황 요약] 또는 [국내 물가·에너지 지표] 데이터에서
   직접 확인된 내용만 작성하세요.
2. 수집된 기사에 없는 내용(날짜·금액·사업명·지자체 발표)은
   절대 만들어 쓰지 마세요.
3. 확인된 사례가 없으면 해당 필드 전체를 JSON에서 완전히 생략하세요.
   - 타지자체_현황: 없으면 필드 삭제
   - 타지자체_벤치마킹: 없으면 필드 삭제
   - lga_responses: 확인된 사례 없는 지자체는 배열에서 완전히 제외
4. 확인된 사례가 있을 때만 출처(언론사·날짜)를 반드시 명시하세요.
5. 전문가_의견은 수집된 기사 본문에서 직접 확인된 내용만 인용하세요.
   - 인용 가능 출처: ForeignAffairs, WarOnRocks, CFR, CSIS, AtlanticCouncil,
     ForeignPolicy, AlMonitor, Bloomberg, FT, NYT, Guardian 등
   - 형식: "[CFR 6/3] 이란 전쟁이 글로벌 경제 구조를 재편하고 있다"
   - 추측·요약 금지 — 수집 기사에서 확인된 분석만

반드시 JSON 형식만 반환하세요."""

PROMPT = """{period_start}~{period_end}(오늘)간 수집된 데이터를 종합해서 수원시 민생경제 분석과 우선 대응과제를 JSON으로 작성하세요.

★ 이번 기간 수집된 핵심 사실 (importance 상위 기사 자동 추출 — 이 사실들을 분석 근거로 활용할 것):
{key_facts}

위 핵심 사실을 분석 근거로 명시적으로 활용하고, 수원시 민생경제에 미치는 영향을 중점 분석할 것.
⚠️ 위 수집 기사에 없는 날짜·수치·사건은 절대 추가하지 말 것.

[국제 전황 요약 — {period_start}~{period_end} 수집 핵심 기사]
{war_summary}

[국내 물가·에너지 지표]
{domestic_summary}

[패러다임 변화 신호]
{paradigm_summary}

[유튜브·전문가 브리핑 요약]
{yt_summary}

[전문가·싱크탱크 분석 기사 — 우선과제 근거로 직접 인용할 것]
{expert_quotes}

[지난주 분석 결과 — 중복 지양, 변화·심화·신규 이슈 중심으로 작성]
{prev_summary}

⚠️ 작성 지침:
1. 지난주와 동일한 제목·내용 반복 금지 — 위 핵심 사실에 근거한 새로운 분석만 작성
2. 수치는 [국내 물가·에너지 지표]의 최신값 사용 (WTI·브렌트 유가, 환율 등)
3. 지난주 "다음주 주목이슈"로 예고된 사건들의 실제 결과 반영
4. ⚠️ 모든 텍스트 필드는 개조식(• 기호로 시작하는 짧고 명확한 문장)으로 작성. 서술형 긴 문장 금지. 한 항목에 여러 내용을 이어 쓰지 말 것.

반환 형식:
{{
  "핵심사실_요약": [
    "① [출처 날짜] 사실 제목 / • 핵심 내용(1줄) / • 수원시 영향(1줄)",
    "② [출처 날짜] 사실 제목 / • 핵심 내용 / • 수원시 영향",
    "③ [출처 날짜] 사실 제목 / • 핵심 내용 / • 수원시 영향"
  ],
  "민생경제_분석": {{
    "지역산업": {{
      "level": "높음|중간|낮음|모니터링",
      "summary": "개조식 3~4항목. 예: '• 삼성전자 협력업체 달러 결제 불확실성 / • 수출기업 2차 제재 리스크 / • 반도체 소재 공급망 점검 필요'",
      "key_indicator": "핵심 수치 1줄 (예: 브렌트유 $89.8 / 환율 ₩1,384)",
      "타지자체_현황": "(선택) 수집 기사에서 확인된 타 지자체 대응 사례+출처만 인용. 없으면 이 필드 생략"
    }},
    "소상공인_자영업": {{
      "level": "높음|중간|낮음|모니터링",
      "summary": "개조식 3~4항목. 예: '• 유류비 ₩1,864/L 운수업 원가 부담 / • 음식점 식재료 수입가 상승 / • 배달업 연료비 증가'",
      "key_indicator": "핵심 수치 1줄",
      "타지자체_현황": "(선택) 수집 기사에서 확인된 소상공인 지원 타 지자체 사례+출처만. 없으면 이 필드 생략"
    }},
    "시민생활": {{
      "level": "높음|중간|낮음|모니터링",
      "summary": "개조식 3~4항목. 예: '• 도시가스 요금 인상 압박 / • 취약계층 에너지 비용 부담 / • 물가 상승률 2.1% 유지'",
      "key_indicator": "핵심 수치 1줄",
      "타지자체_현황": "(선택) 수집 기사에서 확인된 에너지복지 타 지자체 사례+출처만. 없으면 이 필드 생략"
    }}
  }},
  "우선_대응과제": [
    {{
      "순위": 1,
      "title": "수원시가 검토해야 할 정책 과제 제목 (제언 형식. 확정·실행 중인 것처럼 쓰지 말 것)",
      "description": "개조식 2~3항목 (• 로 시작). 이 과제를 왜 검토해야 하는가 — 수집된 전황·지표 근거. 구체적 날짜·수치는 수집된 기사에서 확인된 것만. 없으면 방향만.",
      "priority": "즉시|단기|중기",
      "근거": {{
        "타지자체_벤치마킹": "(선택) 수집 기사에서 확인된 타지자체 실제 사례+출처+날짜. 없으면 이 필드 생략",
        "전문가_의견": "위 [전문가·싱크탱크 분석 기사] 목록에서 이 과제와 관련된 기사 1개를 선택해 핵심 내용 1~2문장을 [출처 날짜] 형식으로 그대로 인용",
        "보고서_근거": "위 [전문가·싱크탱크 분석 기사] 또는 [국제 전황 요약]에서 IEA·IMF·WorldBank·OECD 보고서 내용 1~2문장을 [출처 날짜] 형식으로 인용"
      }}
    }},
    {{
      "순위": 2,
      "title": "수원시 정책 과제 제목 (제언 형식)",
      "description": "개조식 2~3항목 (• 로 시작). 검토 근거. 수원시가 이미 실행 중인 것처럼 쓰지 말 것.",
      "priority": "즉시|단기|중기",
      "근거": {{
        "타지자체_벤치마킹": "(선택) 수집 기사 확인 사례+출처만. 없으면 이 필드 생략",
        "전문가_의견": "(선택) 수집 기사 확인 전문가 분석+출처만. 없으면 이 필드 생략",
        "보고서_근거": "(선택) 수집 기사 확인 보고서+출처만. 없으면 이 필드 생략"
      }}
    }},
    {{
      "순위": 3,
      "title": "수원시 정책 과제 제목 (제언 형식)",
      "description": "개조식 2~3항목 (• 로 시작). 검토 근거. 수원시가 이미 실행 중인 것처럼 쓰지 말 것.",
      "priority": "즉시|단기|중기",
      "근거": {{
        "타지자체_벤치마킹": "(선택) 수집 기사 확인 사례+출처만. 없으면 이 필드 생략",
        "전문가_의견": "(선택) 수집 기사 확인 전문가 분석+출처만. 없으면 이 필드 생략",
        "보고서_근거": "(선택) 수집 기사 확인 보고서+출처만. 없으면 이 필드 생략"
      }}
    }}
  ],
  "today_headline": "오늘 수원시가 가장 주목해야 할 민생 이슈 한 줄",
  "urgency": "긴급|주의|모니터링",
  "검증_포인트": [
    {{
      "title": "1. 검증 포인트 제목 (예: 예산 실현 가능성)",
      "body": "개조식 2~3항목 (• 로 시작). 실행 전 반드시 확인해야 할 리스크·한계·전제조건."
    }},
    {{
      "title": "2. 검증 포인트 제목",
      "body": "개조식 2~3항목 (• 로 시작). 리스크 내용."
    }},
    {{
      "title": "3. 검증 포인트 제목",
      "body": "개조식 2~3항목 (• 로 시작). 리스크 내용."
    }}
  ],
  "scout_points": [
    "• 전황 핵심 포인트 1 — 수원시 민생 연결 (1~2줄 개조식)",
    "• 전황 핵심 포인트 2 (1~2줄 개조식)",
    "• 전황 핵심 포인트 3 (1~2줄 개조식)"
  ],
  "next_week_issues": [
    {{
      "title": "다음주 주목할 이슈 제목 1",
      "detail": "개조식 2~3항목 (• 로 시작). 수원시 민생 영향 및 모니터링 포인트.",
      "tag": "고위험",
      "tag_cls": "ni-high"
    }},
    {{
      "title": "다음주 주목할 이슈 제목 2",
      "detail": "개조식 2~3항목 (• 로 시작). 수원시 민생 영향 및 모니터링 포인트.",
      "tag": "주목",
      "tag_cls": "ni-mid"
    }},
    {{
      "title": "다음주 주목할 이슈 제목 3",
      "detail": "개조식 2~3항목 (• 로 시작). 수원시 민생 영향 및 모니터링 포인트.",
      "tag": "확인 필요",
      "tag_cls": "ni-watch"
    }},
    {{
      "title": "다음주 주목할 이슈 제목 4",
      "detail": "개조식 2~3항목 (• 로 시작). 수원시 민생 영향 및 모니터링 포인트.",
      "tag": "모니터링",
      "tag_cls": "ni-watch"
    }}
  ],
  "lga_responses": [
    {{
      "name": "경기도",
      "type": "도",
      "confirmed_action": "수집된 기사에서 확인된 경기도 실제 대응 조치 (없으면 '수집된 사례 없음')",
      "suggested_action": "※제언※ 수원시가 경기도에 요청하거나 연계할 수 있는 구체적 정책 방향",
      "evidence": "근거 기사 출처 (없으면 '수집 기사 없음')"
    }},
    {{
      "name": "서울특별시",
      "type": "광역",
      "confirmed_action": "수집된 기사에서 확인된 서울시 실제 대응 조치 (없으면 '수집된 사례 없음')",
      "suggested_action": "※제언※ 수원시에 적용 가능한 서울시 모델 방향",
      "evidence": "근거 기사 출처 (없으면 '수집 기사 없음')"
    }},
    {{
      "name": "인천광역시",
      "type": "광역",
      "confirmed_action": "수집된 기사에서 확인된 인천시 실제 대응 조치 (없으면 '수집된 사례 없음')",
      "suggested_action": "※제언※ 항만·물류 기반 인천시 모델 수원 적용 방향",
      "evidence": "근거 기사 출처 (없으면 '수집 기사 없음')"
    }},
    {{
      "name": "전주시",
      "type": "기초",
      "confirmed_action": "수집된 기사에서 확인된 전주시 실제 대응 조치 (없으면 '수집된 사례 없음')",
      "suggested_action": "※제언※ 소상공인·에너지복지 분야 전주시 모델 수원 적용 방향",
      "evidence": "근거 기사 출처 (없으면 '수집 기사 없음')"
    }},
    {{
      "name": "화성시",
      "type": "기초",
      "confirmed_action": "수집된 기사에서 확인된 화성시 실제 대응 조치 (없으면 '수집된 사례 없음')",
      "suggested_action": "※제언※ 삼성전자 협력업체 공동 대응 수원·화성 연계 방향",
      "evidence": "근거 기사 출처 (없으면 '수집 기사 없음')"
    }}
  ]
}}"""


def load_summary(path: Path, max_items: int = 5) -> str:
    if not path or not path.exists():
        return "데이터 없음"
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            # 중요도 높은 기사 우선 정렬
            if data and "importance" in data[0]:
                data = sorted(data, key=lambda x: x.get("importance", 0), reverse=True)
            items = data[:max_items]
            return "\n".join(f"- [{a.get('source','')}] {a.get('title','')} | {a.get('summary_ko','')[:120]}" for a in items)
        elif isinstance(data, dict):
            return json.dumps(data, ensure_ascii=False)[:2000]
    except Exception:
        return "로드 실패"
    return ""


def load_analyzed_summary(path: Path, max_items: int = 15, fc_map: dict = None) -> str:
    """analyzed JSON 전용 로드:
    - "불일치" 팩트체크 기사 제외
    - "검증됨" 우선 정렬 후 importance 내림차순
    - 상위 max_items건 + 지자체 대응 기사 최대 3건 추가
    """
    if not path or not path.exists():
        return "데이터 없음"
    fc_map = fc_map or {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return json.dumps(data, ensure_ascii=False)[:2000]

        # 불일치 기사 제외 후 팩트체크 우선·importance 내림차순 정렬
        sorted_data = sorted(
            [a for a in data if fc_map.get(a.get("url", ""), {}).get("verdict") != "불일치"],
            key=lambda a: _fc_sort_key(a, fc_map),
        )

        # 상위 N건 (주로 전황·외교·군사 기사)
        top_items = [a for a in sorted_data if a.get("importance", 0) >= 1][:max_items]
        seen_urls = {a.get("url", "") for a in top_items}

        # ── 한국 지자체·국내 민생 정책 기사 별도 추가 (타지자체 벤치마킹 전용) ──
        # 슬롯 A: 국내 정책·지원 키워드가 제목에 있는 기사 (서울시 골목상권, 소상공인 지원 등)
        DOMESTIC_POLICY_KW = [
            "서울시", "경기도", "지자체", "소상공인", "골목상권", "골목형", "상점가",
            "자영업", "단체보험", "지원사업", "유류비 지원", "에너지 바우처",
            "에너지 지원", "긴급 지원", "수원시", "전주시", "화성시", "인천시",
        ]
        DOMESTIC_SOURCES = {"Seoul_Mediahub", "Newsis", "News1", "HeraldEco", "Hankyung"}

        domestic_policy_items = [
            a for a in sorted_data
            if a.get("url", "") not in seen_urls
            and a.get("importance", 0) >= 1
            and (
                a.get("source", "") in DOMESTIC_SOURCES
                or any(kw in a.get("title", "") for kw in DOMESTIC_POLICY_KW)
            )
        ][:3]  # 지자체 정책 기사 최대 3건

        seen_urls.update(a.get("url", "") for a in domestic_policy_items)

        # 슬롯 B: 한국 언론 일반 기사 (전황·외교·경제 보도)
        KO_SOURCES = {"Yonhap", "Yonhap_Economy", "Yonhap_Politics", "Chosun"}
        KO_CATS = {"country_response", "korea", "economy"}

        ko_general_items = [
            a for a in sorted_data
            if a.get("url", "") not in seen_urls
            and a.get("importance", 0) >= 1
            and a.get("category") in KO_CATS
            and a.get("source", "") in KO_SOURCES
        ][:3]  # 한국 언론 일반 기사 최대 3건

        items = top_items + domestic_policy_items + ko_general_items
        lines = [f"- [{a.get('source','')}] {a.get('title','')} | {a.get('summary_ko','')[:120]}"
                 for a in items]
        return "\n".join(lines)
    except Exception:
        return "로드 실패"


def load_prev_summary(policy_dir: Path, current_date_str: str) -> str:
    """지난주 minseang 데이터 로드 — 차별화용 컨텍스트 전달

    ※ 할루시네이션 전파 방지:
    - lga_responses(지자체 대응) 제외 — 이전 분석의 가상 사례가 이번주로 전파되는 것 차단
    - 벤치마킹 근거 제외 — 동일 이유
    - 과제 제목·지표·이슈만 포함
    """
    files = sorted(policy_dir.glob("minseang_*.json"), reverse=True)
    for f in files:
        if f.stem.replace("minseang_", "") < current_date_str:
            try:
                data = json.load(open(f, encoding="utf-8"))
                headline  = data.get("today_headline", "")
                urgency   = data.get("urgency", "")
                tasks     = data.get("우선_대응과제", [])
                ni_issues = data.get("next_week_issues", [])
                eco       = data.get("민생경제_분석", {})

                # 과제 제목만 전달 (description 제외 — 할루시네이션 방지)
                task_lines = [
                    f'  {t["순위"]}. [{t.get("priority","")}] {t["title"]}'
                    for t in tasks
                ]
                ni_lines = [f'  - {n["title"]}' for n in ni_issues]

                # 핵심 지표만 (수치 기반)
                eco_lines = []
                for k, v in eco.items():
                    if isinstance(v, dict) and v.get("key_indicator"):
                        eco_lines.append(f'  {k}: {v["key_indicator"]}')

                parts = [
                    f"[지난주 날짜] {data.get('date','')} | 긴급도: {urgency}",
                    f"[지난주 헤드라인] {headline}",
                    f"[지난주 우선과제 제목 — 이번주 반드시 다른 제목·내용으로 작성]",
                ] + task_lines + [
                    f"[지난주 다음주 주목이슈 — 이번주 이 이슈들의 후속·결과를 반영]",
                ] + ni_lines + [
                    f"[지난주 핵심 지표]",
                ] + eco_lines

                return "\n".join(parts)
            except Exception:
                continue
    return "이전 데이터 없음"


def load_expert_quotes(analyzed_path: Path, max_items: int = 8) -> str:
    """싱크탱크·전문매체 분석 기사에서 전문가 의견 인용용 콘텐츠 추출"""
    if not analyzed_path or not analyzed_path.exists():
        return "데이터 없음"
    try:
        with open(analyzed_path, encoding="utf-8") as f:
            data = json.load(f)
        EXPERT_SOURCES = {
            "ForeignAffairs", "WarOnRocks", "CFR_Iran", "CSIS_Iran",
            "AtlanticCouncil", "ForeignPolicy", "AlMonitor",
            "Guardian_Iran", "Guardian_World", "Bloomberg",
            "NYT_World", "FT_World", "IEA_News", "IMF_News",
            "WorldBank_News", "OECD_News",
        }
        experts = sorted(
            [a for a in data
             if a.get("source") in EXPERT_SOURCES
             and a.get("importance", 0) >= 4
             and a.get("summary_ko")],
            key=lambda x: x.get("importance", 0), reverse=True
        )[:max_items]
        lines = []
        for a in experts:
            src = a.get("source", "")
            pub = a.get("published", "")[:10]
            title = a.get("title", "")[:60]
            summ = a.get("summary_ko", "").split("\n")[0][:120]
            lines.append(f"[{src} {pub}] {title}\n  → {summ}")
        return "\n".join(lines) if lines else "데이터 없음"
    except Exception:
        return "로드 실패"


_CIRCLED = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩"]


def load_factcheck(fact_check_path: Path) -> dict:
    """팩트체크 결과 로드 — {url: {"verdict": ..., "confidence": ...}} 반환"""
    if not fact_check_path or not fact_check_path.exists():
        return {}
    try:
        with open(fact_check_path, encoding="utf-8") as f:
            data = json.load(f)
        return {
            r["url"]: {
                "verdict":    r.get("overall_verdict", "미확인"),
                "confidence": r.get("avg_confidence", 0.0),
            }
            for r in data.get("results", [])
            if r.get("url")
        }
    except Exception:
        return {}


def _fc_sort_key(article: dict, fc_map: dict) -> tuple:
    """팩트체크 결과를 반영한 정렬 키 — 검증됨>미체크>미확인, 같은 등급 내 importance 내림차순"""
    verdict = fc_map.get(article.get("url", ""), {}).get("verdict", "")
    rank = {"검증됨": 0}.get(verdict, 1) if verdict != "미확인" else 2
    return (rank, -article.get("importance", 0))


def compute_period(target_date_str: str) -> tuple:
    """발행 요일 기반 분석 기간 반환
    월요일: 금~월 (4일) | 목요일: 화~목 (3일)
    """
    end = datetime.strptime(target_date_str, "%Y-%m-%d")
    days = get_collection_days(target_date_str)
    start = end - timedelta(days=days - 1)
    return f"{start.month}월 {start.day}일", f"{end.month}월 {end.day}일"


def extract_key_facts(analyzed_path: Path, fc_map: dict = None, max_items: int = 8) -> str:
    """analyzed JSON + 팩트체크 결과를 결합해 핵심 사실 자동 추출.

    - "불일치" 판정 기사 제외
    - "검증됨" 우선 → 미체크 → "미확인" 순 정렬
    - 각 항목에 [✓검증됨] / [?미확인] 태그 표시
    """
    if not analyzed_path or not analyzed_path.exists():
        return "수집된 기사 없음"
    fc_map = fc_map or {}
    try:
        with open(analyzed_path, encoding="utf-8") as f:
            data = json.load(f)

        KEY_CATS = {"diplomacy", "military", "energy", "ceasefire", "nuclear", "economy"}

        # 불일치 제외
        filtered = [
            a for a in data
            if fc_map.get(a.get("url", ""), {}).get("verdict") != "불일치"
        ]

        priority = sorted(
            [a for a in filtered if a.get("category") in KEY_CATS and a.get("importance", 0) >= 4],
            key=lambda a: _fc_sort_key(a, fc_map),
        )[:max_items]

        if len(priority) < max_items:
            seen = {a.get("url", "") for a in priority}
            extra = sorted(
                [a for a in filtered if a.get("url", "") not in seen and a.get("importance", 0) >= 3],
                key=lambda a: _fc_sort_key(a, fc_map),
            )[:max_items - len(priority)]
            priority += extra

        lines = []
        for i, a in enumerate(priority[:max_items]):
            circle = _CIRCLED[i] if i < len(_CIRCLED) else f"({i+1})"
            src = a.get("source", "")
            pub = a.get("published", "")[:10]
            title = a.get("title", "")
            summ = a.get("summary_ko", "").split("\n")[0][:150] if a.get("summary_ko") else ""
            lines.append(f"{circle} [{src} {pub}] {title} — {summ}")

        return "\n".join(lines) if lines else "수집된 핵심 기사 없음"
    except Exception:
        return "로드 실패"


def run(target_date: str = None) -> Path:
    if target_date is None:
        target_date = date.today().strftime("%Y-%m-%d")
    date_str = target_date.replace("-", "")
    logger.info(f"=== MinseangAnalyzer 시작: {target_date} ===")

    analyzed_path = ANALYZED_DIR / f"analyzed_{date_str}.json"
    domestic_path = DOMESTIC_DIR / f"domestic_{date_str}.json"
    paradigm_path = PARADIGM_DIR / f"paradigm_{date_str}.json"
    yt_path       = YT_DIR / f"yt_summary_{date_str}.json"

    period_start, period_end = compute_period(target_date)

    fact_check_path = FACT_CHECK_DIR / f"fact_check_{date_str}.json"
    fc_map = load_factcheck(fact_check_path)
    if fc_map:
        fc_stats = {v: sum(1 for x in fc_map.values() if x["verdict"] == v)
                    for v in ["검증됨", "불일치", "미확인"]}
        logger.info(f"팩트체크 로드: 검증됨 {fc_stats['검증됨']} · 불일치 {fc_stats['불일치']} · 미확인 {fc_stats['미확인']}")
    else:
        logger.info("팩트체크 결과 없음 — 전체 기사 사용")

    key_facts = extract_key_facts(analyzed_path, fc_map=fc_map)

    prompt = PROMPT.format(
        period_start     = period_start,
        period_end       = period_end,
        key_facts        = key_facts,
        war_summary      = load_analyzed_summary(analyzed_path, max_items=15, fc_map=fc_map),
        domestic_summary = load_summary(domestic_path),
        paradigm_summary = load_summary(paradigm_path),
        yt_summary       = load_summary(yt_path),
        prev_summary     = load_prev_summary(POLICY_DIR, date_str),
        expert_quotes    = load_expert_quotes(analyzed_path),
    )

    def _call_claude(prompt_text):
        resp = client.messages.create(
            model=CLAUDE_MODEL, max_tokens=16384,
            system=SYSTEM,
            messages=[{"role": "user", "content": prompt_text}],
        )
        raw = resp.content[0].text.strip().replace("```json","").replace("```","").strip()
        # JSON 블록 추출: 첫 { 부터 마지막 } 까지
        start = raw.find("{")
        end   = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            raw = raw[start:end+1]
        return json.loads(raw)

    result = None
    for attempt in range(3):
        try:
            result = _call_claude(prompt)
            break
        except Exception as e:
            logger.warning(f"Claude 실패 (시도 {attempt+1}/3): {e}")
            if attempt == 2:
                result = {"error": str(e), "today_headline": "분석 실패", "urgency": "모니터링"}

    result["date"] = target_date
    result["generated_at"] = datetime.utcnow().isoformat()

    # ── 후처리 ①: 전문가 의견·보고서 근거 자동 채움 ────────────────────
    # Claude가 근거 필드를 비울 경우 Python에서 직접 삽입
    if analyzed_path.exists():
        try:
            with open(analyzed_path, encoding="utf-8") as _f:
                _analyzed = json.load(_f)

            _EXPERT_SRCS = {"ForeignAffairs","WarOnRocks","CFR_Iran","CSIS_Iran",
                           "AtlanticCouncil","ForeignPolicy","AlMonitor",
                           "Guardian_Iran","Guardian_World","Bloomberg","NYT_World","FT_World"}
            _REPORT_SRCS = {"IEA_News","IMF_News","WorldBank_News","OECD_News","UNCTAD_News"}

            _experts = sorted(
                [a for a in _analyzed if a.get("source") in _EXPERT_SRCS
                 and a.get("importance",0) >= 4 and a.get("summary_ko")],
                key=lambda x: x.get("importance",0), reverse=True
            )
            _reports = sorted(
                [a for a in _analyzed if a.get("source") in _REPORT_SRCS
                 and a.get("importance",0) >= 4 and a.get("summary_ko")],
                key=lambda x: x.get("importance",0), reverse=True
            )

            def _make_quote(article: dict) -> str:
                src = article.get("source","")
                pub = article.get("published","")[:10]
                summ = article.get("summary_ko","").split("\n")[0][:120]
                return f"[{src} {pub}] {summ}"

            for i, task in enumerate(result.get("우선_대응과제", [])):
                근거 = task.setdefault("근거", {})
                if not 근거.get("전문가_의견") and i < len(_experts):
                    근거["전문가_의견"] = _make_quote(_experts[i])
                if not 근거.get("보고서_근거") and i < len(_reports):
                    근거["보고서_근거"] = _make_quote(_reports[i])
        except Exception as _e:
            logger.warning(f"전문가 의견 자동 삽입 실패: {_e}")

    # ── 후처리 ②: 빈·무관 타지자체 필드 자동 제거 ─────────────────────────
    # 빈 값 또는 "없음" 패턴을 나타내는 마커
    # ※ ""는 제외: Python에서 any_str.startswith("") == True이므로
    #   모든 값을 빈 값으로 오인하는 버그 방지
    EMPTY_MARKERS = [
        "수집된 사례 없음", "수집 기사 없음", "확인되지 않음",
        "확인 안 됨", "없음", "해당 없음",
    ]

    def _is_empty_val(val: str) -> bool:
        if not val or not val.strip():
            return True
        v = val.strip()
        for m in EMPTY_MARKERS:
            if m and (v.startswith(m) or v == m):
                return True
        return False

    # lga_responses: confirmed_action 없는 지자체 제거
    if "lga_responses" in result:
        result["lga_responses"] = [
            lga for lga in result["lga_responses"]
            if not _is_empty_val(lga.get("confirmed_action", ""))
        ]

    # 민생경제_분석 타지자체_현황: 빈 값 or 관련없음 언급 시 제거
    for section in result.get("민생경제_분석", {}).values():
        if isinstance(section, dict):
            val = section.get("타지자체_현황", "")
            if _is_empty_val(val):
                section.pop("타지자체_현황", None)

    # 우선_대응과제 근거: 빈 필드 제거
    for task in result.get("우선_대응과제", []):
        근거 = task.get("근거", {})
        for key in ["타지자체_벤치마킹", "전문가_의견", "보고서_근거"]:
            if _is_empty_val(근거.get(key, "")):
                근거.pop(key, None)

    out_path = POLICY_DIR / f"minseang_{date_str}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info(f"긴급도: {result.get('urgency')} | 헤드라인: {result.get('today_headline','')}")
    logger.info(f"=== MinseangAnalyzer 완료 → {out_path} ===")
    return out_path


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    run(sys.argv[1] if len(sys.argv) > 1 else None)
