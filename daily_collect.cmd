@echo off
rem 매일 수집: 관심 종목 주가·뉴스·공시 + 오늘 증권사 리포트. 결과는 backend\data\daily.log에 쌓인다.
rem 윈도우 작업 스케줄러에 등록해서 쓴다 (README의 "매일 자동 수집" 참고). 직접 실행해도 된다.
cd /d %~dp0backend
.venv\Scripts\python -m app.daily >> data\daily.log 2>&1
