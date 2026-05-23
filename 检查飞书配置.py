#!/usr/bin/env python3
"""
测试飞书连接配置
"""
import os
import sys

# 添加项目路径
project_dir = r'D:\hermes_agent'
sys.path.insert(0, project_dir)

# 检查环境变量
print("=" * 60)
print("飞书配置检查")
print("=" * 60)

required_vars = [
    'FEISHU_APP_ID',
    'FEISHU_APP_SECRET', 
    'FEISHU_DOMAIN',
    'FEISHU_CONNECTION_MODE'
]

all_ok = True
for var in required_vars:
    value = os.getenv(var)
    if value:
        # 隐藏敏感信息
        if 'SECRET' in var:
            display_value = value[:4] + '...' + value[-4:] if len(value) > 8 else '***'
        else:
            display_value = value
        print(f"✓ {var}: {display_value}")
    else:
        print(f"✗ {var}: 未设置")
        all_ok = False

print("\n" + "=" * 60)
print("网关配置文件检查")
print("=" * 60)

# 检查网关配置
gateway_config_path = os.path.expanduser('~/.hermes/gateway.json')
if os.path.exists(gateway_config_path):
    import json
    try:
        with open(gateway_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if 'platforms' in config and 'feishu' in config['platforms']:
            feishu_config = config['platforms']['feishu']
            print(f"✓ 飞书平台已启用: {feishu_config.get('enabled', False)}")
            
            # 检查home_channel
            if 'home_channel' in feishu_config:
                hc = feishu_config['home_channel']
                print(f"  主页频道: {hc.get('name', '未命名')}")
                print(f"  Chat ID: {hc.get('chat_id', '未设置')}")
            else:
                print("  警告: 未设置home_channel")
        else:
            print("✗ 网关配置中未找到飞书平台设置")
            all_ok = False
    except Exception as e:
        print(f"✗ 读取网关配置失败: {e}")
        all_ok = False
else:
    print("✗ 网关配置文件不存在: ~/.hermes/gateway.json")
    all_ok = False

print("\n" + "=" * 60)
if all_ok:
    print("✓ 所有基本配置检查通过")
    print("\n下一步:")
    print("1. 确保飞书应用有正确的权限")
    print("2. 获取你的飞书Chat ID")
    print("3. 更新gateway.json中的chat_id")
    print("4. 运行网关启动脚本")
else:
    print("✗ 配置检查未通过，请修复上述问题")
print("=" * 60)

# 提供获取chat_id的指导
print("\n如何获取飞书Chat ID:")
print("1. 在飞书中打开与机器人的对话")
print("2. 查看URL或使用开发者工具")
print("3. 或让机器人发送消息，从日志中获取")
print("\n临时解决方案: 使用 'auto' 作为chat_id")
print("网关会自动使用最近对话的chat_id")