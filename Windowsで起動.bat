@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ========================================
echo   Rishu Gachizei - Local Server
echo ========================================
echo.
echo Please open http://127.0.0.1:8000/index.html in your browser.
echo Press Ctrl+C to stop the server.
echo.
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 backend\app_server.py
) else (
    python backend\app_server.py
)
echo.
echo Server stopped or Python was not found.
pause
