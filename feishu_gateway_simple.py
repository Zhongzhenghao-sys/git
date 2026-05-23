#!/usr/bin/env python3
"""
Windows兼容的飞书网关启动器 - 简化版
直接清理锁文件，避免进程检查问题
"""
import os
import sys
import platform
import json
from pathlib import Path

# 添加项目路径
project_dir = r'D:\hermes_agent'
sys.path.insert(0, project_dir)

# 设置环境变量
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['HERMES_QUIET'] = '1'
os.environ['HERMES_EXEC_ASK'] = '1'

print("=" * 60)
print("Hermes Agent - Feishu Gateway (Windows)")
print("=" * 60)

# Windows特定清理
if platform.system() == 'Windows':
    hermes_home = Path.home() / '.hermes'
    
    # 清理所有锁文件和状态文件
    lock_files = [
        'gateway.pid',
        'gateway_state.json',
        'feishu.lock',
        'gateway.lock'
    ]
    
    for lock_file in lock_files:
        file_path = hermes_home / lock_file
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"[Clean] Removed: {lock_file}")
            except:
                pass
    
    print("[Info] Windows cleanup completed")

print(f"Platform: {platform.system()}")
print("Mode: WebSocket")
print("Press Ctrl+C to stop")
print("=" * 60)

try:
    # 导入并启动网关
    from gateway.run import start_gateway
    import asyncio
    
    asyncio.run(start_gateway())
except KeyboardInterrupt:
    print("\n[Info] Gateway stopped")
except Exception as e:
    print(f"\n[Error] Startup failed: {e}")
    
    # 提供具体建议
    if "FEISHU" in str(e).upper():
        print("\n[Feishu-specific issues]:")
        print("1. Check FEISHU_APP_ID and FEISHU_APP_SECRET")
        print("2. Verify app permissions in Feishu developer console")
        print("3. Ensure network can connect to Feishu servers")
    
    print("\n[Debug] Try running with HERMES_QUIET=0 for detailed logs")
    sys.exit(1)