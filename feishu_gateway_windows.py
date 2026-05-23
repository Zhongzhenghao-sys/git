#!/usr/bin/env python3
"""
Windows兼容的飞书网关启动器
解决os.kill在Windows上的问题
"""
import os
import sys
import platform

# 添加项目路径
project_dir = r'D:\hermes_agent'
sys.path.insert(0, project_dir)

# 设置环境变量
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['HERMES_QUIET'] = '1'
os.environ['HERMES_EXEC_ASK'] = '1'

# Windows特定修复
if platform.system() == 'Windows':
    # 清理旧的PID文件
    hermes_home = os.path.expanduser('~/.hermes')
    pid_file = os.path.join(hermes_home, 'gateway.pid')
    state_file = os.path.join(hermes_home, 'gateway_state.json')
    
    for file_path in [pid_file, state_file]:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"[清理] 已删除: {file_path}")
            except:
                pass
    
    # 应用补丁：修复Windows上的os.kill问题
    import gateway.status as status_module
    
    # 保存原始函数
    original_acquire_scoped_lock = status_module.acquire_scoped_lock
    
    def patched_acquire_scoped_lock(lock_name, record, timeout=5):
        """Windows兼容的锁获取函数"""
        if platform.system() == 'Windows':
            # 简化Windows版本，跳过进程检查
            import json
            from pathlib import Path
            
            lock_path = Path(status_module._hermes_home) / f"{lock_name}.lock"
            
            # 直接尝试创建锁文件
            try:
                fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    json.dump(record, handle)
                return True, None
            except FileExistsError:
                # 锁已存在，读取内容
                try:
                    with open(lock_path, 'r', encoding='utf-8') as f:
                        existing = json.load(f)
                    return False, existing
                except:
                    return False, None
        else:
            # Linux/macOS使用原始函数
            return original_acquire_scoped_lock(lock_name, record, timeout)
    
    # 应用补丁
    status_module.acquire_scoped_lock = patched_acquire_scoped_lock
    print("[修复] 已应用Windows兼容性补丁")

print("=" * 60)
print("Hermes Agent - 飞书网关")
print("=" * 60)
print(f"平台: {platform.system()}")
print("模式: WebSocket 长连接")
print("按 Ctrl+C 停止")
print("=" * 60)

try:
    # 导入并启动网关
    from gateway.run import start_gateway
    import asyncio
    
    asyncio.run(start_gateway())
except KeyboardInterrupt:
    print("\n[信息] 网关已停止")
except Exception as e:
    print(f"\n[错误] 启动失败: {e}")
    print("\n[提示] 可能的原因:")
    print("1. 飞书App配置错误")
    print("2. 网络连接问题")
    print("3. 端口冲突")
    print("\n[调试] 尝试设置 HERMES_QUIET=0 查看详细日志")
    sys.exit(1)