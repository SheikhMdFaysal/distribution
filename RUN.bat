@echo off
echo ========================================
echo Enterprise AI Security Red Teaming Platform
echo Starting Backend Server...
echo ========================================

cd /d "%~dp0backend"

echo.
echo Installing backend dependencies...
pip install -r requirements.txt --quiet 2>nul

echo.
echo Starting server on port 8080...
echo Open http://localhost:8080 in your browser
echo.

python -m uvicorn app.main:app --host 127.0.0.1 --port 8080

pause
