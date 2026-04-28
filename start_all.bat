@echo off
REM =================================================================
REM Enterprise AI Security Red Teaming Platform — one-click launcher
REM
REM Opens THREE PowerShell windows:
REM   1. FastAPI backend  (http://localhost:8080)
REM   2. Next.js frontend (http://localhost:3000)
REM   3. RQ async worker  (no port, needs Redis on localhost:6379)
REM
REM Close any window with Ctrl+C to stop that server.
REM Run stop_all.bat to kill all three at once.
REM =================================================================

setlocal
set "ROOT=%~dp0"

echo.
echo  Enterprise AI Security Red Teaming Platform
echo  -------------------------------------------
echo  Starting all three servers in separate windows...
echo.

REM ---- Terminal 1: FastAPI backend ----
start "AI Security - Backend (port 8080)" powershell.exe -NoExit -Command ^
    "Set-Location -Path '%ROOT%backend'; python -m uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload"

timeout /t 2 /nobreak > nul

REM ---- Terminal 2: Next.js frontend ----
start "AI Security - Frontend (port 3000)" powershell.exe -NoExit -Command ^
    "Set-Location -Path '%ROOT%frontend'; npm run dev"

timeout /t 2 /nobreak > nul

REM ---- Terminal 3: RQ worker ----
start "AI Security - RQ Worker" powershell.exe -NoExit -Command ^
    "Set-Location -Path '%ROOT%backend'; python start_worker.py"

echo.
echo  Three terminals opened.
echo.
echo  Open the dashboard in your browser:
echo      http://localhost:3000
echo.
echo  Backend health check:
echo      http://localhost:8080/api/v1/health
echo.
echo  This launcher window can be closed safely - the three servers keep running.
echo.
pause
