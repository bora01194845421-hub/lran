# RSS 피드 주소 목록
# 공신력 티어별 분류

# ── 1티어 (최우선 / 매일)
FEEDS_TIER1 = {
    "AP_World":      "https://feeds.apnews.com/rss/apf-worldnews",
    "AP_Top":        "https://feeds.apnews.com/rss/apf-topnews",
    "Reuters_World": "https://feeds.reuters.com/reuters/worldNews",
    "Reuters_Top":   "https://feeds.reuters.com/reuters/topNews",
}

# ── 2티어 (주요 / 매일)
FEEDS_TIER2 = {
    "BBC_MidEast":   "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml",
    "BBC_World":     "https://feeds.bbci.co.uk/news/world/rss.xml",
    "AlJazeera":     "https://www.aljazeera.com/xml/rss/all.xml",
    "Guardian_Iran": "https://www.theguardian.com/world/iran/rss",
    "Guardian_World":"https://www.theguardian.com/world/rss",
    "NYT_World":     "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "FT_World":      "https://www.ft.com/world?format=rss",
    "Bloomberg":     "https://feeds.bloomberg.com/markets/news.rss",
}

# ── 3티어 (군사·정책 / 매일)
FEEDS_TIER3 = {
    "DefenseOne":    "https://www.defenseone.com/rss/all/",
    "BreakingDef":   "https://breakingdefense.com/feed/",
    "Politico":      "https://rss.politico.com/politics-news.xml",
    "Axios":         "https://api.axios.com/feed/",
    "CSIS":          "https://www.csis.org/rss.xml",
    "CFR":           "https://www.cfr.org/rss.xml",
}

# ── 한국어 피드 (주요)
FEEDS_KO = {
    "Yonhap":        "https://www.yna.co.kr/rss/international.xml",
    "Chosun":        "https://www.chosun.com/arc/outboundfeeds/rss/?outputType=xml",
    "Hankyung":      "https://feeds.hankyung.com/article/international.xml",
}

# ── 한국 정책·부처 대응 전용 피드
# 목적: 외교부·산업부·기재부·국토부·식약처·농림부 실제 대응 기사 수집
FEEDS_KO_POLICY = {
    # 연합뉴스 — 정치(부처 발표 빠름) + 경제(에너지·물가 정책) + 사회
    "Yonhap_Politics": "https://www.yna.co.kr/rss/politics.xml",
    "Yonhap_Economy":  "https://www.yna.co.kr/rss/economy.xml",
    "Yonhap_Society":  "https://www.yna.co.kr/rss/society.xml",
    # 뉴시스 — 정부 부처 발표 전문 보도
    "Newsis":          "https://newsis.com/rss/",
    # 뉴스1 — 부처 정책·긴급 발표 빠른 보도
    "News1":           "https://www.news1.kr/rss/politics.xml",
    # 정책브리핑 — 대한민국 정부 공식 정책 발표 (korea.kr)
    "PolicyBriefing":  "https://www.korea.kr/rss/news.do",
    # 헤럴드경제 — 경제부처·에너지 정책 보도
    "HeraldEco":       "https://biz.heraldkorea.com/rss/rssView.php?cat=all",
}

# ── 경기·수원 지역 언론 (지자체 실제 대응 수집용)
# 목적: 타지자체 벤치마킹에 사실 기반 제공 (할루시네이션 방지)
FEEDS_LOCAL_KR = {
    # 수원일보 — 수원시 직접 관련 정책·사업 보도
    "Suwon_Ilbo":   "https://www.suwonilbo.kr/rss/allArticle.xml",
    # 중부일보 — 수원·경기 지역 경제·에너지 정책
    "Jungbu_Ilbo":  "https://www.joongboo.com/rss/allArticle.xml",
    # 인천일보 — 인천 항만·물류·에너지 정책 (수원 연계 벤치마킹)
    "Incheon_Ilbo": "https://www.incheonilbo.com/rss/allArticle.xml",
}

# ── 지정학·각국 대응 동향 피드 (각국 대응 방안 + 이슈 발굴용)
FEEDS_GEOPOLITICS = {
    "WarOnRocks":       "https://warontherocks.com/feed/",         # 군사·전략 심층분석
    "AtlanticCouncil":  "https://www.atlanticcouncil.org/feed/",   # 대서양 동맹 시각
    "AlMonitor":        "https://www.al-monitor.com/rss",          # 중동 전문 미디어
    "MiddleEastEye":    "https://www.middleeasteye.net/rss",       # 중동 현장
    "ForeignAffairs":   "https://www.foreignaffairs.com/rss.xml",  # 국제관계 심층
    "ForeignPolicy":    "https://foreignpolicy.com/feed/",         # 외교정책 전문
    "AsiaTimes":        "https://asiatimes.com/feed/",             # 아시아 시각
    "SCMP_World":       "https://www.scmp.com/rss/91/feed",        # 중국 시각 (홍콩)
    "EurasiaNet":       "https://eurasianet.org/rss.xml",          # 중앙아·러시아 주변
    "MEI":              "https://www.mei.edu/rss.xml",             # 중동연구소
    "RUSI":             "https://rusi.org/rss.xml",                # 영국 왕립국방안보연구소
}

# ── 전문 분야별 피드 (신규 추가 — 접속 테스트 통과 소스만 포함)
FEEDS_SPECIALIZED = {

    # 〔교통·물류·해운〕
    # Splash247: 해운 전문 미디어 (호르무즈 항로 변경·운임 분석)
    "Splash247":        "https://splash247.com/feed/",
    # FreightWaves: 물류·컨테이너 운임 전문 분석
    "FreightWaves":     "https://www.freightwaves.com/news/feed",
    # FlightGlobal: 항공사 비상경영·전쟁보험·항공화물
    "FlightGlobal":     "https://www.flightglobal.com/rss/",
    # AviationWeek: 중동 항공망 재편·항공유 위기
    "AviationWeek":     "https://aviationweek.com/rss.xml",

    # 〔에너지·유가〕
    # OilPrice: 유가·에너지 시장 분석 (호르무즈 봉쇄 직접 영향)
    "OilPrice":         "https://oilprice.com/rss/main",

    # 〔인도주의·난민〕
    # ReliefWeb Iran: OCHA 이란 인도주의 업데이트 (이란 이재민·의료)
    "ReliefWeb_Iran":   "https://reliefweb.int/updates/rss.xml?primary_country=irn",
    # Refugees International: 이란 난민·인도주의 위기
    "RefugeesIntl":     "https://www.refugeesinternational.org/feed",

    # 〔사이버·안보〕
    # Krebs on Security: ICS/SCADA 이란 사이버 해킹 심층 분석
    "KrebsSecurity":    "https://krebsonsecurity.com/feed/",

    # 〔반도체·IT·첨단산업〕
    # EE Times: 반도체 공급망·헬륨·브롬·특수가스 이란전쟁 영향
    "EETimes":          "https://www.eetimes.com/feed/",

    # 〔환경·기후·에너지 전환〕
    # Grist Energy: 이란전쟁 이후 재생에너지 전환 가속 분석
    "Grist_Energy":     "https://grist.org/energy/feed/",

    # 〔외교·다자관계〕
    # International Crisis Group: 이란 외교·분쟁 실시간 분석
    "CrisisGroup":      "https://www.crisisgroup.org/rss.xml",
}

# ── 전체 통합
ALL_FEEDS = {
    **FEEDS_TIER1, **FEEDS_TIER2, **FEEDS_TIER3,
    **FEEDS_KO, **FEEDS_KO_POLICY,
    **FEEDS_GEOPOLITICS, **FEEDS_SPECIALIZED,
    **FEEDS_LOCAL_KR,
}

# ── 공신력 점수 매핑 (정확성 기준)
CREDIBILITY = {
    "AP_World": 9.5,   "AP_Top": 9.5,
    "Reuters_World": 9.6, "Reuters_Top": 9.6,
    "BBC_MidEast": 9.0,   "BBC_World": 9.0,
    "AlJazeera": 8.0,
    "Guardian_Iran": 8.7, "Guardian_World": 8.7,
    "NYT_World": 8.8,
    "FT_World": 9.1,
    "Bloomberg": 9.0,
    "DefenseOne": 8.0,  "BreakingDef": 8.0,
    "Politico": 8.1,
    "Axios": 7.8,
    "CSIS": 8.8,
    "CFR": 8.6,
    "Yonhap": 8.5,
    "Chosun": 7.8,
    "Hankyung": 8.0,
    # 한국 정책·부처 피드
    "Yonhap_Politics": 8.5,
    "Yonhap_Economy":  8.5,
    "Newsis":          8.0,
    "News1":           7.8,
    "PolicyBriefing":  9.0,   # 정부 공식 발표 — 최고 공신력
    "HeraldEco":       7.8,
    # 지정학·각국 대응 분석
    "WarOnRocks": 8.5,
    "AtlanticCouncil": 8.4,
    "AlMonitor": 8.6,
    "MiddleEastEye": 7.8,
    "ForeignAffairs": 9.0,
    "ForeignPolicy": 8.8,
    "AsiaTimes": 7.5,
    "SCMP_World": 8.0,
    "EurasiaNet": 8.0,
    "MEI": 8.5,
    "RUSI": 8.7,
    # 전문 분야 신규 (접속 테스트 통과)
    "Splash247":     7.8,   # 해운
    "FreightWaves":  8.0,   # 물류·컨테이너
    "FlightGlobal":  8.3,   # 항공
    "AviationWeek":  8.5,   # 항공
    "OilPrice":      7.8,   # 에너지·유가
    "ReliefWeb_Iran":8.5,   # 인도주의
    "RefugeesIntl":  8.2,   # 난민
    "KrebsSecurity": 8.5,   # 사이버
    "EETimes":       8.0,   # 반도체·IT
    "Grist_Energy":  7.5,   # 환경·에너지전환
    "CrisisGroup":   9.0,   # 외교·분쟁
    # 경기·수원 지역 언론
    "Suwon_Ilbo":   7.5,
    "Jungbu_Ilbo":  7.5,
    "Incheon_Ilbo": 7.5,
    "Yonhap_Society": 8.5,
}
