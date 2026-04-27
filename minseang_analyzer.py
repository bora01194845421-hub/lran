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

반드시 JSON 형식만 반환하세요."""

PROMPT = """오늘 수집된 다음 데이터를 종합해서 수원시 민생경제 분석과 우선 대응과제를 JSON으로 작성하세요.

[국제 전황 요약]
{war_summary}

[국내 물가·에너지 지표]
{domestic_summary}

[패러다임 변화 신호]
{paradigm_summary}

[유튜브·전문가 브리핑 요약]
{yt_summary}

반환 형식:
{{
  "민생경제_분석": {{
    "지역산업": {{
      "level": "높음|중간|낮음|모니터링",
      "summary": "수원시 지역산업(삼성전자·제조업·수출기업) 영향 분석 2~3줄",
      "key_indicator": "핵심 지표 또는 수치 1줄",
      "타지자체_현황": "유사 산업구조 타 지자체(예: 화성·평택·인천) 대응 현황 1~2줄"
    }},
    "소상공인_자영업": {{
      "level": "높음|중간|낮음|모니터링",
      "summary": "수원시 소상공인·자영업(음식점·배달·운수·유류비) 영향 분석 2~3줄",
      "key_indicator": "핵심 지표 또는 수치 1줄",
      "타지자체_현황": "소상공인 지원 선도 타 지자체(예: 전주·서울) 대응 현황 1~2줄"
    }},
    "시민생활": {{
      "level": "높음|중간|낮음|모니터링",
      "summary": "수원시 시민생활(도시가스·전기료·물가·취약계층) 영향 분석 2~3줄",
      "key_indicator": "핵심 지표 또는 수치 1줄",
      "타지자체_현황": "에너지복지 선도 타 지자체(예: 서울·경기도) 대응 현황 1~2줄"
    }}
  }},
  "우선_대응과제": [
    {{
      "순위": 1,
      "title": "대응과제 제목 (간결하게)",
      "description": "과제 내용 및 기대효과 2~3줄",
      "priority": "즉시|단기|중기",
      "근거": {{
        "타지자체_벤치마킹": "어느 지자체의 어떤 사례를 참고했는가",
        "전문가_의견": "유튜브·전문가 브리핑에서 언급된 관련 내용",
        "보고서_근거": "KEEI·KIEP·KDI·IEA 등 보고서 인용 근거"
      }}
    }},
    {{
      "순위": 2,
      "title": "대응과제 제목",
      "description": "과제 내용 및 기대효과 2~3줄",
      "priority": "즉시|단기|중기",
      "근거": {{
        "타지자체_벤치마킹": "벤치마킹 사례",
        "전문가_의견": "전문가 의견",
        "보고서_근거": "보고서 인용"
      }}
    }},
    {{
      "순위": 3,
      "title": "대응과제 제목",
      "description": "과제 내용 및 기대효과 2~3줄",
      "priority": "즉시|단기|중기",
      "근거": {{
        "타지자체_벤치마킹": "벤치마킹 사례",
        "전문가_의견": "전문가 의견",
        "보고서_근거": "보고서 인용"
      }}
    }}
  ],
  "today_headline": "오늘 수원시가 가장 주목해야 할 민생 이슈 한 줄",
  "urgency": "긴급|주의|모니터링",
  "scout_points": [
    "전황 요약 포인트 1 (수원시 민생 연결 중심)",
    "전황 요약 포인트 2",
    "전황 요약 포인트 3"
  ]
}}"""


def load_summary(path: Path, max_items: int = 5) -> str:
    if not path or not path.exists():
        return "데이터 없음"
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            items = data[:max_items]
            return "\n".join(f"- [{a.get('source','')}] {a.get('title','')} | {a.get('summary_ko','')[:100]}" for a in items)
        elif isinstance(data, dict):
            return json.dumps(data, ensure_ascii=False)[:1500]
    except Exception:
        return "로드 실패"
    return ""


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
        war_summary     = load_summary(analyzed_path),
        domestic_summary= load_summary(domestic_path),
        paradigm_summary= load_summary(paradigm_path),
        yt_summary      = load_summary(yt_path),
    )

    try:
        resp = client.messages.create(
            model=CLAUDE_MODEL, max_tokens=8096,
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
