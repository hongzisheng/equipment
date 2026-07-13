@echo off
set ROOT=%~dp0

echo Starting backend (port 8800)...
start "Backend" /d "%ROOT%complex-events-backend" cmd /k "python main.py"

timeout /t 2 /nobreak >nul

echo Starting frontend (port 5173)...
start "Frontend" /d "%ROOT%complex-events-frontend" cmd /k "npm run dev"

echo.
echo Backend:  http://127.0.0.1:8800
echo Frontend: http://localhost:5173
