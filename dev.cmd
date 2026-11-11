@echo off
rem 백엔드(8100)와 프론트엔드(3000)를 한 번에 띄운다. 사용: dev.cmd
rem 백엔드는 새 창에서, 프론트엔드는 이 창에서 실행된다. 끝낼 때는 각 창에서 Ctrl+C.
start "stroll-backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\uvicorn app.main:app --reload --port 8100"
cd /d %~dp0frontend && npm run dev
