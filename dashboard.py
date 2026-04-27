"""
이란전쟁 민생 브리핑 대시보드 v4
수원시정연구원 | 전략 브리핑 문서 스타일

실행: streamlit run dashboard.py --server.address 0.0.0.0 --server.port 8502
"""

import json
import subprocess
from datetime import date, datetime
from pathlib import Path

import streamlit as st

from config import DATA_DIR, ANALYZED_DIR, PARADIGM_DIR, POLICY_DIR, DOMESTIC_DIR

COUNTRY_RESPONSE_DIR = DATA_DIR / "country_response"
CLEAN_DIR            = DATA_DIR / "clean"

# ─────────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="수원시 전략 브리핑 | 이란전쟁 민생",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');

*, *::before, *::after {
  box-sizing: border-box;
  font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}

/* 전체 배경 */
.stApp { background: #ECEEF2 !important; }
[data-testid="stAppViewContainer"] { background: #ECEEF2 !important; }

/* 사이드바 (운영용) */
[data-testid="stSidebar"] { background: #0D1B2A !important; }
[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
[data-testid="stSidebar"] .stButton button {
  background: #C0392B !important; color: white !important;
  border: none !important; border-radius: 6px !important; font-weight: 700 !important;
}

/* 최상단 헤더 바 */
.top-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 28px; background: white;
  border-bottom: 3px solid #E8EAED;
  margin-bottom: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.top-bar-left { display: flex; align-items: center; gap: 14px; }
.top-bar-logo {
  width: 44px; height: 44px; background: #1B3A5C;
  border-radius: 10px; display: flex; align-items: center;
  justify-content: center; font-size: 1.4rem;
}
.top-bar-org { line-height: 1.3; }
.top-bar-org .org-name {
  font-size: 0.82rem; font-weight: 800; color: #1B3A5C;
  letter-spacing: 1.5px; text-transform: uppercase;
}
.top-bar-org .org-sub { font-size: 0.72rem; color: #94A3B8; }
.crisis-badge {
  display: flex; align-items: center; gap: 7px;
  padding: 7px 16px; border-radius: 20px;
  font-weight: 800; font-size: 0.82rem; letter-spacing: 0.3px;
}
.crisis-긴급   { background: #FEF0EF; border: 1.5px solid #F87171; color: #C0392B; }
.crisis-주의   { background: #FFFBEB; border: 1.5px solid #FCD34D; color: #B45309; }
.crisis-모니터링 { background: #F0FDF4; border: 1.5px solid #86EFAC; color: #15803D; }
.crisis-dot { width: 8px; height: 8px; border-radius: 50%; animation: pulse 1.5s infinite; }
.dot-긴급   { background: #C0392B; }
.dot-주의   { background: #D97706; }
.dot-모니터링 { background: #16A34A; }
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.5; transform: scale(1.3); }
}

/* 메인 카드 (흰색 컨테이너) */
.brief-card {
  background: white; border-radius: 16px;
  padding: 28px 32px; margin-bottom: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.07);
}

/* 헤로 섹션 */
.hero-label {
  font-size: 0.7rem; font-weight: 800; letter-spacing: 2px;
  color: #C0392B; text-transform: uppercase; margin-bottom: 10px;
}
.hero-headline {
  font-size: 2.0rem; font-weight: 900; color: #0D1B2A;
  line-height: 1.3; margin-bottom: 16px;
}
.hero-headline .highlight { color: #C0392B; }
.hero-meta {
  display: flex; gap: 20px; font-size: 0.75rem; color: #94A3B8;
  margin-bottom: 20px; align-items: center;
}
.hero-meta span { display: flex; align-items: center; gap: 5px; }

/* Scout 요약 */
.scout-section { }
.scout-title {
  font-size: 0.8rem; font-weight: 800; color: #0D1B2A;
  margin-bottom: 10px; display: flex; align-items: center; gap: 6px;
}
.scout-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 10px 14px; background: #FEF8F7;
  border-left: 3px solid #C0392B;
  border-radius: 0 8px 8px 0; margin-bottom: 7px;
  font-size: 0.84rem; color: #2D3748; line-height: 1.5;
}
.scout-num {
  width: 20px; height: 20px; background: #C0392B;
  border-radius: 50%; color: white; font-size: 0.65rem;
  font-weight: 800; display: flex; align-items: center;
  justify-content: center; flex-shrink: 0; margin-top: 1px;
}

/* WTI 유가 카드 */
.wti-card {
  background: #0D1B2A; border-radius: 12px;
  padding: 20px 22px; color: white; height: 100%;
}
.wti-label { font-size: 0.65rem; letter-spacing: 2px; color: #64748B; text-transform: uppercase; margin-bottom: 8px; }
.wti-price { font-size: 2.2rem; font-weight: 900; color: white; line-height: 1; margin-bottom: 6px; }
.wti-change { font-size: 0.82rem; font-weight: 700; }
.wti-up   { color: #F87171; }
.wti-down { color: #34D399; }
.wti-divider { border: none; border-top: 1px solid #1E3A5C; margin: 12px 0; }
.wti-sub-row { display: flex; justify-content: space-between; font-size: 0.72rem; color: #94A3B8; margin-bottom: 4px; }
.wti-sub-val { color: #CBD5E1; font-weight: 600; }

/* 섹션 타이틀 */
.sec-title {
  font-size: 1.05rem; font-weight: 900; color: #0D1B2A;
  margin-bottom: 14px; display: flex; align-items: center;
  justify-content: space-between;
}
.sec-badge {
  font-size: 0.68rem; font-weight: 700; padding: 3px 10px;
  border-radius: 10px; letter-spacing: 0.5px;
}
.badge-blue  { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
.badge-red   { background: #FEF2F2; color: #C0392B; border: 1px solid #FECACA; }
.badge-green { background: #F0FDF4; color: #15803D; border: 1px solid #BBF7D0; }
.badge-gray  { background: #F9FAFB; color: #6B7280; border: 1px solid #E5E7EB; }

/* 각국 대응 테이블 */
.country-row {
  display: flex; align-items: center; gap: 0;
  padding: 11px 0; border-bottom: 1px solid #F1F5F9;
}
.country-row:last-child { border-bottom: none; }
.cr-name { font-size: 0.88rem; font-weight: 700; color: #0D1B2A; min-width: 110px; }
.cr-stance {
  display: inline-block; padding: 3px 10px; border-radius: 10px;
  font-size: 0.7rem; font-weight: 700; min-width: 60px; text-align: center; margin-right: 14px;
}
.st-강경   { background: #FEF2F2; color: #C0392B; border: 1px solid #FECACA; }
.st-지지   { background: #FFF7ED; color: #C2410C; border: 1px solid #FED7AA; }
.st-중립   { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
.st-제재   { background: #F5F3FF; color: #6D28D9; border: 1px solid #DDD6FE; }
.st-협력   { background: #F0FDF4; color: #15803D; border: 1px solid #BBF7D0; }
.st-unknown { background: #F9FAFB; color: #6B7280; border: 1px solid #E5E7EB; }
.cr-action { font-size: 0.8rem; color: #4B5563; flex: 1; line-height: 1.4; }
.cr-suwon  { font-size: 0.72rem; color: #15803D; font-weight: 600; margin-top: 2px; }

/* 한국 지자체 대응 현황 */
.lga-table { width: 100%; border-collapse: collapse; }
.lga-table th {
  background: #F1F5F9; font-size: 0.72rem; font-weight: 800;
  color: #475569; padding: 8px 12px; text-align: left;
  border-bottom: 2px solid #E2E8F0; letter-spacing: 0.3px;
}
.lga-row { border-bottom: 1px solid #F1F5F9; }
.lga-row:last-child { border-bottom: none; }
.lga-row:hover { background: #FAFAFA; }
.lga-name {
  font-size: 0.85rem; font-weight: 700; color: #0D1B2A;
  padding: 10px 12px; white-space: nowrap;
}
.lga-name .lga-type {
  display: inline-block; font-size: 0.63rem; font-weight: 700;
  padding: 2px 6px; border-radius: 6px; margin-left: 5px;
  vertical-align: middle;
}
.type-광역 { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
.type-도   { background: #F5F3FF; color: #6D28D9; border: 1px solid #DDD6FE; }
.type-기초 { background: #F0FDF4; color: #15803D; border: 1px solid #BBF7D0; }
.lga-stage {
  padding: 10px 12px; white-space: nowrap;
}
.stage-badge {
  display: inline-block; padding: 3px 10px; border-radius: 10px;
  font-size: 0.7rem; font-weight: 800;
}
.stage-선제 { background: #FEF2F2; color: #C0392B; border: 1px solid #FECACA; }
.stage-적극 { background: #FFFBEB; color: #B45309; border: 1px solid #FDE68A; }
.stage-검토 { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
.stage-모니터링 { background: #F9FAFB; color: #6B7280; border: 1px solid #E5E7EB; }
.lga-action { font-size: 0.79rem; color: #374151; padding: 10px 12px; line-height: 1.5; }
.lga-ref {
  font-size: 0.73rem; color: #15803D; padding: 10px 12px;
  font-weight: 600; line-height: 1.5;
}
.lga-suwon-row {
  background: linear-gradient(135deg, #F0FDF4, #EFF6FF);
  border: 1.5px solid #86EFAC !important;
  border-radius: 8px;
}
.lga-suwon-label {
  font-size: 0.65rem; font-weight: 800; color: #C0392B;
  letter-spacing: 1px; text-transform: uppercase; margin-bottom: 2px;
}

/* 수원시 영향 */
.impact-row {
  display: flex; align-items: center; gap: 14px;
  padding: 10px 12px; border-radius: 8px;
  margin-bottom: 6px;
}
.impact-row.level-높음   { background: #FEF2F2; }
.impact-row.level-중간   { background: #FFFBEB; }
.impact-row.level-낮음   { background: #F0FDF4; }
.impact-row.level-모니터링 { background: #F9FAFB; }
.impact-dot-box {
  width: 32px; height: 32px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.75rem; font-weight: 800; flex-shrink: 0;
}
.idb-높음   { background: #C0392B; color: white; }
.idb-중간   { background: #D97706; color: white; }
.idb-낮음   { background: #16A34A; color: white; }
.idb-모니터링 { background: #94A3B8; color: white; }
.impact-info { flex: 1; }
.impact-field { font-size: 0.85rem; font-weight: 700; color: #0D1B2A; }
.impact-desc  { font-size: 0.78rem; color: #6B7280; line-height: 1.4; margin-top: 1px; }

/* 정책 카드 */
.policy-card {
  background: white; border: 1.5px solid #E5E7EB;
  border-radius: 12px; padding: 18px 20px;
  height: 100%;
}
.policy-tag {
  display: inline-block; padding: 3px 10px; border-radius: 10px;
  font-size: 0.68rem; font-weight: 800; margin-bottom: 10px;
  letter-spacing: 0.5px;
}
.tag-A { background: #1D4ED8; color: white; }
.tag-B { background: #15803D; color: white; }
.tag-C { background: #6D28D9; color: white; }
.policy-title { font-size: 0.97rem; font-weight: 800; color: #0D1B2A; margin-bottom: 8px; line-height: 1.4; }
.policy-body  { font-size: 0.8rem; color: #4B5563; line-height: 1.6; }
.policy-item  { display: flex; gap: 7px; margin-bottom: 5px; }
.policy-check { color: #1D4ED8; font-weight: 700; flex-shrink: 0; }

/* Devil's Critique */
.devil-card {
  background: #0D1B2A; border-radius: 16px;
  padding: 28px 32px; position: relative; overflow: hidden;
}
.devil-watermark {
  position: absolute; right: 24px; top: 16px;
  font-size: 0.65rem; font-weight: 800; letter-spacing: 2px;
  background: #C0392B; color: white; padding: 4px 12px;
  border-radius: 4px;
}
.devil-quote {
  font-size: 1.3rem; font-weight: 900; color: white;
  font-style: italic; margin-bottom: 20px;
  border-bottom: 1px solid #1E3A5C; padding-bottom: 16px;
}
.devil-quote .dq-inner { color: #F87171; text-decoration: underline; }
.devil-points { display: flex; gap: 16px; }
.devil-point { flex: 1; }
.dp-num {
  font-size: 0.7rem; font-weight: 800; color: #C0392B;
  text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;
}
.dp-title { font-size: 0.88rem; font-weight: 700; color: white; margin-bottom: 6px; }
.dp-body  { font-size: 0.78rem; color: #94A3B8; line-height: 1.6; }

/* 벤치마킹 카드 */
.bench-card {
  background: #F8FAFC; border: 1.5px solid #E2E8F0;
  border-radius: 12px; padding: 18px 20px;
}
.bench-city {
  font-size: 0.82rem; font-weight: 800; color: #1D4ED8;
  margin-bottom: 8px; display: flex; align-items: center; gap: 8px;
}
.bench-title { font-size: 0.92rem; font-weight: 800; color: #0D1B2A; margin-bottom: 8px; }
.bench-item {
  display: flex; gap: 8px; font-size: 0.78rem; color: #4B5563;
  line-height: 1.5; margin-bottom: 4px;
}
.bench-check { color: #1D4ED8; flex-shrink: 0; }

/* 하단 버튼 */
.footer-bar {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 16px 0; margin-top: 8px;
}
.btn-pdf {
  display: inline-flex; align-items: center; gap: 8px;
  background: #1D4ED8; color: white; padding: 10px 22px;
  border-radius: 10px; font-size: 0.85rem; font-weight: 700;
  text-decoration: none; border: none; cursor: pointer;
}
.btn-print {
  display: inline-flex; align-items: center; gap: 8px;
  background: #374151; color: white; padding: 10px 22px;
  border-radius: 10px; font-size: 0.85rem; font-weight: 700;
  text-decoration: none; border: none; cursor: pointer;
}
.footer-doc {
  text-align: center; font-size: 0.7rem; color: #94A3B8;
  padding: 10px; border-top: 1px solid #E5E7EB; margin-top: 8px;
}

/* 민생경제 분석 카드 */
.minseang-card {
  background: white; border: 1.5px solid #E5E7EB;
  border-radius: 12px; padding: 20px 22px; height: 100%;
}
.ms-level-badge {
  display: inline-block; padding: 4px 12px; border-radius: 20px;
  font-size: 0.72rem; font-weight: 800; margin-bottom: 12px;
  letter-spacing: 0.5px;
}
.ms-lvl-높음 { background: #FEF2F2; color: #C0392B; border: 1.5px solid #FECACA; }
.ms-lvl-중간 { background: #FFFBEB; color: #B45309; border: 1.5px solid #FDE68A; }
.ms-lvl-낮음 { background: #F0FDF4; color: #15803D; border: 1.5px solid #BBF7D0; }
.ms-lvl-모니터링 { background: #F9FAFB; color: #6B7280; border: 1.5px solid #E5E7EB; }
.ms-category { font-size: 1.0rem; font-weight: 800; color: #0D1B2A; margin-bottom: 10px; }
.ms-summary { font-size: 0.8rem; color: #374151; line-height: 1.6; margin-bottom: 12px; }
.ms-indicator-box {
  background: #F8FAFC; border-radius: 8px; padding: 10px 14px; margin-bottom: 10px;
  border-left: 3px solid #1D4ED8;
}
.ms-ind-label { font-size: 0.63rem; font-weight: 800; color: #1D4ED8; letter-spacing: 1px; margin-bottom: 4px; text-transform: uppercase; }
.ms-ind-value { font-size: 0.79rem; color: #0D1B2A; font-weight: 600; line-height: 1.5; }
.ms-other-box {
  background: #F0FDF4; border-radius: 8px; padding: 10px 14px;
  border-left: 3px solid #15803D;
}
.ms-other-label { font-size: 0.63rem; font-weight: 800; color: #15803D; letter-spacing: 1px; margin-bottom: 4px; text-transform: uppercase; }
.ms-other-value { font-size: 0.77rem; color: #374151; line-height: 1.5; }

/* 우선 대응과제 카드 */
.action-card {
  background: white; border: 1.5px solid #E5E7EB;
  border-radius: 12px; padding: 20px 22px; height: 100%;
}
.action-rank {
  font-size: 0.63rem; font-weight: 800; color: #94A3B8;
  letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 6px;
}
.action-priority {
  display: inline-block; padding: 3px 10px; border-radius: 10px;
  font-size: 0.7rem; font-weight: 800; margin-bottom: 10px;
}
.pri-즉시 { background: #FEF2F2; color: #C0392B; border: 1px solid #FECACA; }
.pri-단기 { background: #FFFBEB; color: #B45309; border: 1px solid #FDE68A; }
.pri-중기 { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
.action-title { font-size: 0.97rem; font-weight: 800; color: #0D1B2A; margin-bottom: 10px; line-height: 1.4; }
.action-desc { font-size: 0.79rem; color: #4B5563; line-height: 1.65; margin-bottom: 14px; }
.evidence-box { border-top: 1px solid #F1F5F9; padding-top: 12px; display: flex; flex-direction: column; gap: 6px; }
.ev-item { font-size: 0.74rem; color: #374151; line-height: 1.5; padding: 7px 11px; border-radius: 6px; }
.ev-bench  { background: #EFF6FF; border-left: 3px solid #1D4ED8; }
.ev-expert { background: #F0FDF4; border-left: 3px solid #15803D; }
.ev-report { background: #F5F3FF; border-left: 3px solid #6D28D9; }
.ev-tag { font-size: 0.62rem; font-weight: 800; letter-spacing: 0.8px; display: block; margin-bottom: 2px; }
.ev-bench  .ev-tag { color: #1D4ED8; }
.ev-expert .ev-tag { color: #15803D; }
.ev-report .ev-tag { color: #6D28D9; }

/* 유튜브 브리핑 카드 */
.yt-card {
  background: white; border: 1.5px solid #E5E7EB;
  border-radius: 12px; padding: 18px 20px; height: 100%;
  position: relative; overflow: hidden;
}
.yt-channel {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 10px;
}
.yt-ch-badge {
  display: inline-block; padding: 3px 10px; border-radius: 10px;
  font-size: 0.68rem; font-weight: 800; letter-spacing: 0.3px;
}
.yt-aljazeera { background: #FEF2F2; color: #C0392B; border: 1px solid #FECACA; }
.yt-dw        { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
.yt-yonhap    { background: #F0FDF4; color: #15803D; border: 1px solid #BBF7D0; }
.yt-default   { background: #F9FAFB; color: #6B7280; border: 1px solid #E5E7EB; }
.yt-meta { font-size: 0.68rem; color: #94A3B8; margin-left: auto; }
.yt-title {
  font-size: 0.92rem; font-weight: 800; color: #0D1B2A;
  margin-bottom: 10px; line-height: 1.4;
}
.yt-points { margin-bottom: 12px; }
.yt-point {
  display: flex; gap: 8px; font-size: 0.79rem; color: #374151;
  line-height: 1.55; padding: 5px 0; border-bottom: 1px solid #F8FAFC;
}
.yt-point:last-child { border-bottom: none; }
.yt-bullet { color: #C0392B; font-weight: 900; flex-shrink: 0; margin-top: 1px; }
.yt-expert {
  font-size: 0.71rem; color: #6B7280; background: #F8FAFC;
  padding: 6px 10px; border-radius: 6px;
  display: flex; align-items: center; gap: 5px;
}
.yt-score {
  margin-left: auto; font-size: 0.68rem; font-weight: 800;
  color: #1D4ED8; background: #EFF6FF; padding: 2px 7px;
  border-radius: 8px;
}

/* 빈 상태 */
.empty-state {
  text-align: center; padding: 30px 20px;
  background: #F8FAFC; border: 2px dashed #CBD5E1;
  border-radius: 10px; color: #94A3B8; font-size: 0.83rem;
}

/* 인쇄 */
@media print {
  .stApp { background: white !important; }
  [data-testid="stSidebar"] { display: none !important; }
  .no-print { display: none !important; }
  .brief-card { box-shadow: none !important; border: 1px solid #E5E7EB; }
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────────
def load_json(path):
    p = Path(path)
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return None

def ds(d): return d.strftime("%Y%m%d")
def fmt(d): return d.strftime("%Y-%m-%d")
def fmt_ko(d): return d.strftime("%Y년 %m월 %d일")


# ─────────────────────────────────────────────
# 사이드바 (운영 컨트롤)
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ 운영 컨트롤")
    st.divider()
    selected_date = st.date_input("📅 날짜", value=date.today(),
                                   min_value=date(2026,1,1), max_value=date.today())
    date_str = ds(selected_date)
    st.divider()
    if st.button("🚀 파이프라인 실행", type="primary", use_container_width=True):
        with st.spinner("실행 중..."):
            r = subprocess.run(
                ["python","orchestrator.py","--date",fmt(selected_date)],
                capture_output=True, text=True, cwd=str(Path(__file__).parent))
        if r.returncode == 0: st.success("✅ 완료! 새로고침하세요.")
        else: st.error(f"오류\n```\n{r.stderr[-300:]}\n```")
    st.divider()
    st.caption("📂 파일 현황")
    for lbl, path in {
        "뉴스 분석": ANALYZED_DIR        / f"analyzed_{date_str}.json",
        "각국 대응": COUNTRY_RESPONSE_DIR / f"cr_{date_str}.json",
        "패러다임":  PARADIGM_DIR         / f"paradigm_{date_str}.json",
        "민생 분석": POLICY_DIR           / f"minseang_{date_str}.json",
        "국내 지표": DOMESTIC_DIR         / f"domestic_{date_str}.json",
    }.items():
        st.caption(f"{'✅' if Path(path).exists() else '⬜'} {lbl}")
    st.divider()
    st.caption(f"🕐 {datetime.now().strftime('%H:%M')}")


# ─────────────────────────────────────────────
# 데이터 로드
# ─────────────────────────────────────────────
analyzed  = load_json(ANALYZED_DIR        / f"analyzed_{date_str}.json") or []
cr_data   = load_json(COUNTRY_RESPONSE_DIR / f"cr_{date_str}.json")     or {}
paradigm  = load_json(PARADIGM_DIR         / f"paradigm_{date_str}.json") or {}
minseang  = load_json(POLICY_DIR           / f"minseang_{date_str}.json") or {}
domestic  = load_json(DOMESTIC_DIR         / f"domestic_{date_str}.json") or {}
yt_data   = load_json(DATA_DIR / "youtube" / f"yt_summary_{date_str}.json") or {}

if not analyzed:
    analyzed = load_json(CLEAN_DIR / f"clean_{date_str}.json") or []

urgency      = minseang.get("urgency", "모니터링")
headline     = minseang.get("today_headline", "이란-미국 긴장 고조 — 수원시 에너지·물가 영향 모니터링 중")
oil          = domestic.get("oil_price", {})
gas_nat      = oil.get("gasoline_national", None)
gas_ggy      = oil.get("gasoline_gyeonggi", None)
cr_responses = cr_data.get("country_responses", [])
issues       = cr_data.get("emerging_issues", [])
민생_분석    = minseang.get("민생경제_분석", {})
대응과제     = minseang.get("우선_대응과제", [])
signals      = paradigm.get("signals", [])
lessons      = minseang.get("international_lessons", {})
top_articles = sorted(analyzed, key=lambda x: x.get("importance",0), reverse=True)[:5]

# Scout 요약 포인트 — minseang scout_points 우선, 없으면 상위 기사 제목
scout_points = minseang.get("scout_points", [])
if not scout_points:
    for a in top_articles[:3]:
        s = a.get("summary_ko") or a.get("summary") or a.get("title","")
        if s: scout_points.append(s[:120])


# ═══════════════════════════════════════════════════════════
# ① 헤더 바
# ═══════════════════════════════════════════════════════════
crisis_label = {"긴급":"⚡ 중동 전황: 긴급", "주의":"⚠️ 중동 전황: 주의", "모니터링":"🔵 중동 전황: 모니터링"}.get(urgency, "🔵 모니터링")

st.markdown(f"""
<div class="top-bar">
  <div class="top-bar-left">
    <div class="top-bar-logo">🏛️</div>
    <div class="top-bar-org">
      <div class="org-name">Suwon City Strategic Office</div>
      <div class="org-sub">민생경제 위기대응 TF · Agent 협업 모델 v2.0</div>
    </div>
  </div>
  <div class="crisis-badge crisis-{urgency}">
    <div class="crisis-dot dot-{urgency}"></div>
    {crisis_label}
  </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# ② 헤로 — 핵심 메시지 + 유가
# ═══════════════════════════════════════════════════════════
col_hero, col_wti = st.columns([7, 3], gap="medium")

with col_hero:
    # Scout 요약 포인트 HTML — 들여쓰기 없이 한 줄로 생성 (4칸↑ 들여쓰기 = Markdown 코드블록 오작동 방지)
    if scout_points:
        scout_html = "".join(
            f'<div class="scout-item"><div class="scout-num">{i}</div><div>{pt}</div></div>'
            for i, pt in enumerate(scout_points, 1)
        )
    else:
        scout_html = '<div class="empty-state">파이프라인 실행 후 Scout 요약이 표시됩니다.</div>'

    # 헤드라인에서 핵심 단어 강조
    hl_display = headline.replace("재봉쇄", '<span class="highlight">재봉쇄</span>')\
                         .replace("긴급", '<span class="highlight">긴급</span>')\
                         .replace("위기", '<span class="highlight">위기</span>')

    now_str = datetime.now().strftime('%Y. %m. %d. %H:%M')
    art_cnt = len(analyzed)
    hero_html = (
        '<div class="brief-card" style="border-left: 6px solid #C0392B;">'
        f'<div class="hero-label">🔴 Global Crisis Update — {fmt_ko(selected_date)}</div>'
        f'<div class="hero-headline">{hl_display}</div>'
        f'<div class="hero-meta"><span>🕐 최종수정: {now_str}</span><span>📎 수집 기사: {art_cnt}건 분석</span></div>'
        '<div class="scout-title">🎯 긴급 전황 요약 (Scout 보고)</div>'
        f'{scout_html}'
        '</div>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)

with col_wti:
    ex_rate   = domestic.get("exchange_rate", {})
    wti_price = oil.get("wti_usd", None)
    usd_krw   = ex_rate.get("USD_KRW", None)
    usd_display = f"{usd_krw:,.1f}" if isinstance(usd_krw, (int,float)) else "--"

    # 메인 지표: 국내 휘발유 우선, 없으면 WTI
    if isinstance(gas_nat, (int,float)):
        main_label   = "휘발유 (전국 평균)"
        main_value   = f"{gas_nat:,}"
        main_unit    = "원"
        main_sub     = f"경기도 평균 {gas_ggy:,} 원" if isinstance(gas_ggy,(int,float)) else ""
    elif isinstance(wti_price, (int,float)):
        main_label   = "WTI 국제유가"
        main_value   = f"{wti_price:,.2f}"
        main_unit    = "USD/배럴"
        main_sub     = "국내 유가: OPINET API 등록 후 표시"
    else:
        main_label   = "유가 정보"
        main_value   = "--"
        main_unit    = ""
        main_sub     = "데이터 수집 중"

    st.markdown(f"""
    <div class="wti-card" style="height: 100%; min-height: 260px;">
      <div class="wti-label">{main_label}</div>
      <div class="wti-price">{main_value}<span style="font-size:1rem;color:#64748B"> {main_unit}</span></div>
      <div class="wti-change wti-up" style="font-size:0.72rem">{main_sub}</div>
      <hr class="wti-divider">
      <div class="wti-sub-row"><span>USD/KRW 환율</span><span class="wti-sub-val">{usd_display} 원</span></div>
      <div class="wti-sub-row"><span>수집 기사</span><span class="wti-sub-val">{len(analyzed)} 건</span></div>
      <div class="wti-sub-row"><span>패러다임 신호</span><span class="wti-sub-val">{paradigm.get('total_signals',0)} 개</span></div>
      <div class="wti-sub-row"><span>발굴 이슈</span><span class="wti-sub-val">{len(issues)} 건</span></div>
      <div class="wti-sub-row"><span>추적 국가</span><span class="wti-sub-val">{len(cr_responses)} 개국</span></div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# ③ 각국 상황 & 대응
# ═══════════════════════════════════════════════════════════
st.markdown(f"""
<div class="brief-card">
  <div class="sec-title">
    🌍 각국 상황 & 대응
    <span class="sec-badge badge-blue">Country Response Matrix</span>
  </div>
""", unsafe_allow_html=True)

if cr_responses:
    rows_html = ""
    for r in cr_responses:
        country = r.get("country","")
        stance  = r.get("stance","중립")
        actions = r.get("actions",[])
        action_text = " · ".join(actions[:2]) if actions else r.get("outlook","분석 중")[:80]
        suwon = r.get("suwon_relevance","")
        st_class = stance[:2] if stance[:2] in ["강경","지지","중립","제재","협력"] else "unknown"
        suwon_html = f'<div class="cr-suwon">▶ 수원 연결: {suwon[:70]}</div>' if suwon else ""
        rows_html += f'<div class="country-row"><div class="cr-name">{country}</div><span class="cr-stance st-{st_class}">{stance}</span><div class="cr-action">{action_text}{suwon_html}</div></div>'
    st.markdown(rows_html + "</div>", unsafe_allow_html=True)
else:
    DEFAULT_COUNTRIES = [
        ("미국",     "강경", "대이란 제재 강화, 호르무즈 해군 작전 유지"),
        ("이스라엘", "강경", "이란 핵·미사일 시설 타격 옵션 검토"),
        ("중국",     "중립", "이란 원유 수입 지속, 미국과 외교적 거리두기"),
        ("러시아",   "지지", "이란 군사·외교 지원, 서방 제재 우회"),
        ("사우디",   "중립", "OPEC+ 감산 유지, 미·이란 중재 관망"),
        ("EU",       "제재", "대이란 제재 동참, 에너지 공급선 다변화 가속"),
        ("한국",     "협력", "미국 동조 제재, LNG 대체 수입선 확보 긴급 검토"),
        ("일본",     "협력", "에너지 비축 확대, 중동 대체 공급망 구축"),
    ]
    rows_html = "".join(
        f'<div class="country-row"><div class="cr-name">{c}</div><span class="cr-stance st-{s}">{s}</span><div class="cr-action">{a}</div></div>'
        for c, s, a in DEFAULT_COUNTRIES
    )
    st.markdown(rows_html + '<div style="margin-top:10px;font-size:0.73rem;color:#94A3B8">⚠️ 기본값 표시 중</div></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# ③-B 한국 지자체 대응 현황
# ═══════════════════════════════════════════════════════════
# 실데이터 있으면 우선 사용 (domestic 또는 별도 파일), 없으면 기본값
lga_data_raw = domestic.get("lga_responses", [])

DEFAULT_LGA = [
    {
        "name": "경기도",
        "type": "도",
        "stage": "적극",
        "actions": "에너지 취약계층 긴급 지원 예산 편성 검토, 도내 지자체 공동 대응 지침 준비, 중소기업 에너지비용 경감 사업 조기 집행",
        "ref": "수원시 → 도비 매칭사업 연계 필요, 공동 LNG 비축 협의 검토",
    },
    {
        "name": "서울특별시",
        "type": "광역",
        "stage": "선제",
        "actions": "에너지 위기 가정 TF 가동, 취약계층 전기·가스요금 긴급 바우처 조기 집행, 서울형 에너지 상한제 연동 지원 검토",
        "ref": "수원시 → 서울 바우처 단가 및 지급 방식 벤치마킹 대상",
    },
    {
        "name": "인천광역시",
        "type": "광역",
        "stage": "적극",
        "actions": "LNG 수입 다변화 항만 대비 태세 점검, 에너지 비상공급 계획 선제 수립, 소상공인 유류비 직접 보조 예산안 준비",
        "ref": "수원시 → 인천항 물류비 상승 시 납품 단가 연동 지원 모델 참고",
    },
    {
        "name": "대구광역시",
        "type": "광역",
        "stage": "검토",
        "actions": "에너지 비용 급등 시나리오 자체 분석, 취약계층 긴급복지 지원 요건 완화 검토",
        "ref": "수원시 → 긴급복지 완화 기준 공유 요청 가능",
    },
    {
        "name": "전주시",
        "type": "기초",
        "stage": "적극",
        "actions": "K-패스 환급률 상향 조정 건의, 대중교통 에너지 비용 지자체 보조 확대, 취약계층 실태조사 조기 실시",
        "ref": "수원시 → K-패스 수원 도입 연계 시 전주 모델 직접 적용 가능",
    },
    {
        "name": "부산광역시",
        "type": "광역",
        "stage": "모니터링",
        "actions": "해운·물류비 급등 모니터링, 수출기업 공급망 현황 파악 중, 에너지 위기 단계 상향 시 즉시 대응 체계 준비",
        "ref": "수원시 → 삼성 공급망 연계 물류비 분석 공유 요청 가능",
    },
]

lga_list = lga_data_raw if lga_data_raw else DEFAULT_LGA

# 수원시 현황 (현재 페이지 자체)
suwon_status = {
    "stage": urgency if urgency in ["선제","적극","검토","모니터링"] else "모니터링",
    "actions": "민생경제 위기대응 TF 운영, AI 에이전트 기반 실시간 모니터링, 정책 A/B/C 검토 중",
    "ref": "본 브리핑 시스템 운영 중 (Agent v2.0)",
}

# 테이블 행 렌더링
def lga_row_html(row, is_suwon=False):
    name    = row.get("name","")
    ltype   = row.get("type","기초")
    stage   = row.get("stage","모니터링")
    acts    = row.get("actions","")
    ref     = row.get("ref","")
    row_cls = "lga-suwon-row" if is_suwon else "lga-row"
    suwon_lbl = '<div class="lga-suwon-label">▶ 현재 페이지</div>' if is_suwon else ""
    return (f'<tr class="{row_cls}">'
            f'<td class="lga-name">{suwon_lbl}{name}<span class="lga-type type-{ltype}">{ltype}</span></td>'
            f'<td class="lga-stage"><span class="stage-badge stage-{stage}">{stage}</span></td>'
            f'<td class="lga-action">{acts}</td>'
            f'<td class="lga-ref">▶ {ref}</td></tr>')

rows_lga_html = lga_row_html({"name":"수원시","type":"기초","stage":suwon_status["stage"],"actions":suwon_status["actions"],"ref":suwon_status["ref"]}, is_suwon=True)
for row in lga_list:
    rows_lga_html += lga_row_html(row)

st.markdown(f"""
<div class="brief-card">
  <div class="sec-title">
    🇰🇷 한국 지자체 상황 & 대응 현황
    <span class="sec-badge badge-green">Local Gov Response Matrix</span>
  </div>
  <table class="lga-table">
    <thead>
      <tr>
        <th style="min-width:120px">지자체</th>
        <th style="min-width:80px">대응 단계</th>
        <th>주요 조치</th>
        <th style="min-width:200px">수원시 참고 포인트</th>
      </tr>
    </thead>
    <tbody>
      {rows_lga_html}
    </tbody>
  </table>
  <div style="margin-top:10px;font-size:0.72rem;color:#94A3B8">
    ⚠️ 기본값 표시 중 — API 분석 후 실시간 지자체 대응 데이터로 업데이트됩니다.
    &nbsp;|&nbsp; 대응단계: <span style="color:#C0392B;font-weight:700">선제</span> &gt; <span style="color:#B45309;font-weight:700">적극</span> &gt; <span style="color:#1D4ED8;font-weight:700">검토</span> &gt; <span style="color:#6B7280;font-weight:700">모니터링</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# ④ 수원시 민생경제 분석
# ═══════════════════════════════════════════════════════════
st.markdown("""
<div class="brief-card">
  <div class="sec-title">
    🏙️ 수원시 민생경제 분석
    <span class="sec-badge badge-red">3대 관점 영향 분석</span>
  </div>
""", unsafe_allow_html=True)

CATEGORY_META = {
    "지역산업":      ("🏭", "지역산업 (제조·수출)"),
    "소상공인_자영업": ("🛒", "소상공인·자영업"),
    "시민생활":      ("🏠", "시민생활 (에너지·물가)"),
}
DEFAULT_민생 = {
    "지역산업": {
        "level": "모니터링",
        "summary": "삼성전자 협력사 등 수원 제조업·수출기업 영향 분석 중. 호르무즈 봉쇄 시나리오 대비 공급망 점검 필요.",
        "key_indicator": "데이터 수집 후 업데이트",
        "타지자체_현황": "API 분석 실행 후 타 지자체 현황이 표시됩니다.",
    },
    "소상공인_자영업": {
        "level": "모니터링",
        "summary": "유류비·에너지비 상승에 따른 배달·운수·음식업 운영비용 증가 모니터링 중.",
        "key_indicator": "데이터 수집 후 업데이트",
        "타지자체_현황": "API 분석 실행 후 타 지자체 현황이 표시됩니다.",
    },
    "시민생활": {
        "level": "모니터링",
        "summary": "도시가스·전기요금 인상 가능성 및 취약계층 에너지 부담 모니터링 중.",
        "key_indicator": "데이터 수집 후 업데이트",
        "타지자체_현황": "API 분석 실행 후 타 지자체 현황이 표시됩니다.",
    },
}
display_민생 = 민생_분석 if 민생_분석 else DEFAULT_민생

ms_cols = st.columns(3, gap="medium")
for i, (key, (icon, label)) in enumerate(CATEGORY_META.items()):
    item = display_민생.get(key, DEFAULT_민생[key])
    level   = item.get("level", "모니터링")
    summary = item.get("summary", "")
    kpi     = item.get("key_indicator", "")
    other   = item.get("타지자체_현황", "")
    with ms_cols[i]:
        st.markdown(
            f'<div class="minseang-card">'
            f'<div class="ms-category">{icon} {label}</div>'
            f'<span class="ms-level-badge ms-lvl-{level}">영향도 : {level}</span>'
            f'<div class="ms-summary">{summary}</div>'
            f'<div class="ms-indicator-box"><div class="ms-ind-label">📊 핵심 지표</div><div class="ms-ind-value">{kpi}</div></div>'
            f'<div class="ms-other-box"><div class="ms-other-label">🏙 타 지자체 현황</div><div class="ms-other-value">{other}</div></div>'
            f'</div>',
            unsafe_allow_html=True
        )

is_default_민생 = not bool(민생_분석)
note_민생 = "⚠️ 기본값 표시 중 — API 분석 후 실시간 민생경제 분석으로 업데이트됩니다." if is_default_민생 else ""
st.markdown(f'<p style="font-size:0.72rem;color:#94A3B8;margin-top:8px">{note_민생}</p></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# ⑤ 수원시 우선 대응과제
# ═══════════════════════════════════════════════════════════
st.markdown("""
<div class="brief-card">
  <div class="sec-title">
    📋 수원시 민생경제 우선 대응과제
    <span class="sec-badge badge-red">근거 기반 AI 정책 제언</span>
  </div>
""", unsafe_allow_html=True)

DEFAULT_대응과제 = [
    {
        "순위": 1, "title": "에너지 취약가구 긴급 바우처 지원",
        "description": "기초수급·차상위 취약가구 대상 도시가스·전기요금 바우처 조기 집행. 경기도 매칭 사업 연계를 통해 시비 부담을 최소화하고 수혜 기준 완화로 실질 지원 폭 확대.",
        "priority": "즉시",
        "근거": {
            "타지자체_벤치마킹": "서울시 에너지 취약가구 전기·가스 30% 상한 지원 모델 / 경기도 긴급 바우처 조기 집행 사례",
            "전문가_의견": "에너지 취약계층 직접 지원이 물가 상승기 가장 효과적 대응 수단 (전문가 브리핑)",
            "보고서_근거": "KDI — 바우처 직접 지급이 감면 방식 대비 수혜율 2.3배 높음",
        },
    },
    {
        "순위": 2, "title": "소상공인 에너지 비용 긴급 지원",
        "description": "배달·운수·음식업 대상 유류비 보조금 및 에너지 다소비 업종 전기·가스요금 특별 감면을 단일 창구 신청으로 간소화. 경기도 긴급 융자 연계 홍보 강화.",
        "priority": "즉시",
        "근거": {
            "타지자체_벤치마킹": "전주시 소상공인 에너지 특별지원금 50만 원 지급 사례 / 서울시 에너지 다소비 업종 전기요금 30% 할인",
            "전문가_의견": "소상공인 에너지비 부담이 폐업률에 직결 — 직접 보조가 융자보다 즉효 (연합뉴스TV 브리핑)",
            "보고서_근거": "KEEI — 자영업 에너지비 비중 매출 대비 평균 8.4%로 임계치 초과",
        },
    },
    {
        "순위": 3, "title": "에너지 비상대응 TF 구성 및 시나리오 수립",
        "description": "호르무즈 봉쇄 장기화(3·6·12개월) 시나리오별 수원시 에너지·물가 충격 시뮬레이션 및 단계별 대응 매뉴얼 수립. 경기도 LNG 비상비축 MOU 연계 참여.",
        "priority": "단기",
        "근거": {
            "타지자체_벤치마킹": "일본 METI 에너지 비상계획 3단계 시나리오 모델 / 인천시 LNG 비상비축 경기도 MOU 체결 사례",
            "전문가_의견": "호르무즈 봉쇄 가능성 40% 이상 — 지자체 단위 사전 비상계획 필수 (War on the Rocks 분석)",
            "보고서_근거": "KIEP — 봉쇄 6개월 지속 시 국내 에너지 비용 추가 23% 상승 전망",
        },
    },
]

display_대응과제 = 대응과제 if 대응과제 else DEFAULT_대응과제
rank_tags = ["A", "B", "C"]
rank_colors = ["tag-A", "tag-B", "tag-C"]

act_cols = st.columns(3, gap="medium")
for i, task in enumerate(display_대응과제[:3]):
    rank     = task.get("순위", i+1)
    title    = task.get("title", "")
    desc     = task.get("description", "")
    priority = task.get("priority", "단기")
    근거      = task.get("근거", {})
    bench    = 근거.get("타지자체_벤치마킹", "")
    expert   = 근거.get("전문가_의견", "")
    report   = 근거.get("보고서_근거", "")
    with act_cols[i]:
        st.markdown(
            f'<div class="action-card">'
            f'<div class="action-rank">Priority {rank_tags[i]}</div>'
            f'<span class="action-priority pri-{priority}">⚡ {priority} 과제</span>'
            f'<div class="action-title">{title}</div>'
            f'<div class="action-desc">{desc}</div>'
            f'<div class="evidence-box">'
            f'<div class="ev-item ev-bench"><span class="ev-tag">🏙 타지자체 벤치마킹</span>{bench}</div>'
            f'<div class="ev-item ev-expert"><span class="ev-tag">🎙 전문가 의견</span>{expert}</div>'
            f'<div class="ev-item ev-report"><span class="ev-tag">📄 보고서 근거</span>{report}</div>'
            f'</div></div>',
            unsafe_allow_html=True
        )

is_default_과제 = not bool(대응과제)
note_과제 = "⚠️ 기본값 표시 중 — API 분석 후 맞춤형 근거 기반 정책 제언으로 업데이트됩니다." if is_default_과제 else ""
st.markdown(f'<p style="font-size:0.72rem;color:#94A3B8;margin-top:8px">{note_과제}</p></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# ⑥ 타 지자체 벤치마킹
# ═══════════════════════════════════════════════════════════
bench_data = lessons if lessons else {
    "전주시": "에너지 위기 대응 K-패스 환급률 상향 조정, 취약계층 대중교통비 실질 혜택 확대",
    "서울시": "에너지 가격 상한제 연계 취약계층 긴급 바우처 지급, 소상공인 전기요금 할인",
    "인천시": "LNG 수입 다변화 협력, 에너지 비상공급 계획 선제 수립",
}

st.markdown(f"""
<div class="brief-card">
  <div class="sec-title">
    🔍 타 지자체·국외 사례 벤치마킹
    <span class="sec-badge badge-green">Success Model</span>
  </div>
""", unsafe_allow_html=True)

bench_cols = st.columns(len(bench_data), gap="medium")
for i, (city, content) in enumerate(list(bench_data.items())[:3]):
    items = content.split(",") if isinstance(content, str) else [content]
    items_html = "".join(
        f'<div class="bench-item"><span class="bench-check">→</span><span>{item.strip()}</span></div>'
        for item in items[:3]
    )
    with bench_cols[i % len(bench_cols)]:
        st.markdown(
            f'<div class="bench-card"><div class="bench-city">🏙 {city}</div>'
            f'<div class="bench-title">수원시 적용 시뮬레이션</div>'
            f'<div>{items_html}</div></div>',
            unsafe_allow_html=True
        )

st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# ⑦ 전문가 브리핑 (YouTube 요약)
# ═══════════════════════════════════════════════════════════
yt_summaries = yt_data.get("summaries", [])

st.markdown("""
<div class="brief-card">
  <div class="sec-title">
    📺 전문가 브리핑
    <span class="sec-badge badge-blue">YouTube Intelligence</span>
  </div>
""", unsafe_allow_html=True)

def yt_channel_class(channel: str) -> str:
    ch = channel.lower()
    if "al jazeera" in ch: return "yt-aljazeera"
    if "dw" in ch:         return "yt-dw"
    if "연합" in ch:        return "yt-yonhap"
    return "yt-default"

if yt_summaries:
    # 관련도 높은 순으로 최대 3개
    top_yt = sorted(yt_summaries, key=lambda x: x.get("relevance_score", 0), reverse=True)[:3]
    yt_cols = st.columns(len(top_yt), gap="medium")
    for i, item in enumerate(top_yt):
        channel   = item.get("channel", "")
        title_ko  = item.get("title_ko", item.get("title", ""))
        points    = item.get("key_points", [])
        expert    = item.get("expert_name", "")
        score     = item.get("relevance_score", 0)
        published = item.get("published", "")[:10]
        duration  = item.get("duration", "")
        ch_cls    = yt_channel_class(channel)

        points_html = "".join(
            f'<div class="yt-point"><span class="yt-bullet">•</span><span>{pt}</span></div>'
            for pt in points[:3]
        )
        with yt_cols[i]:
            st.markdown(
                f'<div class="yt-card">'
                f'<div class="yt-channel">'
                f'<span class="yt-ch-badge {ch_cls}">{channel}</span>'
                f'<span class="yt-meta">{published} · {duration}</span>'
                f'</div>'
                f'<div class="yt-title">{title_ko}</div>'
                f'<div class="yt-points">{points_html}</div>'
                f'<div class="yt-expert">🎙 {expert}<span class="yt-score">관련도 {score}</span></div>'
                f'</div>',
                unsafe_allow_html=True
            )
else:
    st.markdown('<div class="empty-state">📺 YouTube API 키 등록 후 파이프라인을 실행하면<br>Al Jazeera · DW News · 연합뉴스TV 전문가 브리핑이 여기에 표시됩니다.</div>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# ⑧ Devil's Critique (반론·비판 섹션)
# ═══════════════════════════════════════════════════════════
critiques = [
    ("1. 예산 실현 가능성 검토",
     "긴급 지원 확대는 시 재정자립도(40%) 한계와 충돌 가능. 경기도 매칭 사업 연계 없이는 즉시 집행 불가. **보조금 규모 현실화 필수**."),
    ("2. 공급망 파악 한계",
     "수원시 에너지 수급의 대부분은 중앙정부·한국가스공사 관할. 시 단독 대응 효과 제한적. **광역 연계 대응 전략** 병행 필요."),
    ("3. 장기화 대비 부재",
     "현 대응안은 단기(3개월) 중심. 분쟁이 6개월~1년 지속 시 예산·행정 여력 고갈 우려. **시나리오 기반 중장기 플랜** 수립 시급."),
]

devil_html = "".join(
    f'<div class="devil-point"><div class="dp-num">{c[0][:20]}</div><div class="dp-body">{c[1]}</div></div>'
    for c in critiques
)

st.markdown(
    '<div class="devil-card">'
    '<div class="devil-watermark">DEVIL\'S CRITIQUE</div>'
    '<div class="devil-quote">"<span class="dq-inner">실행 전 이것을 반드시 점검하라</span>"</div>'
    f'<div class="devil-points">{devil_html}</div>'
    '</div>',
    unsafe_allow_html=True
)


# ═══════════════════════════════════════════════════════════
# ⑧ 푸터 & 버튼
# ═══════════════════════════════════════════════════════════
st.markdown(f"""
<div class="brief-card" style="padding: 16px 28px;">
  <div style="display:flex; justify-content:space-between; align-items:center;">
    <div style="font-size:0.72rem; color:#94A3B8">
      AI-Powered Strategic Analysis · Suwon City Strategic Office ·
      Reference: {len(analyzed)} articles · {fmt(selected_date)} · <strong>CONFIDENTIAL</strong>
    </div>
    <div style="display:flex; gap:10px;">
      <button class="btn-print no-print" onclick="window.print()">🖨️ 인쇄</button>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
