# 이란전쟁 민생 이슈 발굴 에이전트

**수원시정연구원** | 미-이란전쟁(2026) → 수원시 민생 영향 자동 분석  
28개 소스 수집 → Claude AI 분석 → Streamlit 대시보드

- **GitHub**: https://github.com/bora01194845421-hub/lran

---

## 환경 요구사항

- Python 3.10 이상
- Git

---

## 최초 세팅 (1회)

### 1. 레포 클론
```bash
git clone https://github.com/bora01194845421-hub/lran.git
cd lran
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```
Windows에서는 `setup.bat` 더블클릭

### 3. .env 파일 설정
팀장에게 받은 `.env` 파일을 프로젝트 루트에 넣기

```
ANTHROPIC_API_KEY=sk-ant-...   ← 필수
NEWSAPI_KEY=
GUARDIAN_API_KEY=
YOUTUBE_API_KEY=
```

---

## 매번 작업할 때

```bash
# 1. 항상 먼저 최신 코드 받기 (필수!)
git pull origin main

# 2. 코드 수정

# 3. 파이프라인 실행
python orchestrator.py

# 4. 특정 날짜 재실행
python orchestrator.py --date 2026-05-19

# 5. 결과 push
git add .
git commit -m "작업 내용"
git push
```

---

## 대시보드 실행

```bash
streamlit run dashboard.py --server.port 8502
```
Windows에서는 `start_dashboard.bat` 더블클릭  
→ 브라우저에서 http://localhost:8502 접속

---

## GitHub Actions (수동 실행)

파이프라인을 GitHub에서 실행하려면:

1. https://github.com/bora01194845421-hub/lran 접속
2. **Actions** 탭 클릭
3. **이란전쟁 파이프라인 자동 실행** 선택
4. **Run workflow** 버튼 클릭

→ 실행 완료 후 결과가 자동으로 data/ 폴더에 저장됩니다.

---

## 파이프라인 구조

```
orchestrator.py (총괄 실행)
    │
    ├── [Layer 1: 수집]
    │     ├── collector.py              뉴스 RSS (Reuters·BBC·Al Jazeera 등)
    │     ├── intl_org_collector.py     국제기구 (IEA·IMF·OECD·WB 등)
    │     ├── kr_research_collector.py  연구기관 (KEEI·KIEP·KDI 등)
    │     ├── domestic_tracker.py       국내 지표 (오피넷·통계청·가스공사)
    │     └── youtube_collector.py      유튜브 검색 수집
    │
    ├── [Layer 2: 정제]
    │     └── dedup.py
    │
    ├── [Layer 3: 분석 - Claude AI]
    │     ├── analyzer.py               뉴스 분류·요약·중요도
    │     ├── paradigm_detector.py      패러다임 변화 신호 감지
    │     ├── country_response_tracker.py  각국·정부부처 대응 추적
    │     └── minseang_analyzer.py      수원시 민생 영향 + 정책 제언
    │
    └── [Layer 4: 출력]
          ├── reporter.py               HTML 일일 브리핑
          └── dashboard.py              Streamlit 대시보드
```

---

## 파일 구조

```
lran/
├── CLAUDE.md
├── orchestrator.py             파이프라인 총괄
├── scheduler.py                자동 스케줄러 (로컬용)
├── dashboard.py                Streamlit 대시보드
├── config.py                   전체 설정
├── collector.py
├── intl_org_collector.py
├── kr_research_collector.py
├── domestic_tracker.py
├── youtube_collector.py
├── analyzer.py
├── paradigm_detector.py
├── country_response_tracker.py
├── minseang_analyzer.py
├── reporter.py
├── setup.bat                   최초 세팅 (Windows)
├── run_pipeline.bat            파이프라인 실행
├── start_dashboard.bat         대시보드 실행
├── requirements.txt
├── .env.example                API 키 템플릿
└── data/
    ├── analyzed/               분석 완료
    ├── country_response/       각국 대응 분석
    ├── domestic/               국내 지표
    ├── paradigm/               패러다임 신호
    ├── policy/                 민생분석·정책제언
    ├── youtube/                유튜브 요약
    └── reports/                최종 HTML 리포트
```

---

## 협업 규칙

```
작업 시작 전 : git pull origin main  ← 반드시!
작업 완료 후 : git add . → git commit → git push
충돌 발생 시 : 팀장에게 문의
```

---

## 주요 설정 (config.py)

| 항목 | 설명 |
|------|------|
| KEYWORDS_EN / KEYWORDS_KO | 뉴스 수집 키워드 |
| CLAUDE_MODEL | 분석 모델 (기본: claude-sonnet-4-5) |
| SUWON_CONTEXT | 수원시 민생 분석 기준 |
| TREND_COUNTRIES | 각국 대응 추적 대상 |
| KR_MINISTRIES | 한국 정부부처 추적 대상 |

---

## 문의

- 팀장 GitHub: bora01194845421-hub
- 레포: https://github.com/bora01194845421-hub/lran
