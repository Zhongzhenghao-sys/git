@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d D:\hermes_agent

:: 从 .env 文件加载环境变量
for /f "usebackq tokens=1,* delims==" %%A in ("%USERPROFILE%\.hermes\.env") do (
    if not "%%A"=="" if not "%%A:~0,1%"=="#" set "%%A=%%B"
)

echo.
echo ========================================
echo   Hermes Agent - 飞书网关启动中...
echo ========================================
echo   App ID: %FEISHU_APP_ID%
echo   模式: %FEISHU_CONNECTION_MODE%
echo   按 Ctrl+C 停止
echo ========================================
echo.

call .\venv\Scripts\activate
hermes gateway run
pause
