@echo off
chcp 65001 >nul
title [대시보드] 수원시 인텔리전스 브리프
echo.
echo  ┌─────────────────────────────────────────┐
echo  │   수원시 AI 브리핑 대시보드 시작        │
echo  │   http://localhost:8502 에서 확인        │
echo  └─────────────────────────────────────────┘
echo.
cd /d "%~dp0"
python -m streamlit run dashboard.py --server.port 8502 --server.address 0.0.0.0 --browser.gatherUsageStats false
pause
