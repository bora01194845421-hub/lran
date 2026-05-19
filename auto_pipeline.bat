@echo off
cd /d %~dp0
echo [%date% %time%] 파이프라인 시작 >> auto_run.log
python orchestrator.py >> auto_run.log 2>&1
echo [%date% %time%] 파이프라인 완료 >> auto_run.log

echo [%date% %time%] GitHub push 시작 >> auto_run.log
git add data/ >> auto_run.log 2>&1
git commit -m "auto: 파이프라인 결과 자동 커밋 (%date%)" >> auto_run.log 2>&1
git push origin main >> auto_run.log 2>&1
echo [%date% %time%] GitHub push 완료 >> auto_run.log
