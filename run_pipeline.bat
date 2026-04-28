@echo off
chcp 65001 >nul
title [파이프라인] 이란 뉴스 에이전트 실행

cd /d "%~dp0"

:: 날짜 인자 처리 (없으면 오늘)
set TARGET_DATE=%1

echo.
echo  ┌─────────────────────────────────────────────┐
echo  │   이란 뉴스 분석 파이프라인 실행            │
if "%TARGET_DATE%"=="" (
echo  │   날짜: 오늘 (자동)                          │
) else (
echo  │   날짜: %TARGET_DATE%                        │
)
echo  └─────────────────────────────────────────────┘
echo.
echo  [시작] %TIME%
echo.

if "%TARGET_DATE%"=="" (
    python orchestrator.py
) else (
    python orchestrator.py --date %TARGET_DATE%
)

echo.
echo  [완료] %TIME%
echo  → 대시보드에서 새로고침하세요: http://localhost:8502
echo.
pause
