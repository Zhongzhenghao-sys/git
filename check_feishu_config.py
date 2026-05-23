#!/usr/bin/env python3
"""
Check Feishu connection configuration
"""
import os
import sys

# Add project path
project_dir = r'D:\hermes_agent'
sys.path.insert(0, project_dir)

# Check environment variables
print("=" * 60)
print("Feishu Configuration Check")
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
        # Hide sensitive information
        if 'SECRET' in var:
            display_value = value[:4] + '...' + value[-4:] if len(value) > 8 else '***'
        else:
            display_value = value
        print(f"[OK] {var}: {display_value}")
    else:
        print(f"[ERROR] {var}: Not set")
        all_ok = False

print("\n" + "=" * 60)
print("Gateway Config File Check")
print("=" * 60)

# Check gateway config
gateway_config_path = os.path.expanduser('~/.hermes/gateway.json')
if os.path.exists(gateway_config_path):
    import json
    try:
        with open(gateway_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if 'platforms' in config and 'feishu' in config['platforms']:
            feishu_config = config['platforms']['feishu']
            print(f"[OK] Feishu platform enabled: {feishu_config.get('enabled', False)}")
            
            # Check home_channel
            if 'home_channel' in feishu_config:
                hc = feishu_config['home_channel']
                print(f"  Home channel: {hc.get('name', 'Unnamed')}")
                print(f"  Chat ID: {hc.get('chat_id', 'Not set')}")
            else:
                print("  Warning: No home_channel set")
        else:
            print("[ERROR] Feishu platform not found in gateway config")
            all_ok = False
    except Exception as e:
        print(f"[ERROR] Failed to read gateway config: {e}")
        all_ok = False
else:
    print("[ERROR] Gateway config file not found: ~/.hermes/gateway.json")
    all_ok = False

print("\n" + "=" * 60)
if all_ok:
    print("[SUCCESS] All basic configuration checks passed")
    print("\nNext steps:")
    print("1. Ensure Feishu app has correct permissions")
    print("2. Get your Feishu Chat ID")
    print("3. Update chat_id in gateway.json")
    print("4. Run the gateway startup script")
else:
    print("[FAILED] Configuration check failed, please fix above issues")
print("=" * 60)

# Provide guidance for getting chat_id
print("\nHow to get Feishu Chat ID:")
print("1. Open conversation with bot in Feishu")
print("2. Check URL or use developer tools")
print("3. Or let bot send message, get from logs")
print("\nTemporary solution: Use 'auto' as chat_id")
print("Gateway will automatically use most recent chat_id")