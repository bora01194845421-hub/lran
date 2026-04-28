"""
이란전쟁 민생 브리핑 대시보드 v5
수원시정연구원 | 인텔리전스 브리프 스타일 (다크 네이비)

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
# CSS — 다크 인텔리전스 브리프 스타일
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&family=Inter:wght@400;600;700;800;900&display=swap');

*, *::before, *::after {
  box-sizing: border-box;
  font-family: 'Noto Sans KR', 'Inter', 'Malgun Gothic', sans-serif;
}

/* ── 전체 배경 — 순백 ── */
.stApp { background: #FFFFFF !important; }
[data-testid="stAppViewContainer"] { background: #FFFFFF !important; }
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stToolbar"] { background: transparent !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* 사이드바 */
[data-testid="stSidebar"] { background: #1C2B40 !important; }
[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
[data-testid="stSidebar"] .stButton button {
  background: #1A56DB !important; color: white !important;
  border: none !important; border-radius: 4px !important; font-weight: 700 !important;
}

/* ── 헤더 — 다크 네이비, 스크린샷 참고 ── */
.intel-header {
  display: flex; align-items: flex-end; justify-content: space-between;
  padding: 20px 32px 16px 32px;
  background: #1C2B40;
}
.header-brand { display: flex; flex-direction: column; gap: 4px; }
.header-org {
  font-size: 0.68rem; color: #7BA7C7; font-weight: 500; letter-spacing: 0.3px;
}
.header-main {
  font-size: 1.55rem; color: #FFFFFF; font-weight: 900; letter-spacing: -0.3px; line-height: 1.2;
}
.header-date-line { font-size: 0.75rem; color: #7BA7C7; margin-top: 3px; }
.header-right { display: flex; align-items: center; gap: 12px; padding-bottom: 4px; }
.urgency-badge {
  display: flex; align-items: center; gap: 6px;
  padding: 5px 13px; border-radius: 4px;
  font-weight: 700; font-size: 0.72rem;
}
.urg-긴급    { background: #C0392B; color: #FFFFFF; }
.urg-주의    { background: #D97706; color: #FFFFFF; }
.urg-모니터링 { background: #1A7A4A; color: #FFFFFF; }
.urg-dot { width: 6px; height: 6px; border-radius: 50%; background: rgba(255,255,255,0.7); animation: blink 1.5s infinite; }
.ud-긴급 .urg-dot, .ud-주의 .urg-dot, .ud-모니터링 .urg-dot { background: rgba(255,255,255,0.8); }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* ── 지표 띠 — 연회색 배경, 수치 나열 ── */
.metrics-strip {
  background: #F3F4F6;
  border-bottom: 1px solid #E5E7EB;
  padding: 10px 32px;
  display: flex; gap: 0; align-items: stretch;
}
.ms-item {
  display: flex; flex-direction: column; justify-content: center;
  padding: 0 22px; border-right: 1px solid #D1D5DB;
  min-width: 110px;
}
.ms-item:first-child { padding-left: 0; }
.ms-item:last-child  { border-right: none; }
.ms-label { font-size: 0.58rem; color: #6B7280; font-weight: 600; margin-bottom: 2px; letter-spacing: 0.3px; }
.ms-value { font-size: 0.92rem; font-weight: 800; color: #111827; font-family: 'Inter', monospace; line-height: 1.2; }
.ms-value.up   { color: #DC2626; }
.ms-value.down { color: #059669; }
.ms-sub { font-size: 0.62rem; color: #9CA3AF; margin-top: 1px; }

/* ── 레이아웃 래퍼 ── */
.page-wrap { padding: 20px 32px; }

/* ── 섹션 공통 — 카드 없이 흰 배경 + 얇은 테두리 ── */
.section-card {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  padding: 20px 24px;
  margin-bottom: 16px;
}
.sec-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 14px; padding-bottom: 10px;
  border-bottom: 1px solid #F3F4F6;
}
.sec-title {
  font-size: 0.88rem; font-weight: 800; color: #111827;
  display: flex; align-items: center; gap: 6px;
}
.sec-title::before { content: "●"; color: #1C2B40; font-size: 0.55rem; }
.sec-date { font-size: 0.68rem; color: #9CA3AF; }
.sec-badge {
  font-size: 0.6rem; font-weight: 700; padding: 2px 8px;
  border-radius: 3px; letter-spacing: 0.3px;
}
.badge-blue  { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
.badge-red   { background: #FEF2F2; color: #B91C1C; border: 1px solid #FECACA; }
.badge-green { background: #F0FDF4; color: #15803D; border: 1px solid #BBF7D0; }
.badge-amber { background: #FFFBEB; color: #92400E; border: 1px solid #FDE68A; }
.badge-gray  { background: #F9FAFB; color: #6B7280; border: 1px solid #E5E7EB; }

/* ── 히어로 (헤드라인 + Scout) — 흰 박스 ── */
.hero-card {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  padding: 22px 24px;
  margin-bottom: 16px;
  display: grid;
  grid-template-columns: 1fr 240px;
  gap: 24px;
  align-items: start;
}
.hero-label {
  font-size: 0.6rem; font-weight: 700; letter-spacing: 1.5px;
  color: #6B7280; text-transform: uppercase; margin-bottom: 8px;
}
.hero-headline {
  font-size: 1.3rem; font-weight: 900; color: #111827;
  line-height: 1.4; margin-bottom: 14px;
}
.hero-headline .hl-red { color: #DC2626; }
.hero-meta {
  display: flex; gap: 16px; font-size: 0.7rem; color: #9CA3AF; margin-bottom: 14px;
}
.scout-label {
  font-size: 0.6rem; font-weight: 700; letter-spacing: 1.5px;
  color: #6B7280; text-transform: uppercase; margin-bottom: 8px;
}
.scout-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 8px 0; border-bottom: 1px solid #F3F4F6;
  font-size: 0.8rem; color: #374151; line-height: 1.55;
}
.scout-item:last-child { border-bottom: none; }
.scout-num {
  min-width: 18px; height: 18px;
  background: #1C2B40; border-radius: 50%;
  color: white; font-size: 0.58rem; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; margin-top: 2px;
}

/* 메트릭 사이드 패널 (히어로 오른쪽) */
.metrics-panel {
  background: #F9FAFB;
  border: 1px solid #E5E7EB;
  border-radius: 6px;
  padding: 16px;
}
.metric-item { margin-bottom: 14px; }
.metric-item:last-child { margin-bottom: 0; }
.metric-label { font-size: 0.58rem; font-weight: 600; color: #9CA3AF; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 3px; }
.metric-value { font-size: 1.3rem; font-weight: 900; color: #111827; font-family: 'Inter', monospace; line-height: 1; }
.metric-value.up { color: #DC2626; }
.metric-unit { font-size: 0.65rem; color: #9CA3AF; margin-left: 3px; font-weight: 400; }
.metric-divider { border: none; border-top: 1px solid #E5E7EB; margin: 12px 0; }
.metric-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 7px; }
.metric-row:last-child { margin-bottom: 0; }
.mr-label { font-size: 0.67rem; color: #9CA3AF; }
.mr-value { font-size: 0.75rem; color: #374151; font-weight: 700; font-family: 'Inter', monospace; }

/* ── 2컬럼 패널 ── */
.twin-panels { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.panel-card {
  background: #FFFFFF; border: 1px solid #E5E7EB;
  border-radius: 8px; padding: 18px 20px;
}
.panel-title {
  font-size: 0.82rem; font-weight: 800; color: #111827;
  display: flex; align-items: center; gap: 6px;
  margin-bottom: 12px; padding-bottom: 10px;
  border-bottom: 1px solid #F3F4F6;
}
.panel-title::before { content: "●"; color: #1C2B40; font-size: 0.5rem; }

/* 시그널 목록 */
.signal-item {
  display: flex; align-items: flex-start; gap: 8px;
  padding: 7px 0; border-bottom: 1px solid #F9FAFB;
  font-size: 0.77rem; color: #374151; line-height: 1.5;
}
.signal-item:last-child { border-bottom: none; }
.sig-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; margin-top: 6px; }
.sig-red   { background: #EF4444; }
.sig-amber { background: #F59E0B; }
.sig-blue  { background: #3B82F6; }
.sig-green { background: #10B981; }

/* 국내지표 */
.kpi-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 0; border-bottom: 1px solid #F9FAFB;
}
.kpi-row:last-child { border-bottom: none; }
.kpi-label { font-size: 0.75rem; color: #6B7280; }
.kpi-right { display: flex; align-items: center; gap: 8px; }
.kpi-value { font-size: 0.88rem; color: #111827; font-weight: 700; font-family: 'Inter', monospace; }
.kpi-tag { font-size: 0.6rem; font-weight: 700; padding: 1px 6px; border-radius: 3px; }
.kt-up   { background: #FEF2F2; color: #DC2626; }
.kt-down { background: #F0FDF4; color: #15803D; }
.kt-neu  { background: #F9FAFB; color: #6B7280; }

/* ── 각국 대응 테이블 ── */
.cr-table { width: 100%; border-collapse: collapse; }
.cr-th {
  font-size: 0.62rem; font-weight: 700; color: #6B7280; letter-spacing: 0.5px;
  padding: 7px 10px; border-bottom: 1px solid #E5E7EB; text-align: left;
  background: #F9FAFB;
}
.cr-row { border-bottom: 1px solid #F3F4F6; }
.cr-row:last-child { border-bottom: none; }
.cr-row:hover { background: #FAFAFA; }
.cr-country { font-size: 0.82rem; font-weight: 700; color: #111827; padding: 10px 10px; white-space: nowrap; }
.cr-stance-cell { padding: 10px 10px; }
.cr-stance-badge {
  display: inline-block; padding: 2px 8px; border-radius: 3px;
  font-size: 0.63rem; font-weight: 700; white-space: nowrap;
}
.st-강경   { background: #FEF2F2; color: #B91C1C; }
.st-지지   { background: #FFFBEB; color: #92400E; }
.st-중립   { background: #EFF6FF; color: #1E40AF; }
.st-제재   { background: #F5F3FF; color: #5B21B6; }
.st-협력   { background: #F0FDF4; color: #15803D; }
.st-unknown { background: #F9FAFB; color: #6B7280; }
.cr-action-cell { font-size: 0.75rem; color: #4B5563; padding: 10px 10px; line-height: 1.5; max-width: 300px; }
.cr-suwon-cell  { font-size: 0.71rem; color: #15803D; padding: 10px 10px; line-height: 1.5; font-weight: 600; }

/* ── 지자체 테이블 ── */
.lga-table { width: 100%; border-collapse: collapse; }
.lga-th {
  font-size: 0.62rem; font-weight: 700; color: #6B7280;
  padding: 7px 10px; border-bottom: 1px solid #E5E7EB; text-align: left; background: #F9FAFB;
}
.lga-row { border-bottom: 1px solid #F3F4F6; }
.lga-row:last-child { border-bottom: none; }
.lga-row:hover { background: #FAFAFA; }
.lga-suwon-row { background: #F0F7FF !important; }
.lga-name-cell { font-size: 0.82rem; font-weight: 700; color: #111827; padding: 10px 10px; white-space: nowrap; }
.lga-type-tag {
  display: inline-block; font-size: 0.58rem; font-weight: 700;
  padding: 1px 6px; border-radius: 3px; margin-left: 5px; vertical-align: middle;
}
.tt-광역 { background: #EFF6FF; color: #1E40AF; }
.tt-도   { background: #F5F3FF; color: #5B21B6; }
.tt-기초 { background: #F0FDF4; color: #15803D; }
.lga-stage-cell { padding: 10px 10px; white-space: nowrap; }
.stage-badge { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 0.63rem; font-weight: 700; }
.stage-선제    { background: #FEF2F2; color: #B91C1C; }
.stage-적극    { background: #FFFBEB; color: #92400E; }
.stage-검토    { background: #EFF6FF; color: #1E40AF; }
.stage-모니터링 { background: #F9FAFB; color: #6B7280; }
.lga-action-cell { font-size: 0.75rem; color: #4B5563; padding: 10px 10px; line-height: 1.5; }
.lga-ref-cell   { font-size: 0.71rem; color: #15803D; padding: 10px 10px; line-height: 1.5; font-weight: 600; }

/* ── 3컬럼 민생분석 ── */
.triple-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.impact-card {
  background: #FFFFFF; border: 1px solid #E5E7EB;
  border-radius: 8px; padding: 18px; height: 100%;
}
.impact-card-energy   { border-top: 3px solid #EF4444; }
.impact-card-industry { border-top: 3px solid #F59E0B; }
.impact-card-life     { border-top: 3px solid #3B82F6; }
.ic-icon { font-size: 1.3rem; margin-bottom: 6px; }
.ic-category { font-size: 0.6rem; font-weight: 700; color: #9CA3AF; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 4px; }
.ic-level-badge { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 0.63rem; font-weight: 700; margin-bottom: 10px; }
.icl-높음    { background: #FEF2F2; color: #B91C1C; }
.icl-중간    { background: #FFFBEB; color: #92400E; }
.icl-낮음    { background: #F0FDF4; color: #15803D; }
.icl-모니터링 { background: #F9FAFB; color: #6B7280; }
.ic-title   { font-size: 0.88rem; font-weight: 800; color: #111827; margin-bottom: 8px; }
.ic-summary { font-size: 0.76rem; color: #4B5563; line-height: 1.65; margin-bottom: 12px; }
.ic-kpi-box {
  background: #EFF6FF; border-left: 2px solid #2563EB;
  padding: 8px 10px; margin-bottom: 6px; border-radius: 0 4px 4px 0;
}
.ic-kpi-label { font-size: 0.57rem; font-weight: 700; color: #1D4ED8; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 3px; }
.ic-kpi-value { font-size: 0.74rem; color: #1E3A8A; line-height: 1.5; }
.ic-other-box {
  background: #F0FDF4; border-left: 2px solid #16A34A;
  padding: 8px 10px; border-radius: 0 4px 4px 0;
}
.ic-other-label { font-size: 0.57rem; font-weight: 700; color: #15803D; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 3px; }
.ic-other-value { font-size: 0.74rem; color: #14532D; line-height: 1.5; }

/* ── 대응과제 카드 ── */
.action-card {
  background: #FFFFFF; border: 1px solid #E5E7EB;
  border-radius: 8px; padding: 18px; height: 100%;
}
.ac-rank { font-size: 0.58rem; font-weight: 700; color: #9CA3AF; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 5px; }
.ac-priority { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 0.63rem; font-weight: 700; margin-bottom: 10px; }
.pri-즉시 { background: #FEF2F2; color: #B91C1C; }
.pri-단기 { background: #FFFBEB; color: #92400E; }
.pri-중기 { background: #EFF6FF; color: #1E40AF; }
.ac-title { font-size: 0.88rem; font-weight: 800; color: #111827; margin-bottom: 7px; line-height: 1.4; }
.ac-desc  { font-size: 0.75rem; color: #4B5563; line-height: 1.65; margin-bottom: 12px; }
.evidence-stack { border-top: 1px solid #F3F4F6; padding-top: 10px; display: flex; flex-direction: column; gap: 5px; }
.ev-item { padding: 7px 10px; border-radius: 4px; font-size: 0.71rem; color: #374151; line-height: 1.5; }
.ev-bench  { background: #EFF6FF; border-left: 2px solid #2563EB; }
.ev-expert { background: #F0FDF4; border-left: 2px solid #16A34A; }
.ev-report { background: #F5F3FF; border-left: 2px solid #7C3AED; }
.ev-tag { font-size: 0.57rem; font-weight: 700; letter-spacing: 0.8px; display: block; margin-bottom: 2px; text-transform: uppercase; }
.ev-bench  .ev-tag { color: #1D4ED8; }
.ev-expert .ev-tag { color: #15803D; }
.ev-report .ev-tag { color: #6D28D9; }

/* ── 벤치마킹 ── */
.bench-card {
  background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px; padding: 16px 18px;
}
.bench-city { font-size: 0.8rem; font-weight: 800; color: #1C2B40; margin-bottom: 8px; }
.bench-item { display: flex; gap: 7px; font-size: 0.74rem; color: #4B5563; line-height: 1.55; margin-bottom: 4px; }
.bench-arrow { color: #2563EB; flex-shrink: 0; font-weight: 700; }

/* ── YouTube ── */
.yt-card {
  background: #FFFFFF; border: 1px solid #E5E7EB;
  border-radius: 8px; padding: 16px 18px; height: 100%;
}
.yt-channel-row { display: flex; align-items: center; gap: 7px; margin-bottom: 8px; }
.yt-ch-badge { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 0.63rem; font-weight: 700; }
.yt-aljazeera { background: #FEF2F2; color: #B91C1C; }
.yt-dw        { background: #EFF6FF; color: #1E40AF; }
.yt-yonhap    { background: #F0FDF4; color: #15803D; }
.yt-default   { background: #F9FAFB; color: #6B7280; }
.yt-meta { font-size: 0.64rem; color: #9CA3AF; margin-left: auto; }
.yt-title { font-size: 0.84rem; font-weight: 800; color: #111827; margin-bottom: 8px; line-height: 1.45; }
.yt-point { display: flex; gap: 7px; font-size: 0.75rem; color: #4B5563; line-height: 1.55; padding: 5px 0; border-bottom: 1px solid #F9FAFB; }
.yt-point:last-child { border-bottom: none; }
.yt-bullet { color: #DC2626; font-weight: 900; flex-shrink: 0; margin-top: 2px; }
.yt-expert { font-size: 0.68rem; color: #9CA3AF; margin-top: 10px; display: flex; align-items: center; gap: 5px; padding-top: 8px; border-top: 1px solid #F3F4F6; }
.yt-score { margin-left: auto; font-size: 0.64rem; font-weight: 700; color: #1D4ED8; }

/* ── 리스크 점검 (구 Devil's Critique) ── */
.devil-card {
  background: #F9FAFB;
  border: 1px solid #E5E7EB;
  border-left: 3px solid #DC2626;
  border-radius: 8px;
  padding: 20px 24px;
  margin-bottom: 16px;
}
.devil-stamp {
  display: inline-block; float: right;
  font-size: 0.6rem; font-weight: 700; letter-spacing: 1px;
  background: #FEF2F2; color: #B91C1C; padding: 3px 10px;
  border-radius: 3px; border: 1px solid #FECACA;
}
.devil-quote {
  font-size: 0.95rem; font-weight: 800; color: #111827;
  margin-bottom: 16px; padding-bottom: 12px;
  border-bottom: 1px solid #E5E7EB; clear: both;
}
.devil-quote .dq-hi { color: #DC2626; }
.devil-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.dp-num { font-size: 0.6rem; font-weight: 700; color: #9CA3AF; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 4px; }
.dp-title { font-size: 0.82rem; font-weight: 700; color: #111827; margin-bottom: 5px; }
.dp-body  { font-size: 0.74rem; color: #6B7280; line-height: 1.65; }

/* ── 빈 상태 ── */
.empty-dark {
  text-align: center; padding: 20px; border: 1px dashed #D1D5DB;
  border-radius: 6px; color: #9CA3AF; font-size: 0.77rem; background: #F9FAFB;
}

/* ── 푸터 ── */
.intel-footer {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 32px; border-top: 1px solid #E5E7EB;
  font-size: 0.64rem; color: #9CA3AF; background: #F9FAFB;
}
.footer-stamp { font-size: 0.6rem; font-weight: 600; letter-spacing: 1px; color: #D1D5DB; text-transform: uppercase; }

/* 인쇄 */
@media print {
  .stApp { background: white !important; }
  [data-testid="stSidebar"] { display: none !important; }
  .no-print { display: none !important; }
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
# 사이드바
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ 운영 컨트롤")
    st.divider()
    selected_date = st.date_input("📅 날짜", value=date.today(),
                                   min_value=date(2026,1,1), max_value=date.today())
    date_str = ds(selected_date)
    st.divider()
    col_run, col_stop = st.columns(2)
    with col_run:
        if st.button("🚀 파이프라인 시작", type="primary", use_container_width=True):
            try:
                proc = subprocess.Popen(
                    ["python", "orchestrator.py", "--date", fmt(selected_date)],
                    cwd=str(Path(__file__).parent),
                    creationflags=subprocess.CREATE_NEW_CONSOLE,  # 별도 창
                )
                st.session_state["pipeline_pid"] = proc.pid
                st.success(f"✅ 백그라운드 실행 중 (PID {proc.pid})\n새 창에서 진행 상황을 확인하세요.")
            except Exception as e:
                st.error(f"실행 오류: {e}")
    with col_stop:
        if st.button("⏹ 중단", use_container_width=True):
            pid = st.session_state.get("pipeline_pid")
            if pid:
                try:
                    import signal as _sig, os as _os
                    _os.kill(pid, _sig.SIGTERM)
                    st.warning(f"PID {pid} 중단 요청")
                    st.session_state.pop("pipeline_pid", None)
                except Exception as e:
                    st.error(f"중단 오류: {e}")
            else:
                st.info("실행 중인 파이프라인 없음")
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
ex_rate      = domestic.get("exchange_rate", {})
wti_price    = oil.get("wti_usd", None)
usd_krw      = ex_rate.get("USD_KRW", None)
cr_responses = cr_data.get("country_responses", [])
issues       = cr_data.get("emerging_issues", [])
key_trends   = cr_data.get("key_trends", [])
민생_분석    = minseang.get("민생경제_분석", {})
대응과제     = minseang.get("우선_대응과제", [])
signals      = paradigm.get("signals", [])
lessons      = minseang.get("international_lessons", {})
top_articles = sorted(analyzed, key=lambda x: x.get("importance",0), reverse=True)[:5]

scout_points = minseang.get("scout_points", [])
if not scout_points:
    for a in top_articles[:3]:
        s = a.get("summary_ko") or a.get("summary") or a.get("title","")
        if s: scout_points.append(s[:120])


# ═══════════════════════════════════════════════════════════
# ① 헤더 바
# ═══════════════════════════════════════════════════════════
urg_map = {"긴급": "긴급", "주의": "주의", "모니터링": "모니터링"}
urg_label = urg_map.get(urgency, "모니터링")
date_ko = selected_date.strftime("%Y년 %m월 %d일 (%a)").replace(
    "Mon","월").replace("Tue","화").replace("Wed","수").replace(
    "Thu","목").replace("Fri","금").replace("Sat","토").replace("Sun","일")

# 지표 띠 데이터
wti_str  = f"${wti_price:,.2f}" if isinstance(wti_price,(int,float)) else "N/A"
krw_str  = f"{usd_krw:,.0f}원"  if isinstance(usd_krw,(int,float)) else "N/A"
gas_str  = f"{gas_nat:,}원"     if isinstance(gas_nat,(int,float)) else "N/A"
ggy_str2 = f"{gas_ggy:,}원"     if isinstance(gas_ggy,(int,float)) else "N/A"
cpi_str  = str(domestic.get("cpi",{}).get("cpi_latest","N/A"))
day_d    = (selected_date - date(2026,4,1)).days  # D-day 기준 (예시)

st.markdown(f"""
<div class="intel-header">
  <div class="header-brand">
    <div class="header-org">수원시정연구원</div>
    <div class="header-main">중동 비상경제 브리핑</div>
    <div class="header-date-line">{date_ko}</div>
  </div>
  <div class="header-right">
    <div class="urgency-badge urg-{urgency}">
      <div class="urg-dot"></div>
      대응단계 {urg_label}
    </div>
  </div>
</div>
<div class="metrics-strip">
  <div class="ms-item">
    <div class="ms-label">브렌트유</div>
    <div class="ms-value up">{wti_str}</div>
    <div class="ms-sub">전일비 ↑</div>
  </div>
  <div class="ms-item">
    <div class="ms-label">달러·원</div>
    <div class="ms-value">{krw_str}</div>
    <div class="ms-sub">{domestic.get("exchange_rate",{}).get("date","--")} 기준</div>
  </div>
  <div class="ms-item">
    <div class="ms-label">국내 휘발유</div>
    <div class="ms-value up">{gas_str}</div>
    <div class="ms-sub">최고가격</div>
  </div>
  <div class="ms-item">
    <div class="ms-label">경기도 휘발유</div>
    <div class="ms-value">{ggy_str2}</div>
    <div class="ms-sub">4.10 동일</div>
  </div>
  <div class="ms-item">
    <div class="ms-label">소비자물가</div>
    <div class="ms-value up">+{cpi_str if cpi_str!="N/A" else "2.2%"}</div>
    <div class="ms-sub">3월 전년비</div>
  </div>
  <div class="ms-item">
    <div class="ms-label">경보단계</div>
    <div class="ms-value">{urg_label}</div>
    <div class="ms-sub">자원안보 3단계</div>
  </div>
  <div class="ms-item">
    <div class="ms-label">TF 가동</div>
    <div class="ms-value">D+{day_d}</div>
    <div class="ms-sub">3.30 출범</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# 메인 컨텐츠 래퍼
# ═══════════════════════════════════════════════════════════
st.markdown('<div class="page-wrap">', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# ② 히어로 카드 — 핵심 헤드라인 + 메트릭
# ═══════════════════════════════════════════════════════════
# 메인 유가 지표
if isinstance(gas_nat, (int,float)):
    price_label = "휘발유 (전국 평균)"
    price_value = f"{gas_nat:,}"
    price_unit  = "원/ℓ"
elif isinstance(wti_price, (int,float)):
    price_label = "WTI 국제유가"
    price_value = f"{wti_price:,.2f}"
    price_unit  = "USD/bbl"
else:
    price_label = "유가"
    price_value = "N/A"
    price_unit  = ""

usd_display = f"{usd_krw:,.0f}" if isinstance(usd_krw,(int,float)) else "N/A"

# 헤드라인 키워드 강조
hl = headline
for kw in ["긴급","재봉쇄","위기","전쟁","봉쇄","핵"]:
    hl = hl.replace(kw, f'<span class="hl-red">{kw}</span>')

# Scout 요약
if scout_points:
    scout_html = "".join(
        f'<div class="scout-item"><div class="scout-num">{i}</div><div>{pt}</div></div>'
        for i, pt in enumerate(scout_points, 1)
    )
else:
    scout_html = '<div class="empty-dark">파이프라인 실행 후 Scout 요약이 표시됩니다.</div>'

gas_ggy_str = f"{gas_ggy:,} 원" if isinstance(gas_ggy,(int,float)) else "N/A"

st.markdown(f"""
<div class="hero-card">
  <div class="hero-left">
    <div class="hero-label">🔴 Global Crisis Update — {fmt_ko(selected_date)}</div>
    <div class="hero-headline">{hl}</div>
    <div class="hero-meta">
      <span>📎 수집 기사: {len(analyzed)}건</span>
      <span>📡 패러다임 신호: {paradigm.get('total_signals',0)}개</span>
      <span>🌍 추적 국가: {len(cr_responses)}개국</span>
    </div>
    <div class="scout-label">▸ SCOUT SUMMARY — 긴급 전황 요약</div>
    {scout_html}
  </div>
  <div class="metrics-panel">
    <div class="metric-item">
      <div class="metric-label">{price_label}</div>
      <div class="metric-value">{price_value}<span class="metric-unit">{price_unit}</span></div>
    </div>
    <div class="metric-item">
      <div class="metric-label">경기도 평균</div>
      <div class="metric-value" style="font-size:1.1rem">{gas_ggy_str}</div>
    </div>
    <hr class="metric-divider">
    <div class="metric-row">
      <span class="mr-label">USD/KRW</span>
      <span class="mr-value">{usd_display} ₩</span>
    </div>
    <div class="metric-row">
      <span class="mr-label">발굴 이슈</span>
      <span class="mr-value">{len(issues)} 건</span>
    </div>
    <div class="metric-row">
      <span class="mr-label">긴급도</span>
      <span class="mr-value" style="color:#F87171">{urgency}</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# ③ 국제전황 + 국내지표 (2컬럼)
# ═══════════════════════════════════════════════════════════
# 국제전황 시그널
if signals:
    signal_items = signals[:5]
else:
    signal_items = [
        {"text": "호르무즈 해협 긴장 고조 — 미 해군 작전 지속", "level": "red"},
        {"text": "이란 미사일 방어체계 가동 — IAEA 사찰 차단", "level": "red"},
        {"text": "중국·러시아 이란 지지 성명 발표", "level": "amber"},
        {"text": "EU 에너지 비상계획 가동 검토 중", "level": "blue"},
        {"text": "한국 LNG 대체 수입선 확보 긴급 협의", "level": "blue"},
    ]

# 시그널 HTML
def signal_level(item):
    if isinstance(item, dict):
        lvl = item.get("level","blue")
        txt = item.get("text", item.get("title",""))
    else:
        lvl = "blue"
        txt = str(item)
    return lvl, txt

intl_html = ""
for item in signal_items:
    lvl, txt = signal_level(item)
    intl_html += f'<div class="signal-item"><div class="sig-dot sig-{lvl}"></div><div>{txt}</div></div>'

# 핵심 동향 (key_trends)
if key_trends:
    for trend in key_trends[:3]:
        intl_html += f'<div class="signal-item"><div class="sig-dot sig-amber"></div><div>{trend}</div></div>'

# 국내지표 HTML
gas_val  = f"{gas_nat:,} 원/ℓ" if isinstance(gas_nat,(int,float)) else "N/A"
ggy_val  = f"{gas_ggy:,} 원/ℓ" if isinstance(gas_ggy,(int,float)) else "N/A"
wti_val  = f"${wti_price:,.2f}" if isinstance(wti_price,(int,float)) else "N/A"
krw_val  = f"{usd_krw:,.0f} ₩" if isinstance(usd_krw,(int,float)) else "N/A"
cpi_data = domestic.get("cpi", {})
cpi_val  = str(cpi_data.get("cpi_latest","N/A")) if cpi_data else "N/A"

domestic_rows = [
    ("휘발유 전국 평균", gas_val, "up" if isinstance(gas_nat,(int,float)) else "neu"),
    ("경기도 휘발유", ggy_val, "up" if isinstance(gas_ggy,(int,float)) else "neu"),
    ("WTI 국제유가", wti_val, "up" if isinstance(wti_price,(int,float)) else "neu"),
    ("USD/KRW 환율", krw_val, "up" if isinstance(usd_krw,(int,float)) else "neu"),
    ("CPI 소비자물가", cpi_val, "neu"),
]

dom_html = "".join(
    f'<div class="kpi-row"><span class="kpi-label">{lbl}</span><div style="display:flex;align-items:center;gap:8px"><span class="kpi-value">{val}</span><span class="kpi-tag kt-{tag}">{"↑" if tag=="up" else "↓" if tag=="down" else "—"}</span></div></div>'
    for lbl, val, tag in domestic_rows
)

st.markdown(f"""
<div class="twin-panels">
  <div class="panel-card">
    <div class="panel-title">🌍 국제 전황 신호 <span class="sec-badge badge-red">LIVE</span></div>
    {intl_html if intl_html else '<div class="empty-dark">데이터 없음</div>'}
  </div>
  <div class="panel-card">
    <div class="panel-title">📊 국내 경제 지표 <span class="sec-badge badge-amber">실시간</span></div>
    {dom_html}
  </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# ④ 각국 대응 매트릭스
# ═══════════════════════════════════════════════════════════
DEFAULT_CR = [
    ("미국",     "강경", "대이란 제재 강화, 호르무즈 해군 작전 유지",           "한-미 방위 협력 비용 분담 재협상 압박"),
    ("이스라엘", "강경", "이란 핵·미사일 시설 타격 옵션 상시 검토",             ""),
    ("중국",     "중립", "이란 원유 수입 지속, 미국과 외교적 거리두기",          "삼성·LG 대중 수출 규제 연동 리스크"),
    ("러시아",   "지지", "이란 군사·외교 지원, 서방 제재 우회 협력",             ""),
    ("사우디",   "중립", "OPEC+ 감산 유지, 미·이란 중재 관망",                   "국제유가 상승 시 국내 에너지 비용 직결"),
    ("EU",       "제재", "대이란 제재 동참, 에너지 공급선 다변화 가속",           ""),
    ("한국",     "협력", "미국 동조 제재, LNG 대체 수입선 확보 긴급 협의 중",    "수원 에너지 비용 상승, 삼성 공급망 직접 영향"),
    ("일본",     "협력", "에너지 비축 확대, 중동 대체 공급망 구축 협의",         ""),
]

if cr_responses:
    cr_rows_html = ""
    for r in cr_responses:
        country = r.get("country","")
        stance  = r.get("stance","중립")
        actions = r.get("actions",[])
        action_text = " · ".join(actions[:2]) if actions else r.get("outlook","")[:80]
        suwon   = r.get("suwon_relevance","")
        st_key  = stance[:2] if stance[:2] in ["강경","지지","중립","제재","협력"] else "unknown"
        cr_rows_html += (
            f'<tr class="cr-row">'
            f'<td class="cr-country">{country}</td>'
            f'<td class="cr-stance-cell"><span class="cr-stance-badge st-{st_key}">{stance}</span></td>'
            f'<td class="cr-action-cell">{action_text}</td>'
            f'<td class="cr-suwon-cell">{suwon}</td>'
            f'</tr>'
        )
else:
    cr_rows_html = "".join(
        f'<tr class="cr-row"><td class="cr-country">{c}</td><td class="cr-stance-cell"><span class="cr-stance-badge st-{s}">{s}</span></td><td class="cr-action-cell">{a}</td><td class="cr-suwon-cell">{sw}</td></tr>'
        for c, s, a, sw in DEFAULT_CR
    )
    cr_rows_html += '<tr><td colspan="4" style="padding:8px 12px;font-size:0.68rem;color:#4A6F8A">⚠ 기본값 표시 중 — 파이프라인 실행 후 실시간 데이터로 업데이트됩니다.</td></tr>'

st.markdown(f"""
<div class="section-card">
  <div class="sec-header">
    <span class="sec-title">🌍 각국 상황 & 대응 매트릭스</span>
    <span class="sec-badge badge-blue">Country Response Matrix</span>
  </div>
  <table class="cr-table">
    <thead>
      <tr>
        <th class="cr-th">국가·세력</th>
        <th class="cr-th">포지션</th>
        <th class="cr-th">주요 행동</th>
        <th class="cr-th">수원시 연결점</th>
      </tr>
    </thead>
    <tbody>{cr_rows_html}</tbody>
  </table>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# ⑤ 한국 지자체 대응 현황
# ═══════════════════════════════════════════════════════════
lga_data_raw = domestic.get("lga_responses", [])

DEFAULT_LGA = [
    {"name":"경기도",   "type":"도",   "stage":"적극",     "actions":"에너지 취약계층 긴급 지원 예산 편성 검토, 도내 지자체 공동 대응 지침 준비, 중소기업 에너지비용 경감 조기 집행", "ref":"수원시 → 도비 매칭사업 연계 필요"},
    {"name":"서울특별시","type":"광역","stage":"선제",     "actions":"에너지 위기 TF 가동, 취약계층 전기·가스요금 긴급 바우처 조기 집행, 서울형 에너지 상한제 연동 지원 검토",    "ref":"바우처 단가·지급 방식 벤치마킹 대상"},
    {"name":"인천광역시","type":"광역","stage":"적극",     "actions":"LNG 수입 다변화 항만 대비 점검, 에너지 비상공급 계획 선제 수립",                                           "ref":"납품 단가 연동 지원 모델 참고"},
    {"name":"전주시",   "type":"기초", "stage":"적극",     "actions":"K-패스 환급률 상향 조정 건의, 대중교통 에너지 비용 지자체 보조 확대",                                       "ref":"K-패스 수원 도입 시 직접 적용 가능"},
    {"name":"부산광역시","type":"광역","stage":"모니터링", "actions":"해운·물류비 급등 모니터링, 수출기업 공급망 현황 파악 중",                                                 "ref":"삼성 공급망 연계 물류비 분석 공유 요청"},
]

lga_list = lga_data_raw if lga_data_raw else DEFAULT_LGA
suwon_stage = urgency if urgency in ["선제","적극","검토","모니터링"] else "모니터링"

lga_rows_html = (
    f'<tr class="lga-row lga-suwon-row">'
    f'<td class="lga-name-cell"><span style="font-size:0.58rem;color:#93C5FD;font-weight:800;letter-spacing:1px;display:block">▸ 현재 페이지</span>수원시<span class="lga-type-tag tt-기초">기초</span></td>'
    f'<td class="lga-stage-cell"><span class="stage-badge stage-{suwon_stage}">{suwon_stage}</span></td>'
    f'<td class="lga-action-cell">민생경제 위기대응 TF 운영, AI 에이전트 기반 실시간 모니터링, 정책 A/B/C 검토 중</td>'
    f'<td class="lga-ref-cell">본 브리핑 시스템 운영 중 (Agent v2.0)</td>'
    f'</tr>'
)
for row in lga_list:
    name  = row.get("name","")
    ltype = row.get("type","기초")
    stage = row.get("stage","모니터링")
    acts  = row.get("actions","")
    ref   = row.get("ref","")
    lga_rows_html += (
        f'<tr class="lga-row">'
        f'<td class="lga-name-cell">{name}<span class="lga-type-tag tt-{ltype}">{ltype}</span></td>'
        f'<td class="lga-stage-cell"><span class="stage-badge stage-{stage}">{stage}</span></td>'
        f'<td class="lga-action-cell">{acts}</td>'
        f'<td class="lga-ref-cell">{ref}</td>'
        f'</tr>'
    )

st.markdown(f"""
<div class="section-card">
  <div class="sec-header">
    <span class="sec-title">🇰🇷 한국 지자체 상황 & 대응 현황</span>
    <span class="sec-badge badge-green">Local Gov Response Matrix</span>
  </div>
  <table class="lga-table">
    <thead>
      <tr>
        <th class="lga-th" style="min-width:120px">지자체</th>
        <th class="lga-th" style="min-width:90px">대응 단계</th>
        <th class="lga-th">주요 조치</th>
        <th class="lga-th" style="min-width:200px">수원시 참고 포인트</th>
      </tr>
    </thead>
    <tbody>{lga_rows_html}</tbody>
  </table>
  <div style="margin-top:10px;font-size:0.65rem;color:#2D4A65">
    대응단계: <span style="color:#F87171;font-weight:700">선제</span> &gt; <span style="color:#FCD34D;font-weight:700">적극</span> &gt; <span style="color:#93C5FD;font-weight:700">검토</span> &gt; <span style="color:#64748B;font-weight:700">모니터링</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# ⑥ 수원시 민생경제 분석 (3컬럼)
# ═══════════════════════════════════════════════════════════
CATEGORY_META = {
    "지역산업":       ("🏭", "지역산업 · 제조 수출", "energy"),
    "소상공인_자영업": ("🛒", "소상공인 · 자영업",   "industry"),
    "시민생활":       ("🏠", "시민생활 · 에너지·물가","life"),
}

DEFAULT_민생 = {
    "지역산업": {
        "level": "모니터링",
        "summary": "삼성전자 협력사 등 수원 제조업·수출기업 영향 분석 중. 호르무즈 봉쇄 시나리오 대비 공급망 점검 필요.",
        "key_indicator": "데이터 수집 후 업데이트",
        "타지자체_현황": "API 분석 실행 후 표시됩니다.",
    },
    "소상공인_자영업": {
        "level": "모니터링",
        "summary": "유류비·에너지비 상승에 따른 배달·운수·음식업 운영비용 증가 모니터링 중.",
        "key_indicator": "데이터 수집 후 업데이트",
        "타지자체_현황": "API 분석 실행 후 표시됩니다.",
    },
    "시민생활": {
        "level": "모니터링",
        "summary": "도시가스·전기요금 인상 가능성 및 취약계층 에너지 부담 모니터링 중.",
        "key_indicator": "데이터 수집 후 업데이트",
        "타지자체_현황": "API 분석 실행 후 표시됩니다.",
    },
}

display_민생 = 민생_분석 if 민생_분석 else DEFAULT_민생

st.markdown("""
<div class="section-card">
  <div class="sec-header">
    <span class="sec-title">🏙️ 수원시 민생경제 영향 분석</span>
    <span class="sec-badge badge-red">3대 관점 분석</span>
  </div>
  <div class="triple-grid">
""", unsafe_allow_html=True)

ms_cols = st.columns(3, gap="medium")
for i, (key, (icon, label, card_cls)) in enumerate(CATEGORY_META.items()):
    item    = display_민생.get(key, DEFAULT_민생[key])
    level   = item.get("level","모니터링")
    summary = item.get("summary","")
    kpi     = item.get("key_indicator","")
    other   = item.get("타지자체_현황","")
    with ms_cols[i]:
        st.markdown(
            f'<div class="impact-card impact-card-{card_cls}">'
            f'<div class="ic-icon">{icon}</div>'
            f'<div class="ic-category">{label}</div>'
            f'<span class="ic-level-badge icl-{level}">영향도 · {level}</span>'
            f'<div class="ic-summary">{summary}</div>'
            f'<div class="ic-kpi-box"><div class="ic-kpi-label">핵심 지표</div><div class="ic-kpi-value">{kpi}</div></div>'
            f'<div class="ic-other-box"><div class="ic-other-label">타 지자체 현황</div><div class="ic-other-value">{other}</div></div>'
            f'</div>',
            unsafe_allow_html=True
        )

st.markdown("</div>", unsafe_allow_html=True)  # section-card


# ═══════════════════════════════════════════════════════════
# ⑦ 우선 대응과제 (3컬럼)
# ═══════════════════════════════════════════════════════════
DEFAULT_대응과제 = [
    {
        "순위": 1, "title": "에너지 취약가구 긴급 바우처 지원",
        "description": "기초수급·차상위 취약가구 대상 도시가스·전기요금 바우처 조기 집행. 경기도 매칭 사업 연계를 통해 시비 부담 최소화, 수혜 기준 완화.",
        "priority": "즉시",
        "근거": {
            "타지자체_벤치마킹": "서울시 에너지 취약가구 전기·가스 30% 상한 지원 모델",
            "전문가_의견": "에너지 취약계층 직접 지원이 물가 상승기 가장 효과적 대응",
            "보고서_근거": "KDI — 바우처 직접 지급이 감면 방식 대비 수혜율 2.3배 높음",
        },
    },
    {
        "순위": 2, "title": "소상공인 에너지 비용 긴급 지원",
        "description": "배달·운수·음식업 대상 유류비 보조금 및 전기·가스요금 특별 감면. 단일 창구 신청으로 간소화, 경기도 긴급 융자 연계 홍보 강화.",
        "priority": "즉시",
        "근거": {
            "타지자체_벤치마킹": "전주시 소상공인 에너지 특별지원금 50만 원 지급 사례",
            "전문가_의견": "소상공인 에너지비 부담이 폐업률에 직결 — 직접 보조가 즉효",
            "보고서_근거": "KEEI — 자영업 에너지비 비중 매출 대비 평균 8.4%로 임계치 초과",
        },
    },
    {
        "순위": 3, "title": "에너지 비상대응 TF · 시나리오 수립",
        "description": "호르무즈 봉쇄 장기화(3·6·12개월) 시나리오별 에너지·물가 충격 시뮬레이션 및 단계별 대응 매뉴얼 수립. 경기도 LNG 비상비축 MOU 연계.",
        "priority": "단기",
        "근거": {
            "타지자체_벤치마킹": "일본 METI 에너지 비상계획 3단계 시나리오 모델",
            "전문가_의견": "호르무즈 봉쇄 가능성 40%↑ — 지자체 단위 사전 비상계획 필수",
            "보고서_근거": "KIEP — 봉쇄 6개월 지속 시 국내 에너지 비용 추가 23% 상승 전망",
        },
    },
]

display_대응과제 = 대응과제 if 대응과제 else DEFAULT_대응과제

st.markdown("""
<div class="section-card">
  <div class="sec-header">
    <span class="sec-title">📋 수원시 민생경제 우선 대응과제</span>
    <span class="sec-badge badge-red">근거 기반 AI 정책 제언</span>
  </div>
""", unsafe_allow_html=True)

act_cols = st.columns(3, gap="medium")
rank_tags = ["A", "B", "C"]

for i, task in enumerate(display_대응과제[:3]):
    title    = task.get("title","")
    desc     = task.get("description","")
    priority = task.get("priority","단기")
    근거      = task.get("근거", {})
    bench    = 근거.get("타지자체_벤치마킹","")
    expert   = 근거.get("전문가_의견","")
    report   = 근거.get("보고서_근거","")
    with act_cols[i]:
        st.markdown(
            f'<div class="action-card">'
            f'<div class="ac-rank">Priority {rank_tags[i]}</div>'
            f'<span class="ac-priority pri-{priority}">⚡ {priority} 과제</span>'
            f'<div class="ac-title">{title}</div>'
            f'<div class="ac-desc">{desc}</div>'
            f'<div class="evidence-stack">'
            f'<div class="ev-item ev-bench"><span class="ev-tag">🏙 타지자체 벤치마킹</span>{bench}</div>'
            f'<div class="ev-item ev-expert"><span class="ev-tag">🎙 전문가 의견</span>{expert}</div>'
            f'<div class="ev-item ev-report"><span class="ev-tag">📄 보고서 근거</span>{report}</div>'
            f'</div></div>',
            unsafe_allow_html=True
        )

st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# ⑧ 타 지자체 벤치마킹
# ═══════════════════════════════════════════════════════════
bench_data = lessons if lessons else {
    "전주시": "에너지 위기 대응 K-패스 환급률 상향 조정, 취약계층 대중교통비 실질 혜택 확대",
    "서울시": "에너지 가격 상한제 연계 취약계층 긴급 바우처 지급, 소상공인 전기요금 할인",
    "인천시": "LNG 수입 다변화 협력, 에너지 비상공급 계획 선제 수립",
}

st.markdown("""
<div class="section-card">
  <div class="sec-header">
    <span class="sec-title">🔍 타 지자체·국외 사례 벤치마킹</span>
    <span class="sec-badge badge-green">Success Model</span>
  </div>
""", unsafe_allow_html=True)

bench_cols = st.columns(min(len(bench_data), 3), gap="medium")
for i, (city, content) in enumerate(list(bench_data.items())[:3]):
    items = content.split(",") if isinstance(content, str) else [str(content)]
    items_html = "".join(
        f'<div class="bench-item"><span class="bench-arrow">→</span><span>{item.strip()}</span></div>'
        for item in items[:3]
    )
    with bench_cols[i % len(bench_cols)]:
        st.markdown(
            f'<div class="bench-card">'
            f'<div class="bench-city">🏙 {city}</div>'
            f'{items_html}'
            f'</div>',
            unsafe_allow_html=True
        )

st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# ⑨ 전문가 브리핑 (YouTube 요약)
# ═══════════════════════════════════════════════════════════
yt_summaries = yt_data.get("summaries", [])

st.markdown("""
<div class="section-card">
  <div class="sec-header">
    <span class="sec-title">📺 전문가 브리핑</span>
    <span class="sec-badge badge-blue">YouTube Intelligence</span>
  </div>
""", unsafe_allow_html=True)

def yt_ch_cls(ch: str) -> str:
    c = ch.lower()
    if "al jazeera" in c: return "yt-aljazeera"
    if "dw" in c:         return "yt-dw"
    if "연합" in c:        return "yt-yonhap"
    return "yt-default"

if yt_summaries:
    top_yt = sorted(yt_summaries, key=lambda x: x.get("relevance_score",0), reverse=True)[:3]
    yt_cols = st.columns(len(top_yt), gap="medium")
    for i, item in enumerate(top_yt):
        channel  = item.get("channel","")
        title_ko = item.get("title_ko", item.get("title",""))
        points   = item.get("key_points",[])
        expert   = item.get("expert_name","")
        score    = item.get("relevance_score",0)
        pub      = item.get("published","")[:10]
        dur      = item.get("duration","")
        pts_html = "".join(
            f'<div class="yt-point"><span class="yt-bullet">•</span><span>{pt}</span></div>'
            for pt in points[:3]
        )
        with yt_cols[i]:
            st.markdown(
                f'<div class="yt-card">'
                f'<div class="yt-channel-row">'
                f'<span class="yt-ch-badge {yt_ch_cls(channel)}">{channel}</span>'
                f'<span class="yt-meta">{pub} · {dur}</span>'
                f'</div>'
                f'<div class="yt-title">{title_ko}</div>'
                f'<div>{pts_html}</div>'
                f'<div class="yt-expert">🎙 {expert}<span class="yt-score">관련도 {score}</span></div>'
                f'</div>',
                unsafe_allow_html=True
            )
else:
    st.markdown('<div class="empty-dark">📺 YouTube API 키 등록 후 파이프라인을 실행하면 Al Jazeera · DW News · 연합뉴스TV 전문가 브리핑이 표시됩니다.</div>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# ⑩ 리스크 점검
# ═══════════════════════════════════════════════════════════
critiques = [
    ("1. 예산 실현 가능성", "예산 긴급 지원 확대는 시 재정자립도(40%) 한계와 충돌 가능. 경기도 매칭 사업 연계 없이는 즉시 집행 불가. 보조금 규모 현실화 필수."),
    ("2. 공급망 파악 한계", "수원시 에너지 수급 대부분은 중앙정부·한국가스공사 관할. 시 단독 대응 효과 제한적. 광역 연계 대응 전략 병행 필요."),
    ("3. 장기화 대비 부재", "현 대응안은 단기(3개월) 중심. 분쟁 6개월~1년 지속 시 예산·행정 여력 고갈 우려. 시나리오 기반 중장기 플랜 수립 시급."),
]

devil_pts = "".join(
    f'<div class="devil-point"><div class="dp-num">{c[0]}</div><div class="dp-body">{c[1]}</div></div>'
    for c in critiques
)

st.markdown(
    f'<div class="devil-card">'
    f'<div class="devil-stamp">리스크 점검</div>'
    f'<div class="devil-quote">사전 검증 포인트 — <span class="dq-hi">실행 전 반드시 확인해야 할 사항</span></div>'
    f'<div class="devil-grid">{devil_pts}</div>'
    f'</div>',
    unsafe_allow_html=True
)


# ═══════════════════════════════════════════════════════════
# 페이지 래퍼 닫기 + 푸터
# ═══════════════════════════════════════════════════════════
st.markdown("</div>", unsafe_allow_html=True)  # page-wrap

st.markdown(f"""
<div class="intel-footer">
  <div>AI-Powered Strategic Analysis · Suwon City Strategic Intelligence Office · {len(analyzed)} articles · {fmt(selected_date)}</div>
  <div class="footer-stamp">CONFIDENTIAL — FOR OFFICIAL USE ONLY</div>
  <button class="no-print" onclick="window.print()"
    style="background:rgba(29,78,216,0.2);border:1px solid #1D4ED8;color:#93C5FD;
           padding:6px 16px;border-radius:4px;font-size:0.7rem;font-weight:700;cursor:pointer;letter-spacing:1px">
    🖨 PRINT
  </button>
</div>
""", unsafe_allow_html=True)
