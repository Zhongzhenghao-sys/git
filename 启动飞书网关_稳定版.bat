@echo off
chcp 65001 >nul
title Hermes Feishu Gateway [稳定版]
cd /d D:\hermes_agent

echo ================================================================
echo  Hermes Feishu Gateway - 稳定启动版
echo  启动时间: %date% %time%
echo ================================================================

:: 清理锁文件
echo [准备] 清理旧锁文件...
if exist "C:\Users\%USERNAME%\.hermes\gateway.pid" del /f "C:\Users\%USERNAME%\.hermes\gateway.pid" >nul 2>&1
if exist "C:\Users\%USERNAME%\.hermes\gateway.lock" del /f "C:\Users\%USERNAME%\.hermes\gateway.lock" >nul 2>&1
if exist "C:\Users\%USERNAME%\.hermes\feishu.lock" del /f "C:\Users\%USERNAME%\.hermes\feishu.lock" >nul 2>&1
echo      完成

:: 激活虚拟环境
echo [准备] 激活 Python 虚拟环境...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo      已激活 venv
) else (
    echo      未找到 venv，使用系统 Python
)

:: 清理过期去重缓存
echo [准备] 检查去重缓存...
python -c "import json,time,os; f=os.path.expanduser('~/.hermes/feishu_seen_message_ids.json'); d=json.loads(open(f,encoding='utf-8').read()) if os.path.exists(f) else {'message_ids':{}}; ids=d.get('message_ids',{}); now=time.time(); valid={k:v for k,v in ids.items() if now-v<86400}; removed=len(ids)-len(valid); open(f,'w',encoding='utf-8').write(json.dumps({'message_ids':valid})) if removed>0 else None; print(f'     去重缓存: 保留{len(valid)}条，清理{removed}条过期')" 2>&1

:: 创建日志目录
if not exist "C:\Users\%USERNAME%\.hermes\logs" mkdir "C:\Users\%USERNAME%\.hermes\logs" >nul 2>&1

echo.
echo ================================================================
echo  按 Ctrl+C 停止网关
echo  日志: C:\Users\%USERNAME%\.hermes\logs\
echo ================================================================
echo.

set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1
set HERMES_QUIET=0
set HERMES_EXEC_ASK=1

:: 启动网关
python start_gateway.py

echo.
echo ================================================================
echo [网关已停止] 退出时间: %time%
echo ================================================================
pause
