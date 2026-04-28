@echo off
REM =================================================================
REM Stop all Enterprise AI Security Red Teaming Platform servers
REM   - Kills any process listening on ports 8080 (backend) and 3000 (frontend)
REM   - Kills RQ worker (python.exe running start_worker.py)
REM =================================================================

echo.
echo  Stopping all servers...
echo.

REM Kill backend on 8080
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8080" ^| findstr "LISTENING"') do (
    echo   Killing backend ^(PID %%P^) on port 8080
    taskkill /PID %%P /F > nul 2>&1
)

REM Kill frontend on 3000
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING"') do (
    echo   Killing frontend ^(PID %%P^) on port 3000
    taskkill /PID %%P /F > nul 2>&1
)

REM Kill any python.exe running start_worker.py
for /f "tokens=2" %%P in ('wmic process where "name='python.exe' and commandline like '%%start_worker%%'" get processid /value 2^>nul ^| findstr "ProcessId"') do (
    set "WPID=%%P"
    setlocal EnableDelayedExpansion
    if not "!WPID!"=="" (
        echo   Killing RQ worker ^(PID !WPID!^)
        taskkill /PID !WPID! /F > nul 2>&1
    )
    endlocal
)

echo.
echo  Done. All three servers stopped.
echo.
pause
