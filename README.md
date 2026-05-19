# 이란전쟁 민생 이슈 발굴 에이전트

**수원시정연구원** | 미-이란전쟁(2026) → 수원시 민생 영향 자동 분석  
28개 소스 수집 → Claude AI 분석 → Streamlit 대시보드

---

## 빠른 시작 (Windows)

### 1단계 — 레포 클론
```bash
git clone https://github.com/bora01194845421-hub/lran.git
cd lran
```

### 2단계 — 초기 세팅 (최초 1회)
```
setup.bat 더블클릭
```
> 패키지 설치 + .env 파일 생성까지 자동으로 처리됩니다.  
> .env 파일이 열리면 **팀장에게 받은 API 키**를 붙여넣고 저장하세요.

### 3단계 — 파이프라인 실행
```
run_pipeline.bat 더블클릭
```

### 4단계 — 대시보드 실행
```
start_dashboard.bat 더블클릭
```
> 브라우저에서 http://localhost:8502 접속

---

## 수동 실행 (터미널)

```bash
# 패키지 설치
pip install -r requirements.txt

# 파이프라인 1회 실행
python orchestrator.py

# 특정 날짜 재실행
python orchestrator.py --date 2026-05-19

# 대시보드 실행
streamlit run dashboard.py --server.port 8502
```

---

## .env API 키 안내

`.env.example`을 복사해서 `.env`로 만들고 키를 입력합니다.

| 키 | 필수 여부 | 발급처 |
|----|-----------|--------|
| ANTHROPIC_API_KEY | **필수** | console.anthropic.com |
| NEWSAPI_KEY | 선택 | newsapi.org (무료 100회/월) |
| GUARDIAN_API_KEY | 선택 | open-platform.theguardian.com (무료) |
| NYT_API_KEY | 선택 | developer.nytimes.com (무료 500회/일) |
| BRAVE_API_KEY | 선택 | api.search.brave.com (무료 2000회/월) |
| OPINET_API_KEY | 선택 | www.opinet.co.kr (무료, 회원가입) |
| YOUTUBE_API_KEY | 선택 | console.cloud.google.com |

> ⚠️ **ANTHROPIC_API_KEY만 있으면 기본 동작합니다.**  
> 나머지는 없으면 해당 소스 수집만 건너뜁니다.

---

## 협업 규칙

```
main 브랜치 = 안정 버전
작업 시작 전: git pull origin main
코드 수정 후: git add . → git commit → git push
파이프라인 실행 후: auto_pipeline.bat (데이터 자동 push 포함)
```

---

## 파일 구조

```
├── orchestrator.py       파이프라인 총괄 실행
├── scheduler.py          07:00 / 19:00 자동 실행
├── dashboard.py          Streamlit 대시보드
├── config.py             설정 (API키·경로·키워드)
├── collector.py          뉴스 수집 (RSS·스크래핑)
├── analyzer.py           Claude AI 분석
├── country_response_tracker.py  각국 대응 추적
├── domestic_tracker.py   국내 유가·물가 수집
├── youtube_collector.py  유튜브 검색 수집
├── setup.bat             최초 세팅 (Windows)
├── run_pipeline.bat      파이프라인 실행
├── start_dashboard.bat   대시보드 실행
├── auto_pipeline.bat     파이프라인 + 자동 push
├── requirements.txt
├── .env.example          API 키 템플릿
└── data/                 수집·분석 결과 (자동 생성)
```

---

## Streamlit Cloud 배포

1. [share.streamlit.io](https://share.streamlit.io) 접속
2. New app → Repository: `bora01194845421-hub/lran`
3. Main file: `dashboard.py`
4. Secrets 탭에 `.env` 내용 붙여넣기
5. Deploy

배포 URL: https://lran.streamlit.app (또는 커스텀 URL)
