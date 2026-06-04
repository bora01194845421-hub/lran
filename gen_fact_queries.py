"""
gen_fact_queries.py — 수동 사실검증용 Perplexity 질문 목록 생성기

수집된 기사에서 핵심 주장을 추출하고
Perplexity 채팅창에 복붙할 수 있는 마크다운 파일로 저장합니다.

사용법:
  python gen_fact_queries.py             # 오늘 날짜
  python gen_fact_queries.py 2026-06-01  # 특정 날짜
"""

import json, logging, time, sys
from datetime import date, datetime
from pathlib import Path
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, ANALYZED_DIR, DATA_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

FACT_CHECK_DIR = DATA_DIR / "fact_check"
FACT_CHECK_DIR.mkdir(parents=True, exist_ok=True)

# ── 설정 ──────────────────────────────────────────────────────────────────
MAX_ARTICLES   = 15   # 검증 대상 기사 수
CLAIMS_PER_ART = 2    # 기사당 추출 주장 수
MIN_IMPORTANCE = 4    # 최소 중요도

CAT_LABELS = {
    "military":        "⚔️ 군사·전황",
    "diplomacy":       "🤝 외교·협상",
    "economy":         "💰 경제·금융",
    "energy":          "⛽ 에너지·유가",
    "humanitarian":    "🏥 인도주의",
    "nuclear":         "☢️ 핵·원전",
    "korea":           "🇰🇷 한국 대응",
    "paradigm":        "🔄 패러다임",
    "country_response":"🌍 각국 대응",
    "transport":       "🚢 교통·물류",
    "food_security":   "🌾 식량·농업",
    "semiconductor":   "🔬 반도체·IT",
    "cyber":           "🔐 사이버",
    "environment":     "🌿 환경·기후",
}


def extract_claims(article: dict) -> list[str]:
    """기사에서 Perplexity로 검증할 핵심 주장 추출"""
    title   = article.get("title", "")
    summary = article.get("summary_ko", "") or article.get("summary", "")
    source  = article.get("source", "")

    prompt = f"""다음 기사에서 퍼플렉시티(Perplexity) 검색으로 사실 확인이 가능한 구체적 주장 {CLAIMS_PER_ART}개를 추출하세요.

출처: {source}
제목: {title}
요약: {summary}

조건:
- 날짜·수치·인명·지명이 포함된 검증 가능한 사실
- 분석·예측·의견 제외
- 한국어, 한 문장으로 간결하게
- 반드시 JSON 배열만 반환: ["주장1", "주장2"]"""

    try:
        resp = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip().replace("```json","").replace("```","").strip()
        claims = json.loads(raw)
        return claims if isinstance(claims, list) else []
    except Exception as e:
        logger.warning(f"주장 추출 실패 ({title[:30]}): {e}")
        return []


def format_perplexity_query(claim: str, article: dict) -> str:
    """Perplexity 채팅창에 그대로 붙여넣을 수 있는 질문 문장 생성"""
    return (
        f"다음 주장이 사실인지 최신 뉴스를 검색해서 확인해줘. "
        f"출처·날짜와 함께 검증됨/불일치/미확인으로 답해줘:\n"
        f"「{claim}」"
    )


def run(target_date: str = None) -> Path:
    if target_date is None:
        target_date = date.today().strftime("%Y-%m-%d")

    date_str = target_date.replace("-", "")
    logger.info(f"=== 사실검증 질문 목록 생성: {target_date} ===")

    analyzed_path = ANALYZED_DIR / f"analyzed_{date_str}.json"
    if not analyzed_path.exists():
        logger.error(f"파일 없음: {analyzed_path}")
        return None

    with open(analyzed_path, encoding="utf-8") as f:
        articles = json.load(f)

    # 검증 대상 선택
    SKIP_CATS = {"filtered", "unknown", "paradigm"}
    candidates = [
        a for a in articles
        if a.get("importance", 0) >= MIN_IMPORTANCE
        and a.get("category", "unknown") not in SKIP_CATS
    ]
    candidates.sort(key=lambda x: x.get("importance", 0), reverse=True)
    targets = candidates[:MAX_ARTICLES]
    logger.info(f"대상: {len(targets)}건 선택")

    # 카테고리별 분류
    by_cat: dict[str, list] = {}
    for art in targets:
        cat = art.get("category", "unknown")
        by_cat.setdefault(cat, []).append(art)

    # 주장 추출
    all_items = []
    total_claims = 0

    for cat, arts in by_cat.items():
        cat_items = []
        for art in arts:
            logger.info(f"  [{art.get('source','')}] {art.get('title','')[:50]}")
            claims = extract_claims(art)
            if not claims:
                continue

            queries = [
                {
                    "claim":   c,
                    "query":   format_perplexity_query(c, art),
                    "checked": False,
                    "result":  "",
                }
                for c in claims
            ]
            cat_items.append({
                "article": {
                    "title":      art.get("title", ""),
                    "source":     art.get("source", ""),
                    "url":        art.get("url", ""),
                    "importance": art.get("importance", 0),
                    "published":  art.get("published", ""),
                },
                "queries": queries,
            })
            total_claims += len(queries)
            time.sleep(0.3)

        if cat_items:
            all_items.append({"category": cat, "items": cat_items})

    # ── 마크다운 생성 ─────────────────────────────────────────────────────────
    lines = [
        f"# 🔍 사실 검증 대기 목록 — {target_date}",
        f"> 생성: {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  "
        f"기사 **{len(targets)}건**  |  검증 주장 **{total_claims}개**",
        f">",
        f"> **사용법**: 각 질문을 [perplexity.ai](https://perplexity.ai) 채팅창에 복사·붙여넣기",
        f"> **검증 후**: 결과(✅/⚠️/❓)와 근거를 메모란에 기록",
        "",
        "---",
        "",
    ]

    claim_no = 1
    for group in all_items:
        cat   = group["category"]
        label = CAT_LABELS.get(cat, cat)
        lines.append(f"## {label}")
        lines.append("")

        for item in group["items"]:
            art = item["article"]
            src = art["source"]
            ttl = art["title"][:70]
            pub = art["published"][:10] if art.get("published") else ""
            url = art.get("url", "")
            imp = "★" * art.get("importance", 0)

            lines.append(f"### [{src}] {ttl}")
            if pub:
                lines.append(f"📅 {pub}  {imp}")
            if url:
                lines.append(f"🔗 {url}")
            lines.append("")

            for q in item["queries"]:
                lines.append(f"**질문 {claim_no}.**")
                lines.append(f"```")
                lines.append(q["query"])
                lines.append(f"```")
                lines.append(f"- [ ] 검증됨 　- [ ] 불일치 　- [ ] 미확인")
                lines.append(f"- **결과 메모**: _여기에 Perplexity 결과 요약_")
                lines.append("")
                claim_no += 1

        lines.append("---")
        lines.append("")

    # 빠른 복붙용 전체 질문 목록 (부록)
    lines.append("## 📋 전체 질문 빠른 복사 목록")
    lines.append("")
    claim_no2 = 1
    for group in all_items:
        for item in group["items"]:
            for q in item["queries"]:
                lines.append(f"**Q{claim_no2}.** {q['claim']}")
                claim_no2 += 1
    lines.append("")

    md_content = "\n".join(lines)

    # 마크다운 저장
    md_path = FACT_CHECK_DIR / f"fact_queries_{date_str}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    # JSON 저장 (추후 자동화 연동용)
    json_out = {
        "date": target_date,
        "generated_at": datetime.now().isoformat(),
        "stats": {
            "articles": len(targets),
            "claims": total_claims,
        },
        "items": all_items,
    }
    json_path = FACT_CHECK_DIR / f"fact_queries_{date_str}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_out, f, ensure_ascii=False, indent=2)

    logger.info(f"저장 완료:")
    logger.info(f"  마크다운: {md_path}")
    logger.info(f"  JSON:     {json_path}")
    logger.info(f"  총 {total_claims}개 질문 생성")
    return md_path


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else None)
