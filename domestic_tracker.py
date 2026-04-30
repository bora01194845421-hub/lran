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
    """유가 수집 — OPINET API 우선, 실패 시 웹 스크래핑 대체"""
    result = {"source": "오피넷", "collected_at": datetime.utcnow().isoformat()}

    # ── 1차: OPINET 공식 API (키 있을 때)
    if OPINET_API_KEY:
        try:
            url = "https://www.opinet.or.kr/api/avgAllPrice.do"
            params = {"code": OPINET_API_KEY, "out": "json"}
            r = requests.get(url, params=params, headers=HEADERS, timeout=10)
            data = r.json()
            items = data.get("RESULT", {}).get("OIL", [])
            for item in items:
                if item.get("PRODCD") == "B027":
                    result["gasoline_national"] = float(item.get("PRICE", 0))
                elif item.get("PRODCD") == "D047":
                    result["diesel_national"] = float(item.get("PRICE", 0))
            url2 = "https://www.opinet.or.kr/api/avgSidoPrice.do"
            r2 = requests.get(url2, params={**params, "sido": "06"}, headers=HEADERS, timeout=10)
            items2 = r2.json().get("RESULT", {}).get("OIL", [])
            for item in items2:
                if item.get("PRODCD") == "B027":
                    result["gasoline_gyeonggi"] = float(item.get("PRICE", 0))
            logger.info(f"[오피넷 API] 휘발유 전국={result.get('gasoline_national')} 경기={result.get('gasoline_gyeonggi')}")
            return result
        except Exception as e:
            logger.warning(f"[오피넷 API] 실패: {e}")

    # ── 2차: 오피넷 공개 JSON API (데모키)
    try:
        demo_url = "https://www.opinet.or.kr/api/avgAllPrice.do"
        demo_params = {"code": "F186170631", "out": "json"}
        r2 = requests.get(demo_url, params=demo_params, headers=HEADERS, timeout=10)
        items2 = r2.json().get("RESULT", {}).get("OIL", [])
        for item in items2:
            if item.get("PRODCD") == "B027":
                result["gasoline_national"] = float(item.get("PRICE", 0))
            elif item.get("PRODCD") == "D047":
                result["diesel_national"] = float(item.get("PRICE", 0))
        if result.get("gasoline_national"):
            logger.info(f"[오피넷 데모키] 휘발유 전국={result['gasoline_national']}")
    except Exception as e:
        logger.warning(f"[오피넷 데모키] 실패: {e}")

    # ── 3차: 오피넷 메인 페이지 스크래핑 (다중 셀렉터)
    if not result.get("gasoline_national"):
        try:
            url = "https://www.opinet.or.kr/user/main/mainView.do"
            r = requests.get(url, headers=HEADERS, timeout=12)
            soup = BeautifulSoup(r.text, "html.parser")
            selectors = [
                ".oil_price_wrap .price", "#gasolineAll", ".gasoline_price",
                "td.price", ".avgPrice", "#avgPrice_b027",
                "span.num", ".oil-num",
            ]
            for sel in selectors:
                el = soup.select_one(sel)
                if el:
                    txt = el.get_text(strip=True).replace(",", "").replace("원", "").strip()
                    try:
                        val = float(txt)
                        if 1000 < val < 3000:
                            result["gasoline_national"] = val
                            logger.info(f"[오피넷 스크래핑:{sel}] 휘발유={val}")
                            break
                    except ValueError:
                        continue
        except Exception as e:
            logger.warning(f"[오피넷 스크래핑] 실패: {e}")

    # ── 4차: GlobalPetrolPrices — 오피넷 접근 불가 시 대체
    if not result.get("gasoline_national"):
        try:
            gpp_url = "https://www.globalpetrolprices.com/South-Korea/gasoline_prices/"
            r_gpp = requests.get(gpp_url, headers=HEADERS, timeout=12)
            soup_gpp = BeautifulSoup(r_gpp.text, "html.parser")
            for table in soup_gpp.select("table"):
                rows = table.select("tr")
                for row in rows:
                    cells = [td.get_text(strip=True) for td in row.select("td,th")]
                    # "Current price" 행의 KRW 가격 파싱
                    if len(cells) >= 2 and "Current price" in cells[0]:
                        price_str = cells[1].replace(",", "").strip()
                        try:
                            val = float(price_str)
                            if 1000 < val < 4000:   # KRW/Liter 범위
                                result["gasoline_national"] = val
                                result["gasoline_source"] = "GlobalPetrolPrices"
                                logger.info(f"[GlobalPetrolPrices] 한국 휘발유={val}원/L")
                                break
                        except ValueError:
                            continue
                if result.get("gasoline_national"):
                    break
        except Exception as e:
            logger.warning(f"[GlobalPetrolPrices] 실패: {e}")

    # ── 3차: Yahoo Finance — WTI·브렌트·RBOB 휘발유
    def _yahoo(ticker: str):
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        return r.json()["chart"]["result"][0]["meta"].get("regularMarketPrice")

    try:
        wti = _yahoo("CL=F")
        if wti:
            result["wti_usd"] = round(float(wti), 2)
            logger.info(f"[Yahoo] WTI=${result['wti_usd']}")
    except Exception as e:
        logger.warning(f"[Yahoo WTI] 실패: {e}")

    try:
        brent = _yahoo("BZ=F")
        if brent:
            result["brent_usd"] = round(float(brent), 2)
            logger.info(f"[Yahoo] 브렌트=${result['brent_usd']}")
    except Exception as e:
        logger.warning(f"[Yahoo Brent] 실패: {e}")

    # ── 두바이유 (한국 중동 수입 기준가) — EIA 무료 API → KNOC 스크래핑 순으로 시도
    try:
        # EIA v2 API (DEMO_KEY, 두바이 현물가 RDUBC)
        eia_url = (
            "https://api.eia.gov/v2/petroleum/pri/spt/data/"
            "?api_key=DEMO_KEY&frequency=daily"
            "&data[0]=value&facets[series][]=RDUBC"
            "&sort[0][column]=period&sort[0][direction]=desc&length=3"
        )
        eia_r = requests.get(eia_url, headers=HEADERS, timeout=12)
        eia_data = eia_r.json()
        eia_rows = eia_data.get("response", {}).get("data", [])
        if eia_rows and eia_rows[0].get("value"):
            result["dubai_usd"] = round(float(eia_rows[0]["value"]), 2)
            result["dubai_date"] = eia_rows[0].get("period", "")
            logger.info(f"[EIA] 두바이유=${result['dubai_usd']} ({result['dubai_date']})")
    except Exception as e:
        logger.warning(f"[EIA 두바이유] 실패: {e}")

    # EIA 실패 시 KNOC 홈페이지 스크래핑
    if not result.get("dubai_usd"):
        try:
            knoc_url = "https://www.knoc.co.kr/sub02/sub02_1_2.jsp"
            kr = requests.get(knoc_url, headers=HEADERS, timeout=12)
            ksoup = BeautifulSoup(kr.text, "html.parser")
            # 두바이 원유 가격 셀 파싱
            for td in ksoup.select("td"):
                txt = td.get_text(strip=True).replace(",", "")
                try:
                    val = float(txt)
                    if 50 < val < 200:   # 합리적 유가 범위
                        result["dubai_usd"] = round(val, 2)
                        logger.info(f"[KNOC] 두바이유=${result['dubai_usd']}")
                        break
                except ValueError:
                    continue
        except Exception as e:
            logger.warning(f"[KNOC 두바이유] 실패: {e}")

    # 두 소스 모두 실패 시 Brent 기준 추산 (두바이는 통상 Brent -1~2$/bbl)
    if not result.get("dubai_usd") and result.get("brent_usd"):
        result["dubai_usd"] = round(result["brent_usd"] - 1.5, 2)
        result["dubai_note"] = "Brent 기반 추산 (-$1.5/bbl)"
        logger.info(f"[추산] 두바이유=${result['dubai_usd']} (Brent 기반)")

    # RBOB 휘발유 선물 (USD/갤런) → 참고값 저장
    try:
        rbob = _yahoo("RB=F")
        if rbob:
            result["rbob_usd_gal"] = round(float(rbob), 4)
            logger.info(f"[Yahoo] RBOB=${result['rbob_usd_gal']}/gal")
    except Exception as e:
        logger.warning(f"[Yahoo RBOB] 실패: {e}")

    return result


def fetch_exchange_rate() -> dict:
    """환율 수집 — frankfurter.app 무료 API (키 불필요)"""
    result = {"source": "frankfurter.app", "collected_at": datetime.utcnow().isoformat()}
    try:
        url = "https://api.frankfurter.app/latest"
        params = {"from": "USD", "to": "KRW,EUR,JPY,CNY"}
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = r.json()
        rates = data.get("rates", {})
        result["USD_KRW"] = rates.get("KRW")
        result["EUR_KRW"] = round(rates.get("EUR", 0) and rates.get("KRW", 0) / rates.get("EUR", 1), 2) if rates.get("EUR") else None
        result["date"]    = data.get("date")
        logger.info(f"[환율] USD/KRW={result.get('USD_KRW')}")
    except Exception as e:
        logger.warning(f"[환율] 실패: {e}")
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
        "date":            target_date,
        "collected_at":    datetime.utcnow().isoformat(),
        "oil_price":       fetch_opinet_price(),
        "exchange_rate":   fetch_exchange_rate(),
        "cpi":             fetch_kostat_cpi(),
        "gas_price":       fetch_gas_price(),
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
