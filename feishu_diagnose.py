#!/usr/bin/env python3
"""
Feishu Gateway 诊断工具
=======================
快速诊断飞书消息不回复的原因，输出结构化诊断报告。

用法: python feishu_diagnose.py
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERMES_HOME = Path.home() / ".hermes"
PROJECT_DIR = Path(__file__).parent

PASS = "  [OK]"
WARN = "  [!] "
FAIL = "  [X]"
INFO = "  [i]"

issues = []
warnings = []

def check(label: str, ok: bool, msg: str, critical: bool = False):
    icon = PASS if ok else (FAIL if critical else WARN)
    print(f"{icon} {label}: {msg}")
    if not ok:
        (issues if critical else warnings).append(f"{label}: {msg}")

print("=" * 60)
print(" Feishu Gateway 诊断报告")
print(f" 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# ── 1. 环境变量检查 ────────────────────────────────────────────────────────────
print("\n【1】环境变量检查")
env_file = HERMES_HOME / ".env"
env_vars = {}
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            env_vars[k.strip()] = v.strip()

required = {
    "FEISHU_APP_ID": "飞书 App ID（必填）",
    "FEISHU_APP_SECRET": "飞书 App Secret（必填）",
}
recommended = {
    "FEISHU_BOT_OPEN_ID": "Bot Open ID（群消息@检测必需）",
    "FEISHU_BOT_NAME": "Bot 名称（群消息@检测必需）",
}

for k, desc in required.items():
    val = env_vars.get(k, os.getenv(k, ""))
    check(k, bool(val), f"{'已配置: ' + val[:8] + '...' if val else '未配置 → 飞书连接失败'}", critical=not bool(val))

for k, desc in recommended.items():
    val = env_vars.get(k, os.getenv(k, ""))
    check(k, bool(val), f"{'已配置' if val else f'未配置 → {desc}'}")

# group_policy 检查
gp = env_vars.get("FEISHU_GROUP_POLICY", os.getenv("FEISHU_GROUP_POLICY", "allowlist"))
allow_all = env_vars.get("FEISHU_ALLOW_ALL_USERS", os.getenv("FEISHU_ALLOW_ALL_USERS", "")).lower()
if gp == "open" or allow_all in ("true", "1", "yes"):
    check("群消息策略", True, f"FEISHU_GROUP_POLICY={gp}, ALLOW_ALL={allow_all} → 所有用户可访问")
else:
    allowed = env_vars.get("FEISHU_ALLOWED_USERS", os.getenv("FEISHU_ALLOWED_USERS", ""))
    check("群消息策略", bool(allowed),
          f"policy={gp}, 已配置白名单: {allowed[:30]}..." if allowed else
          f"policy={gp} 但 FEISHU_ALLOWED_USERS 为空 → 群消息将被拒绝",
          critical=not bool(allowed))

# ── 2. 网关进程检查 ────────────────────────────────────────────────────────────
print("\n【2】网关进程检查")
pid_file = HERMES_HOME / "gateway.pid"
state_file = HERMES_HOME / "gateway_state.json"

pid = None
if pid_file.exists():
    try:
        pid_data = json.loads(pid_file.read_text(encoding="utf-8"))
        pid = int(pid_data.get("pid", 0)) or None
        if pid:
            # 检查进程是否存活
            try:
                import subprocess
                result = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                    capture_output=True, text=True, timeout=5
                )
                alive = str(pid) in result.stdout
                check("gateway.pid", alive,
                      f"PID={pid} {'进程存活' if alive else '进程已死亡 → 网关未运行'}",
                      critical=not alive)
            except Exception:
                print(f"{INFO} 无法验证 PID={pid} 的进程状态")
        else:
            check("gateway.pid", False, "PID 为 0 或空", critical=True)
    except Exception as e:
        check("gateway.pid", False, f"读取失败: {e}", critical=True)
else:
    check("gateway.pid", False, "文件不存在 → 网关未曾启动", critical=True)

# gateway_state.json 检查
if state_file.exists():
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
        gw_state = state.get("gateway_state", "unknown")
        active_agents = state.get("active_agents", 0)
        updated_at = state.get("updated_at", "")
        feishu_state = state.get("platforms", {}).get("feishu", {}).get("state", "unknown")

        # 计算状态文件的"年龄"
        age_s = float("inf")
        if updated_at:
            try:
                if updated_at.endswith("Z"):
                    updated_at_p = updated_at[:-1] + "+00:00"
                else:
                    updated_at_p = updated_at
                dt = datetime.fromisoformat(updated_at_p)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                age_s = (datetime.now(timezone.utc) - dt).total_seconds()
            except Exception:
                pass

        age_str = f"{age_s:.0f}s 前" if age_s < float("inf") else "未知"
        check("gateway_state", gw_state == "running",
              f"状态={gw_state} 最后更新={age_str} 活跃agent={active_agents}",
              critical=gw_state != "running")
        check("飞书连接", feishu_state == "connected",
              f"飞书状态={feishu_state}",
              critical=feishu_state != "connected")

        if age_s > 300:
            check("状态新鲜度", False,
                  f"gateway_state.json 已 {age_s:.0f}s 未更新（>5min），网关可能卡死")
        else:
            check("状态新鲜度", True, f"上次更新 {age_s:.0f}s 前，正常")
    except Exception as e:
        check("gateway_state.json", False, f"读取失败: {e}", critical=True)
else:
    check("gateway_state.json", False, "文件不存在", critical=True)

# ── 3. 去重缓存检查 ────────────────────────────────────────────────────────────
print("\n【3】去重缓存检查")
dedup_file = HERMES_HOME / "feishu_seen_message_ids.json"
if dedup_file.exists():
    try:
        dedup = json.loads(dedup_file.read_text(encoding="utf-8"))
        ids = dedup.get("message_ids", {})
        now = time.time()
        expired = sum(1 for v in ids.values() if now - v >= 86400)
        active_count = len(ids) - expired
        check("去重缓存", True,
              f"共 {len(ids)} 条记录，{active_count} 条活跃，{expired} 条过期（24h内）")
        if expired > 0:
            print(f"  {INFO} 可用 'python feishu_watchdog.py --dry-run' 检查后运行清理")
    except Exception as e:
        check("去重缓存", False, f"读取失败: {e}")
else:
    check("去重缓存", True, "文件不存在（首次运行正常）")

# ── 4. 日志检查 ────────────────────────────────────────────────────────────────
print("\n【4】日志检查")
log_dir = HERMES_HOME / "logs"
interrupt_log = HERMES_HOME / "interrupt_debug.log"

if log_dir.exists():
    log_files = sorted(log_dir.glob("gateway_*.log"), key=lambda f: f.stat().st_mtime, reverse=True)
    if log_files:
        latest = log_files[0]
        age = time.time() - latest.stat().st_mtime
        check("网关日志", True, f"最新日志: {latest.name} ({age:.0f}s 前)")
        # 读取最后20行找错误
        try:
            lines = latest.read_text(encoding="utf-8", errors="replace").splitlines()
            errors = [l for l in lines[-100:] if "ERROR" in l or "CRITICAL" in l or "exception" in l.lower()]
            if errors:
                print(f"  {WARN} 最近错误日志（最多3条）:")
                for e_line in errors[-3:]:
                    print(f"       {e_line.strip()[:120]}")
            else:
                print(f"  {INFO} 最近100行未发现错误日志")
        except Exception:
            pass
    else:
        check("网关日志", False, "logs/ 目录为空，建议使用 启动飞书网关_稳定版.bat")
else:
    check("网关日志", False, "logs/ 目录不存在，建议使用 启动飞书网关_稳定版.bat")

if interrupt_log.exists():
    try:
        lines = interrupt_log.read_text(encoding="utf-8").splitlines()
        if lines:
            last = lines[-1]
            print(f"  {INFO} 最后中断日志: {last.strip()[:100]}")
    except Exception:
        pass

# ── 5. Python 环境检查 ─────────────────────────────────────────────────────────
print("\n【5】依赖检查")
deps = ["lark_oapi", "aiohttp", "anthropic", "deepseek", "openai", "dotenv", "yaml"]
for dep in deps:
    import importlib.util
    real_name = {"dotenv": "python_dotenv", "yaml": "pyyaml"}.get(dep, dep)
    found = importlib.util.find_spec(dep.replace("-", "_"))
    check(dep, found is not None, "已安装" if found else "未安装 → 可能影响运行")

# ── 汇总 ───────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
if issues:
    print(f" 严重问题 ({len(issues)} 个):")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")
if warnings:
    print(f" 警告 ({len(warnings)} 个):")
    for i, w in enumerate(warnings, 1):
        print(f"  {i}. {w}")
if not issues and not warnings:
    print(" 所有检查通过！网关配置正常。")
    print(" 若仍有问题，请检查网关日志中的 'Dropping' 关键词。")

print("\n【快速修复建议】")
print("  1. 使用 '启动飞书网关_稳定版.bat' 启动（自带日志+自动清理）")
print("  2. 使用 'python feishu_watchdog.py' 后台监控（自动重启卡死的网关）")
print("  3. 查看实时日志: C:\\Users\\%USERNAME%\\.hermes\\logs\\")
print("  4. 群消息不回复? 在 .env 添加: FEISHU_BOT_OPEN_ID=<你的bot open_id>")
print("  5. 私信不回复? 确认 FEISHU_ALLOW_ALL_USERS=true 已设置")
print("=" * 60)
