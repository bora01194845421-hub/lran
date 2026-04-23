"""
Domestic Tracker
국내 물가·에너지 지표 자동 수집

수집 대상:
  - 오피넷 API: 수원시·전국 유가 실시간
  - 통계청: 소비자물가지수 (CPI)
  - 한국가스공사: 도시가스 요금 공시
  - 한국전력: 전기요금 공시
  - 경기도 보도자료: 민생 대책 RSS

출력: data/domestic/domestic_YYYYMMDD.json
"""

import json
import logging
import requests
from datetime import date, datetime
from pathlib import Path
from bs4 import BeautifulSoup
from config import DOMESTIC_DIR, OPINET_API_KEY, USER_AGENT, REQUEST_DELAY

logger = logging.getLogger(__name__)
HEADERS = {"User-Agent": USER_AGENT}


def fetch_opinet_price() -> dict:
    """오피넷 API - 수원시·전국 유가"""
    result = {"source": "오피넷", "collected_at": datetime.utcnow().isoformat()}
    try:
        # 전국 평균 유가
        url = "https://www.opinet.or.kr/api/avgAllPrice.do"
        params = {"code": OPINET_API_KEY or "F202209161", "out": "json"}
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = r.json()
        items = data.get("RESULT", {}).get("OIL", [])
        for item in items:
            if item.get("PRODCD") == "B027":   # 휘발유
                result["gasoline_national"] = item.get("PRICE")
            elif item.get("PRODCD") == "D047":  # 경유
                result["diesel_national"] = item.get("PRICE")
        # 수원시 지역 유가 (경기도 코드: 06)
        url2 = "https://www.opinet.or.kr/api/avgSidoPrice.do"
        params2 = {**params, "sido": "06"}
        r2 = requests.get(url2, params=params2, headers=HEADERS, timeout=10)
        data2 = r2.json()
        items2 = data2.get("RESULT", {}).get("OIL", [])
        for item in items2:
            if item.get("PRODCD") == "B027":
                result["gasoline_gyeonggi"] = item.get("PRICE")
        logger.info(f"[오피넷] 휘발유 전국={result.get('gasoline_national')} 경기={result.get('gasoline_gyeonggi')}")
    except Exception as e:
        logger.warning(f"[오피넷] 실패: {e}")
        result["error"] = str(e)
    return result


def fetch_kostat_cpi() -> dict:
    """통계청 소비자물가지수 (최신 발표)"""
    result = {"source": "통계청", "collected_at": datetime.utcnow().isoformat()}
    try:
        # 통계청 KOSIS API (무료)
        url = "https://kosis.kr/openapi/statisticsData.do"
        params = {
            "method":     "getList",
            "apiKey":     "free",  # 실제 사용 시 발급 키 입력
            "orgId":      "101",   # 통계청
            "tblId":      "DT_1J22003",  # 소비자물가지수
            "objL1":      "ALL",
            "format":     "json",
            "jsonVD":     "Y",
            "prdSe":      "M",
            "startPrdDe": date.today().strftime("%Y%m"),
            "endPrdDe":   date.today().strftime("%Y%m"),
        }
        r = requests.get(url, params=params, headers=HEADERS, timeout=12)
        data = r.json()
        if isinstance(data, list) and data:
            result["cpi_latest"] = data[0].get("DT")
            result["period"] = data[0].get("PRD_DE")
        logger.info(f"[통계청] CPI={result.get('cpi_latest')}")
    except Exception as e:
        logger.warning(f"[통계청] 실패 (API키 필요): {e}")
        result["note"] = "KOSIS API 키 발급 후 사용 (kosis.kr/openapi)"
    return result


def fetch_gas_price() -> dict:
    """한국가스공사 도시가스 요금 공시 스크래핑"""
    result = {"source": "한국가스공사", "collected_at": datetime.utcnow().isoformat()}
    try:
        url = "https://www.kogas.or.kr/portal/contents.do?key=2176"
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        # 요금 테이블 추출 시도
        table = soup.select_one("table")
        if table:
            rows = table.select("tr")
            for row in rows[:3]:
                cells = row.select("td")
                if cells:
                    result["latest_row"] = [c.get_text(strip=True) for c in cells]
                    break
        logger.info(f"[가스공사] 수집 완료")
    except Exception as e:
        logger.warning(f"[가스공사] 실패: {e}")
        result["error"] = str(e)
    return result


def fetch_gyeonggi_press() -> list:
    """경기도 보도자료 RSS - 민생 관련 정책"""
    articles = []
    try:
        import feedparser
        url = "https://www.gg.go.kr/bbs/rss.do?bbsId=BBSMSTR_000000000036"
        import time; time.sleep(REQUEST_DELAY)
        r = requests.get(url, headers=HEADERS, timeout=10)
        feed = feedparser.parse(r.text)
        minseang_kw = ["에너지", "민생", "물가", "소상공인", "난방", "전기", "취약"]
        for entry in feed.entries[:20]:
            title = entry.get("title", "")
            if any(kw in title for kw in minseang_kw):
                articles.append({
                    "source":  "경기도보도자료",
                    "title":   title,
                    "url":     entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "data_type": "policy",
                })
        logger.info(f"[경기도] 민생 보도자료 {len(articles)}건")
    except Exception as e:
        logger.warning(f"[경기도] 실패: {e}")
    return articles


def run(target_date: str = None) -> Path:
    if target_date is None:
        from datetime import date
        target_date = date.today().strftime("%Y-%m-%d")

    logger.info(f"=== DomesticTracker 시작: {target_date} ===")

    output = {
        "date":          target_date,
        "collected_at":  datetime.utcnow().isoformat(),
        "oil_price":     fetch_opinet_price(),
        "cpi":           fetch_kostat_cpi(),
        "gas_price":     fetch_gas_price(),
        "gyeonggi_policy": fetch_gyeonggi_press(),
    }

    date_str = target_date.replace("-", "")
    out_path = DOMESTIC_DIR / f"domestic_{date_str}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    logger.info(f"=== DomesticTracker 완료 → {out_path} ===")
    return out_path


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    run(sys.argv[1] if len(sys.argv) > 1 else None)
