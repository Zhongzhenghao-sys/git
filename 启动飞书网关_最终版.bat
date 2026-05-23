@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   Hermes Agent - 飞书网关 (Windows修复版)
echo ========================================
echo.

cd /d D:\hermes_agent

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 激活虚拟环境
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate
) else (
    echo [警告] 未找到虚拟环境，使用系统Python
)

REM 运行修复版网关
echo [信息] 启动飞书网关...
echo [提示] 按 Ctrl+C 停止
echo.

python feishu_gateway_windows.py

echo.
echo ========================================
echo   网关进程已结束
echo ========================================
pause