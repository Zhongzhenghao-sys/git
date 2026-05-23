@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set HERMES_QUIET=1
set HERMES_EXEC_ASK=1

cd /d D:\hermes_agent

echo.
echo ========================================
echo   Hermes Agent - 飞书网关启动器
echo ========================================
echo   App ID: cli_a9388aea1a381bc2
echo   模式: WebSocket 长连接
echo ========================================
echo.

REM 清理旧的PID文件
if exist "%USERPROFILE%\.hermes\gateway.pid" (
    echo [信息] 清理旧的PID文件...
    del "%USERPROFILE%\.hermes\gateway.pid"
)

if exist "%USERPROFILE%\.hermes\gateway_state.json" (
    echo [信息] 清理旧的网关状态文件...
    del "%USERPROFILE%\.hermes\gateway_state.json"
)

REM 检查飞书配置
echo [信息] 检查飞书配置...
if not defined FEISHU_APP_ID (
    echo [错误] 未找到FEISHU_APP_ID环境变量
    echo [提示] 请确保~/.hermes/.env文件中有飞书配置
    pause
    exit /b 1
)

echo [信息] 激活Python虚拟环境...
call .\venv\Scripts\activate

echo [信息] 启动飞书网关...
echo [提示] 按 Ctrl+C 停止网关
echo.

REM 运行网关
python -c "
import os
import sys
import asyncio

# 添加项目路径
project_dir = r'D:\hermes_agent'
sys.path.insert(0, project_dir)

# 设置环境变量
os.environ['HERMES_QUIET'] = '1'
os.environ['HERMES_EXEC_ASK'] = '1'

# 导入网关
from gateway.run import start_gateway

print('飞书网关启动中...')
print('连接模式: WebSocket')
print('按 Ctrl+C 停止')

try:
    asyncio.run(start_gateway())
except KeyboardInterrupt:
    print('\n网关已停止')
except Exception as e:
    print(f'启动失败: {e}')
    sys.exit(1)
"

echo.
echo ========================================
echo   网关已停止
echo ========================================
pause