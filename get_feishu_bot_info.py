#!/usr/bin/env python3
"""
获取飞书 Bot Open ID 工具
=========================
自动从飞书 API 获取 Bot 的 open_id 和名称，用于配置 FEISHU_BOT_OPEN_ID。

运行: python get_feishu_bot_info.py
"""
import json
import os
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# 读取 .env
env_file = Path.home() / ".hermes" / ".env"
env_vars = {}
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            env_vars[k.strip()] = v.strip()

APP_ID = env_vars.get("FEISHU_APP_ID") or os.getenv("FEISHU_APP_ID", "")
APP_SECRET = env_vars.get("FEISHU_APP_SECRET") or os.getenv("FEISHU_APP_SECRET", "")
DOMAIN = env_vars.get("FEISHU_DOMAIN", "feishu").lower()
BASE_URL = "https://open.larksuite.com" if DOMAIN == "lark" else "https://open.feishu.cn"

if not APP_ID or not APP_SECRET:
    print("错误: 未找到 FEISHU_APP_ID 或 FEISHU_APP_SECRET")
    print("请在 ~/.hermes/.env 中配置这两个变量")
    sys.exit(1)

print(f"APP_ID: {APP_ID}")
print(f"DOMAIN: {DOMAIN} ({BASE_URL})")
print()

def api_post(path: str, data: dict, token: str = None) -> dict:
    url = BASE_URL + path
    body = json.dumps(data).encode("utf-8")
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, data=body, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        return {"error": str(e), "body": e.read().decode("utf-8", errors="replace")}
    except URLError as e:
        return {"error": str(e)}

def api_get(path: str, token: str) -> dict:
    url = BASE_URL + path
    headers = {"Authorization": f"Bearer {token}"}
    req = Request(url, headers=headers, method="GET")
    try:
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        return {"error": str(e), "code": e.code, "body": e.read().decode("utf-8", errors="replace")}
    except URLError as e:
        return {"error": str(e)}

# Step 1: 获取 Tenant Access Token
print("Step 1: 获取 Tenant Access Token...")
result = api_post("/open-apis/auth/v3/tenant_access_token/internal", {
    "app_id": APP_ID,
    "app_secret": APP_SECRET
})
if "error" in result:
    print(f"  失败: {result['error']}")
    if "body" in result:
        print(f"  详情: {result['body'][:300]}")
    sys.exit(1)

token = result.get("tenant_access_token", "")
if not token:
    print(f"  失败: {json.dumps(result, ensure_ascii=False)}")
    sys.exit(1)
print(f"  成功! Token: {token[:20]}...")

# Step 2: 获取 Bot 信息
print("\nStep 2: 获取 Bot 信息...")
bot_info = api_get("/open-apis/bot/v3/info", token)
if "error" in bot_info:
    print(f"  失败 (code={bot_info.get('code')}): {bot_info.get('error')}")
    print(f"  注意: 需要 'Read Application Information' 权限")
else:
    bot = bot_info.get("bot", {})
    open_id = bot.get("open_id", "")
    bot_name = bot.get("app_name", "")
    print(f"  Bot Open ID: {open_id}")
    print(f"  Bot 名称: {bot_name}")
    print(f"  Bot 状态: {bot.get('status', 'unknown')}")

    if open_id:
        print("\n" + "=" * 60)
        print("请将以下配置添加到 ~/.hermes/.env 中:")
        print(f"FEISHU_BOT_OPEN_ID={open_id}")
        print(f"FEISHU_BOT_NAME={bot_name}")
        print("=" * 60)

        # 询问是否自动写入
        try:
            answer = input("\n是否自动写入 ~/.hermes/.env? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = "n"

        if answer == "y":
            env_content = env_file.read_text(encoding="utf-8")
            if "FEISHU_BOT_OPEN_ID" not in env_content:
                env_content = env_content.rstrip() + f"\nFEISHU_BOT_OPEN_ID={open_id}\n"
            if "FEISHU_BOT_NAME" not in env_content:
                env_content = env_content.rstrip() + f"\nFEISHU_BOT_NAME={bot_name}\n"
            env_file.write_text(env_content, encoding="utf-8")
            print("已写入！请重启网关使配置生效。")
        else:
            print("请手动添加上述配置后重启网关。")
