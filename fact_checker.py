"""
Fact Checker — 수집 기사 핵심 주장 사실 검증 모듈
파이프라인 Layer 3.5: analyzer → fact_checker → minseang_analyzer

동작 방식:
  1. analyzed_YYYYMMDD.json 에서 importance≥4 기사 상위 N건 선택
  2. Claude API로 각 기사에서 검증 가능한 핵심 주장 2개 추출
  3. 검증 엔진 우선순위:
       ① Perplexity API  (PERPLEXITY_API_KEY 설정 시)
       ② Brave Search API (BRAVE_API_KEY 설정 시)
       ③ Claude 단독     (fallback — 학습 지식 기반)
  4. 결과를 data/fact_check/fact_check_YYYYMMDD.json 저장

출력 필드:
  verdict     : "검증됨" | "불일치" | "미확인"
  confidence  : 0.0 ~ 1.0
  evidence    : 검증 근거 요약
  sources     : 참고 URL 목록
"""

import json
import logging
import time
from datetime import date, datetime
from pathlib import Path

import requests
import anthropic

from config import (
    ANTHROPIC_API_KEY, CLAUDE_MODEL,
    BRAVE_API_KEY, ANALYZED_DIR,
    BASE_DIR, DATA_DIR,
)

logger = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ── 검증 대상 설정 ──────────────────────────────────────────────────────────
MAX_ARTICLES   = 10   # 검증할 기사 최대 수
CLAIMS_PER_ART = 2    # 기사당 추출할 주장 수
MIN_IMPORTANCE = 4    # 최소 중요도
FACT_CHECK_DIR = DATA_DIR / "fact_check"
FACT_CHECK_DIR.mkdir(parents=True, exist_ok=True)

# Perplexity API 키 (config에 없으므로 env에서 직접 로드)
import os
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")

HEADERS_COMMON = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


# ══════════════════════════════════════════════════════════════════════════════
# 1. 핵심 주장 추출 (Claude)
# ══════════════════════════════════════════════════════════════════════════════

def extract_claims(article: dict) -> list[str]:
    """기사에서 검증 가능한 사실적 주장 N개를 추출"""
    title   = article.get("title", "")
    summary = article.get("summary_ko", "") or article.get("summary", "")
    source  = article.get("source", "")

    prompt = f"""다음 기사에서 사실 검증이 필요한 구체적·수치적 핵심 주장 {CLAIMS_PER_ART}개를 추출하세요.

기사 출처: {source}
제목: {title}
요약: {summary}

조건:
- 검증 가능한 구체적 사실 (날짜, 수치, 인물 발언 포함 우선)
- 의견·분석·예측 제외
- 한 문장으로 간결하게
- 반드시 JSON 배열만 반환: ["주장1", "주장2"]"""

    try:
        resp = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        claims = json.loads(raw)
        return claims if isinstance(claims, list) else []
    except Exception as e:
        logger.warning(f"[주장추출] '{title[:40]}' 실패: {e}")
        return []


# ══════════════════════════════════════════════════════════════════════════════
# 2. 검증 엔진
# ══════════════════════════════════════════════════════════════════════════════

def verify_with_perplexity(claim: str) -> dict:
    """Perplexity Sonar API로 실시간 웹 검색 기반 사실 검증"""
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a fact-checker for news about the 2026 Iran-US war. "
                    "Search the web and verify the given claim. "
                    "Respond ONLY in JSON: "
                    "{\"verdict\": \"검증됨|불일치|미확인\", "
                    "\"confidence\": 0.0-1.0, "
                    "\"evidence\": \"근거 요약 (한국어)\", "
                    "\"sources\": [\"url1\", \"url2\"]}"
                ),
            },
            {"role": "user", "content": f"다음 주장을 검증하세요: {claim}"},
        ],
        "return_citations": True,
        "search_recency_filter": "month",
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=20)
        r.raise_for_status()
        data = r.json()
        text = data["choices"][0]["message"]["content"].strip()
        text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        # citations 추가
        citations = data.get("citations", [])
        if citations and not result.get("sources"):
            result["sources"] = citations[:3]
        result["engine"] = "perplexity"
        return result
    except Exception as e:
        logger.warning(f"[Perplexity] 실패: {e}")
        return {}


def verify_with_brave(claim: str) -> dict:
    """Brave Search API + Claude로 검증"""
    # ① Brave로 관련 기사 검색
    search_url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": BRAVE_API_KEY,
    }
    query = f"{claim} 2026 Iran war"
    try:
        r = requests.get(
            search_url, headers=headers,
            params={"q": query, "count": 5, "freshness": "pm"},
            timeout=10,
        )
        r.raise_for_status()
        results = r.json().get("web", {}).get("results", [])
    except Exception as e:
        logger.warning(f"[Brave검색] 실패: {e}")
        return {}

    if not results:
        return {}

    # ② 검색 결과 텍스트 구성
    snippets = "\n".join(
        f"- [{res.get('title','')}] {res.get('description','')[:150]} ({res.get('url','')})"
        for res in results[:5]
    )
    source_urls = [res.get("url", "") for res in results[:3]]

    # ③ Claude로 평가
    prompt = f"""다음 주장을 검색 결과를 근거로 사실 검증하세요.

검증할 주장: {claim}

검색 결과:
{snippets}

반드시 JSON만 반환하세요:
{{"verdict": "검증됨|불일치|미확인",
  "confidence": 0.0~1.0,
  "evidence": "검색 결과 기반 근거 요약 (한국어, 1~2줄)"}}"""

    try:
        resp = client.messages.create(
            model=CLAUDE_MODEL, max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip().replace("```json","").replace("```","").strip()
        result = json.loads(raw)
        result["sources"] = source_urls
        result["engine"]  = "brave+claude"
        return result
    except Exception as e:
        logger.warning(f"[Brave+Claude 평가] 실패: {e}")
        return {}


def verify_with_claude_only(claim: str, article: dict) -> dict:
    """Claude 단독 검증 (학습 데이터 기반 — fallback)"""
    title  = article.get("title", "")
    source = article.get("source", "")

    prompt = f"""다음 주장을 이란-미국 전쟁(2026) 관련 지식을 바탕으로 검증하세요.

출처: [{source}] {title}
검증할 주장: {claim}

판단 기준:
- 검증됨: 학습된 정보와 일치하거나 신뢰할 수 있는 소스와 부합
- 불일치: 알려진 사실과 명백히 다름
- 미확인: 정보 부족으로 판단 불가

반드시 JSON만 반환:
{{"verdict": "검증됨|불일치|미확인",
  "confidence": 0.0~1.0,
  "evidence": "판단 근거 (한국어, 1~2줄)",
  "sources": []}}"""

    try:
        resp = client.messages.create(
            model=CLAUDE_MODEL, max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip().replace("```json","").replace("```","").strip()
        result = json.loads(raw)
        result["engine"] = "claude-only"
        return result
    except Exception as e:
        logger.warning(f"[Claude단독] 실패: {e}")
        return {
            "verdict": "미확인", "confidence": 0.0,
            "evidence": f"검증 오류: {e}", "sources": [],
            "engine": "claude-only",
        }


def verify_claim(claim: str, article: dict) -> dict:
    """검증 엔진 자동 선택 (Perplexity > Brave > Claude)"""
    result = {}

    if PERPLEXITY_API_KEY:
        logger.info(f"  [검증-Perplexity] {claim[:50]}...")
        result = verify_with_perplexity(claim)
    elif BRAVE_API_KEY:
        logger.info(f"  [검증-Brave] {claim[:50]}...")
        result = verify_with_brave(claim)

    if not result:
        logger.info(f"  [검증-Claude] {claim[:50]}...")
        result = verify_with_claude_only(claim, article)

    result["claim"] = claim
    return result


# ══════════════════════════════════════════════════════════════════════════════
# 3. 메인 실행
# ══════════════════════════════════════════════════════════════════════════════

def run(target_date: str = None) -> Path:
    if target_date is None:
        target_date = date.today().strftime("%Y-%m-%d")

    date_str = target_date.replace("-", "")
    logger.info(f"=== FactChecker 시작: {target_date} ===")

    # 엔진 확인
    if PERPLEXITY_API_KEY:
        engine_name = "Perplexity Sonar"
    elif BRAVE_API_KEY:
        engine_name = "Brave Search + Claude"
    else:
        engine_name = "Claude 단독 (fallback)"
    logger.info(f"검증 엔진: {engine_name}")

    # analyzed 데이터 로드
    analyzed_path = ANALYZED_DIR / f"analyzed_{date_str}.json"
    if not analyzed_path.exists():
        logger.warning(f"파일 없음: {analyzed_path}")
        return None

    with open(analyzed_path, encoding="utf-8") as f:
        articles = json.load(f)

    # 검증 대상 선택: importance ≥ MIN_IMPORTANCE, filtered/unknown 제외
    SKIP_CATS = {"filtered", "unknown"}
    candidates = [
        a for a in articles
        if a.get("importance", 0) >= MIN_IMPORTANCE
        and a.get("category", "unknown") not in SKIP_CATS
    ]
    candidates.sort(key=lambda x: x.get("importance", 0), reverse=True)
    targets = candidates[:MAX_ARTICLES]
    logger.info(f"검증 대상: {len(targets)}건 / 전체 {len(articles)}건")

    # 검증 실행
    results = []
    stats = {"verified": 0, "disputed": 0, "unverified": 0, "total_claims": 0}

    for art in targets:
        title = art.get("title", "")[:60]
        logger.info(f"  → [{art.get('source','')}] {title}")

        # 주장 추출
        claims = extract_claims(art)
        if not claims:
            logger.info(f"    주장 추출 실패 — 건너뜀")
            continue

        # 각 주장 검증
        verified_claims = []
        for claim in claims:
            vc = verify_claim(claim, art)
            verified_claims.append(vc)
            stats["total_claims"] += 1

            v = vc.get("verdict", "미확인")
            if v == "검증됨":    stats["verified"]  += 1
            elif v == "불일치":  stats["disputed"]  += 1
            else:                stats["unverified"] += 1

            time.sleep(0.5)  # API 레이트 리밋 방지

        # 기사 전체 판정 (주장들의 다수결)
        verdicts = [vc.get("verdict","미확인") for vc in verified_claims]
        if verdicts.count("검증됨") >= len(verdicts) / 2:
            overall = "검증됨"
        elif "불일치" in verdicts:
            overall = "불일치"
        else:
            overall = "미확인"

        avg_conf = sum(vc.get("confidence", 0) for vc in verified_claims) / max(len(verified_claims), 1)

        results.append({
            "article_id":      art.get("id", ""),
            "title":           art.get("title", ""),
            "source":          art.get("source", ""),
            "url":             art.get("url", ""),
            "importance":      art.get("importance", 0),
            "category":        art.get("category", ""),
            "claims":          verified_claims,
            "overall_verdict": overall,
            "avg_confidence":  round(avg_conf, 2),
            "checked_at":      datetime.utcnow().isoformat(),
        })

    # 결과 저장
    output = {
        "date":           target_date,
        "generated_at":   datetime.utcnow().isoformat(),
        "engine":         engine_name,
        "stats": {
            "articles_checked": len(results),
            "total_claims":     stats["total_claims"],
            "verified":         stats["verified"],
            "disputed":         stats["disputed"],
            "unverified":       stats["unverified"],
            "verified_rate":    round(
                stats["verified"] / max(stats["total_claims"], 1) * 100, 1
            ),
        },
        "results": results,
    }

    out_path = FACT_CHECK_DIR / f"fact_check_{date_str}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    logger.info(
        f"검증 완료: {len(results)}건 기사 / "
        f"주장 {stats['total_claims']}개 "
        f"(검증됨 {stats['verified']} · 불일치 {stats['disputed']} · 미확인 {stats['unverified']})"
    )
    logger.info(f"=== FactChecker 완료 → {out_path} ===")
    return out_path


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    run(sys.argv[1] if len(sys.argv) > 1 else None)
