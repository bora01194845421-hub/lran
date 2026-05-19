@echo off
cd /d %~dp0
echo ========================================
echo  이란전쟁 민생 에이전트 초기 세팅
echo ========================================

echo [1/3] 패키지 설치 중...
pip install -r requirements.txt

echo [2/3] .env 파일 생성...
if not exist .env (
    copy .env.example .env
    echo .env 파일이 생성됐습니다.
    echo 메모장으로 .env 파일을 열어 API 키를 입력하세요.
    notepad .env
) else (
    echo .env 파일이 이미 존재합니다.
)

echo [3/3] 완료!
echo 이제 run_pipeline.bat 또는 start_dashboard.bat 을 실행하세요.
pause
