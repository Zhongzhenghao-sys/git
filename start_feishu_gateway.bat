@echo off
chcp 65001 >nul
cd /d D:\hermes_agent
echo.
echo ========================================
echo   Hermes Agent - Feishu Gateway
echo ========================================
echo   Press Ctrl+C to stop
echo ========================================
echo.
call venv\Scripts\activate
python start_gateway.py
echo.
pause
