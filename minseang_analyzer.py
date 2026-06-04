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

반드시 JSON 형식만 반환하세요."""

PROMPT = """6월 1일(월)~6월 4일(수·오늘)간 수집된 데이터를 종합해서 수원시 민생경제 분석과 우선 대응과제를 JSON으로 작성하세요.

★ 이번 주(6/4) 반드시 반영해야 할 핵심 사실 (6/1~6/4 확인된 사실):
① 미 하원, 6/3 215-208로 이란전쟁 중단 결의안 통과 — 공화당 4명 이탈, 트럼프 견제 (BBC·FT·Al Jazeera)
② FT 6/3: 미국 석유재고 2004년 이후 최저(22년 만에) — 호르무즈 봉쇄 장기화 직격탄
③ FT 6/3: 걸프 국가들 호르무즈 우회 석유 파이프라인 협상 착수 — 봉쇄 장기화 전제 인프라 전환
④ 이란, 6/3~4 쿠웨이트 국제공항 드론 공격(터미널1 심각 파괴) + 바레인 미사일 — 협상 중에도 군사행동 지속
⑤ 트럼프 6/4: "이번 주말에라도 합의 가능" + "모즈타바 하메네이 만나고 싶다" 표명 (연합뉴스)
⑥ 이스라엘·레바논 휴전 재개 합의 — 헤즈볼라 요원 철수 요청 포함 (NYT 6/4)
⑦ OECD 6/3: "이란 분쟁 2027년까지 지속 시 전 세계 동시 경기침체" 경고 (Guardian)
⑧ 유가: WTI $95.14 (6/1 $89.61 대비 +$5.5↑), 브렌트 $96.85 (+$3.8↑)
⑨ USD/KRW 1530.99 (6/1 1506.27 대비 +24원 급등) — 자본유출·에너지 수입비용 이중 압박

위 ①~⑨를 분석 근거로 명시적으로 활용할 것. 지난주(6/1) 분석과 중복되는 내용은 작성 금지.

[국제 전황 요약 — 6/1~6/4 수집 핵심 기사]
{war_summary}

[국내 물가·에너지 지표]
{domestic_summary}

[패러다임 변화 신호]
{paradigm_summary}

[유튜브·전문가 브리핑 요약]
{yt_summary}

[지난주(5/26) 분석 결과 — 중복 지양, 변화·심화·신규 이슈 중심으로 작성]
{prev_summary}

⚠️ 작성 지침:
1. 지난주(6/1)와 동일한 제목·내용 반복 금지 — 위 ①~⑨ 사실에 근거한 새로운 분석만 작성
2. "미 하원 이란전쟁 중단 결의안 통과(①)"가 수원시 에너지·산업·수출에 미치는 영향 분석 — 외교 변수 변화
3. "미국 석유재고 22년 만에 최저(②)"와 "걸프 파이프라인 협상 착수(③)"이 국내 에너지 비용 구조에 미치는 영향 반드시 포함
4. "이란 쿠웨이트 공항 공격(④)"이 항공화물·물류비용·수원 기업 수출에 미치는 구체적 영향
5. 수치는 위 ①~⑨에 명시된 최신값 사용 (6/4 기준 WTI $95.14, 브렌트 $96.85, 환율 1530.99원)
6. 지난주(6/1) 우선과제와 완전히 다른 제목·내용 사용
7. 지난주 "다음주 주목이슈"로 예고된 사건들의 실제 결과를 이번주 내용에 반영 (하원 결의·쿠웨이트 공격 등)

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
      "title": "대응과제 제목 (간결하게)",
      "description": "과제 내용 및 기대효과 2~3줄",
      "priority": "즉시|단기|중기",
      "근거": {{
        "타지자체_벤치마킹": "(선택) 수집 기사 확인 타지자체 사례+출처만. 없으면 이 필드 생략",
        "전문가_의견": "(선택) 수집 기사 확인 전문가 의견+출처만. 없으면 이 필드 생략",
        "보고서_근거": "(선택) 수집 기사 확인 보고서+출처만. 없으면 이 필드 생략"
      }}
    }},
    {{
      "순위": 2,
      "title": "대응과제 제목",
      "description": "과제 내용 및 기대효과 2~3줄",
      "priority": "즉시|단기|중기",
      "근거": {{
        "타지자체_벤치마킹": "(선택) 수집 기사 확인 사례+출처만. 없으면 이 필드 생략",
        "전문가_의견": "(선택) 수집 기사 확인 전문가 의견+출처만. 없으면 이 필드 생략",
        "보고서_근거": "(선택) 수집 기사 확인 보고서+출처만. 없으면 이 필드 생략"
      }}
    }},
    {{
      "순위": 3,
      "title": "대응과제 제목",
      "description": "과제 내용 및 기대효과 2~3줄",
      "priority": "즉시|단기|중기",
      "근거": {{
        "타지자체_벤치마킹": "(선택) 수집 기사 확인 사례+출처만. 없으면 이 필드 생략",
        "전문가_의견": "(선택) 수집 기사 확인 전문가 의견+출처만. 없으면 이 필드 생략",
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
        war_summary     = load_analyzed_summary(analyzed_path, max_items=15),  # 전황 상위 15건 + country_response/korea 5건
        domestic_summary= load_summary(domestic_path),
        paradigm_summary= load_summary(paradigm_path),
        yt_summary      = load_summary(yt_path),
        prev_summary    = load_prev_summary(POLICY_DIR, date_str),
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

    # ── 후처리: 빈 타지자체 필드 자동 제거 ──────────────────────────────
    # 수집된 사례 없는 lga_responses 항목 제거
    EMPTY_MARKERS = ["수집된 사례 없음", "수집 기사 없음", "없음", ""]
    if "lga_responses" in result:
        result["lga_responses"] = [
            lga for lga in result["lga_responses"]
            if lga.get("confirmed_action", "").strip() not in EMPTY_MARKERS
            and not lga.get("confirmed_action", "").strip().startswith("수집된 사례 없음")
        ]

    # 민생경제_분석 타지자체_현황 빈 값 제거
    for section in result.get("민생경제_분석", {}).values():
        if isinstance(section, dict):
            for key in ["타지자체_현황"]:
                val = section.get(key, "")
                if not val or any(m in val for m in EMPTY_MARKERS[:3]):
                    section.pop(key, None)

    # 우선_대응과제 근거 빈 필드 제거
    for task in result.get("우선_대응과제", []):
        근거 = task.get("근거", {})
        for key in ["타지자체_벤치마킹", "전문가_의견", "보고서_근거"]:
            val = 근거.get(key, "")
            if not val or any(m in val for m in EMPTY_MARKERS[:3]):
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
