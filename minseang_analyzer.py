"""
Minseang Analyzer (수원시 민생 영향 분석기)
Claude API로 수원시 민생 영향 분석 + 정책 제언 생성

입력: analyzed, domestic, paradigm, yt_summary JSON
출력: data/policy/minseang_YYYYMMDD.json
"""
import json, logging
from datetime import date, datetime
from pathlib import Path
import anthropic
from config import (
    ANTHROPIC_API_KEY, CLAUDE_MODEL, POLICY_DIR,
    ANALYZED_DIR, DOMESTIC_DIR, PARADIGM_DIR, YT_DIR, SUWON_CONTEXT
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

PROMPT = """6월 9일(월)~6월 11일(수·오늘)간 수집된 데이터를 종합해서 수원시 민생경제 분석과 우선 대응과제를 JSON으로 작성하세요.

★ 이번 주(6/11) 반드시 반영해야 할 핵심 사실 (6/9~6/11 확인된 사실):
① 미국, 6/11 이란에 2차 대규모 공습 단행 — 트럼프 "이란을 오늘 다시 강하게 타격할 것" 예고 후 실행 (FT·BBC)
② 이란, 미군 걸프 기지 재공격 — 미국의 2차 공습에 대한 보복으로 쿠웨이트·바레인 미군기지 재타격 (BBC·CNN)
③ 미군 헬기 격추 사건 → 미국 이란 추가 보복 공격 — 이란이 미군 군사 헬기 격추, 미국 즉각 공습으로 응수 (BBC)
④ 이란·이스라엘, 6/11 일시 공격 중단 발표 — 단, 양측 모두 보복 경고 지속 (BBC)
⑤ 유가 급등 — 미국 2차 이란 공습으로 '취약한 휴전' 위협, 브렌트 급등 (Bloomberg 6/11)
⑥ 트럼프 이란 전쟁 통제력 상실 우려 — BBC "Has Trump lost control of the Iran war?" 분석 보도 (BBC)
⑦ 유가: WTI $91.50, 브렌트 $94.35 (6/11 기준) / USD/KRW 1524.5
⑧ 지난주(6/8) 예고: 트럼프 6/10 합의 → 실제 결렬, 2차 공습으로 전환. 6/10 합의 무산 확인

위 ①~⑧를 분석 근거로 명시적으로 활용할 것. 지난주(6/8) 분석과 중복되는 내용은 작성 금지.

[국제 전황 요약 — 6/5~6/8 수집 핵심 기사]
{war_summary}

[국내 물가·에너지 지표]
{domestic_summary}

[패러다임 변화 신호]
{paradigm_summary}

[유튜브·전문가 브리핑 요약]
{yt_summary}

[전문가·싱크탱크 분석 기사 — 우선과제 근거로 직접 인용할 것]
{expert_quotes}

[지난주(6/4) 분석 결과 — 중복 지양, 변화·심화·신규 이슈 중심으로 작성]
{prev_summary}

⚠️ 작성 지침:
1. 지난주(6/4)와 동일한 제목·내용 반복 금지 — 위 ①~⑨ 사실에 근거한 새로운 분석만 작성
2. "이란 이스라엘 미사일 발사(①②)" — 4월 휴전 이후 전선 재확대가 수원시 에너지·물류에 미치는 영향
3. "미-이란 걸프 직접 교전(③)" + "트럼프 6/10 합의 가능(④)" — 외교·군사 양면 시나리오별 수원시 대응
4. "호르무즈 통행료 150~200만 달러(⑤)" + "IATA 순익 50% 하향(⑦)" — 항공화물·해운 비용 직접 영향
5. 수치는 위 ①~⑨에 명시된 최신값 사용 (6/8 기준 WTI $92.74, 브렌트 $95.44, 환율 1540.93원)
6. 지난주(6/4) 우선과제와 완전히 다른 제목·내용 사용
7. 지난주 "다음주 주목이슈"로 예고된 사건들의 실제 결과 반영 (트럼프-하메네이 접촉·이란 미사일 발사 등)

반환 형식:
{{
  "민생경제_분석": {{
    "지역산업": {{
      "level": "높음|중간|낮음|모니터링",
      "summary": "수원시 지역산업(삼성전자·제조업·수출기업) 영향 분석 2~3줄",
      "key_indicator": "핵심 지표 또는 수치 1줄",
      "타지자체_현황": "(선택) 수집 기사에서 확인된 타 지자체 대응 사례+출처만 인용. 없으면 이 필드 생략"
    }},
    "소상공인_자영업": {{
      "level": "높음|중간|낮음|모니터링",
      "summary": "수원시 소상공인·자영업(음식점·배달·운수·유류비) 영향 분석 2~3줄",
      "key_indicator": "핵심 지표 또는 수치 1줄",
      "타지자체_현황": "(선택) 수집 기사에서 확인된 소상공인 지원 타 지자체 사례+출처만. 없으면 이 필드 생략"
    }},
    "시민생활": {{
      "level": "높음|중간|낮음|모니터링",
      "summary": "수원시 시민생활(도시가스·전기료·물가·취약계층) 영향 분석 2~3줄",
      "key_indicator": "핵심 지표 또는 수치 1줄",
      "타지자체_현황": "(선택) 수집 기사에서 확인된 에너지복지 타 지자체 사례+출처만. 없으면 이 필드 생략"
    }}
  }},
  "우선_대응과제": [
    {{
      "순위": 1,
      "title": "수원시가 검토해야 할 정책 과제 제목 (제언 형식. 확정·실행 중인 것처럼 쓰지 말 것)",
      "description": "이 과제를 왜 검토해야 하는가 — 수집된 전황·지표 근거 2~3줄. 구체적 날짜·사업명·수치는 수집된 기사에서 확인된 것만 사용. 없으면 방향만 제시.",
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
      "description": "검토 근거 2~3줄. 수원시가 이미 실행 중인 것처럼 쓰지 말 것.",
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
      "description": "검토 근거 2~3줄. 수원시가 이미 실행 중인 것처럼 쓰지 말 것.",
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
      "body": "해당 날짜 우선과제·전황 데이터를 근거로 실행 전 반드시 확인해야 할 리스크·한계·전제조건 2~3줄"
    }},
    {{
      "title": "2. 검증 포인트 제목",
      "body": "리스크 내용 2~3줄"
    }},
    {{
      "title": "3. 검증 포인트 제목",
      "body": "리스크 내용 2~3줄"
    }}
  ],
  "scout_points": [
    "전황 요약 포인트 1 (수원시 민생 연결 중심)",
    "전황 요약 포인트 2",
    "전황 요약 포인트 3"
  ],
  "next_week_issues": [
    {{
      "title": "다음주 주목할 이슈 제목 1",
      "detail": "수원시 민생에 미치는 영향 및 모니터링 포인트 2~3줄",
      "tag": "고위험",
      "tag_cls": "ni-high"
    }},
    {{
      "title": "다음주 주목할 이슈 제목 2",
      "detail": "수원시 민생에 미치는 영향 및 모니터링 포인트 2~3줄",
      "tag": "주목",
      "tag_cls": "ni-mid"
    }},
    {{
      "title": "다음주 주목할 이슈 제목 3",
      "detail": "수원시 민생에 미치는 영향 및 모니터링 포인트 2~3줄",
      "tag": "확인 필요",
      "tag_cls": "ni-watch"
    }},
    {{
      "title": "다음주 주목할 이슈 제목 4",
      "detail": "수원시 민생에 미치는 영향 및 모니터링 포인트 2~3줄",
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


def load_analyzed_summary(path: Path, max_items: int = 15) -> str:
    """analyzed JSON 전용 로드:
    - 상위 max_items건 (importance 내림차순, 전황·외교·군사 중심) +
    - 한국어 지자체 대응 기사 최대 5건 별도 추가
      (importance 낮아도 타지자체 벤치마킹에 필수: 서울시·경기도·전주·화성 등)
    """
    if not path or not path.exists():
        return "데이터 없음"
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return json.dumps(data, ensure_ascii=False)[:2000]

        # 중요도 내림차순 정렬
        sorted_data = sorted(data, key=lambda x: x.get("importance", 0), reverse=True)

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


def run(target_date: str = None) -> Path:
    if target_date is None:
        target_date = date.today().strftime("%Y-%m-%d")
    date_str = target_date.replace("-", "")
    logger.info(f"=== MinseangAnalyzer 시작: {target_date} ===")

    analyzed_path = ANALYZED_DIR / f"analyzed_{date_str}.json"
    domestic_path = DOMESTIC_DIR / f"domestic_{date_str}.json"
    paradigm_path = PARADIGM_DIR / f"paradigm_{date_str}.json"
    yt_path       = YT_DIR / f"yt_summary_{date_str}.json"

    prompt = PROMPT.format(
        war_summary     = load_analyzed_summary(analyzed_path, max_items=15),
        domestic_summary= load_summary(domestic_path),
        paradigm_summary= load_summary(paradigm_path),
        yt_summary      = load_summary(yt_path),
        prev_summary    = load_prev_summary(POLICY_DIR, date_str),
        expert_quotes   = load_expert_quotes(analyzed_path),
    )

    try:
        resp = client.messages.create(
            model=CLAUDE_MODEL, max_tokens=16384,
            system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip().replace("```json","").replace("```","").strip()
        result = json.loads(raw)
    except Exception as e:
        logger.warning(f"Claude 실패: {e}")
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
