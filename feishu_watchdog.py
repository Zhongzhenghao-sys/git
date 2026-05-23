#!/usr/bin/env python3
"""
Feishu Gateway Watchdog - 飞书网关自动监控与自愈
===============================================
监控 gateway_state.json 的更新时间，若超过阈值则自动重启网关。

用法:
    python feishu_watchdog.py [--interval 30] [--timeout 180] [--dry-run]

参数:
    --interval  检查间隔（秒），默认 30
    --timeout   允许无响应的最大时间（秒），默认 180（3分钟无更新则重启）
    --dry-run   仅报告，不实际重启
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

# ── 配置 ──────────────────────────────────────────────────────────────────────
HERMES_HOME = Path.home() / ".hermes"
GATEWAY_STATE_FILE = HERMES_HOME / "gateway_state.json"
GATEWAY_PID_FILE = HERMES_HOME / "gateway.pid"
LOG_DIR = HERMES_HOME / "logs"
WATCHDOG_LOG = LOG_DIR / "watchdog.log"

GATEWAY_SCRIPT = Path(__file__).parent / "start_gateway.py"
STARTUP_BAT = Path(__file__).parent / "启动飞书网关_稳定版.bat"

# ── 日志 ──────────────────────────────────────────────────────────────────────
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WATCHDOG] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(WATCHDOG_LOG, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("watchdog")


def get_gateway_pid() -> int | None:
    """从 gateway.pid 读取当前网关进程 PID"""
    if not GATEWAY_PID_FILE.exists():
        return None
    try:
        data = json.loads(GATEWAY_PID_FILE.read_text(encoding="utf-8"))
        return int(data.get("pid", 0)) or None
    except Exception:
        return None


def is_process_alive(pid: int) -> bool:
    """检查进程是否存活"""
    try:
        import ctypes
        handle = ctypes.windll.kernel32.OpenProcess(0x0400, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    except Exception:
        # 备用：tasklist 方式
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                capture_output=True, text=True, timeout=5
            )
            return str(pid) in result.stdout
        except Exception:
            return False


def get_gateway_state() -> dict | None:
    """读取网关状态文件"""
    if not GATEWAY_STATE_FILE.exists():
        return None
    try:
        return json.loads(GATEWAY_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def state_is_stale(state: dict, timeout_secs: float) -> tuple[bool, float]:
    """
    检查 gateway_state.json 是否过期。
    返回 (is_stale, age_seconds)
    """
    updated_at = state.get("updated_at", "")
    if not updated_at:
        return True, float("inf")
    try:
        # 解析 ISO 8601 时间戳
        if updated_at.endswith("Z"):
            updated_at = updated_at[:-1] + "+00:00"
        dt = datetime.fromisoformat(updated_at)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        age = (now - dt).total_seconds()
        return age > timeout_secs, age
    except Exception as e:
        logger.warning("解析 updated_at 失败: %s", e)
        return True, float("inf")


def feishu_is_connected(state: dict) -> bool:
    """检查飞书是否处于连接状态"""
    platforms = state.get("platforms", {})
    feishu = platforms.get("feishu", {})
    return feishu.get("state") == "connected"


def kill_gateway():
    """终止当前网关进程"""
    pid = get_gateway_pid()
    if pid and is_process_alive(pid):
        logger.info("终止网关进程 PID=%d", pid)
        try:
            subprocess.run(["taskkill", "/PID", str(pid), "/F", "/T"], timeout=10)
        except Exception as e:
            logger.warning("终止进程失败: %s", e)
        time.sleep(2)

    # 额外扫描所有 hermes gateway 相关进程
    try:
        result = subprocess.run(
            ["wmic", "process", "where",
             "Name='python.exe'", "get", "ProcessId,CommandLine", "/FORMAT:CSV"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.splitlines():
            if "start_gateway" in line or ("hermes_agent" in line and "gateway" in line.lower()):
                parts = line.strip().split(",")
                if len(parts) >= 2:
                    try:
                        extra_pid = int(parts[-1].strip())
                        if extra_pid != pid:
                            logger.info("终止额外网关进程 PID=%d", extra_pid)
                            subprocess.run(["taskkill", "/PID", str(extra_pid), "/F"], timeout=5)
                    except (ValueError, IndexError):
                        pass
    except Exception:
        pass


def clean_stale_files():
    """清理阻止重启的锁文件"""
    lock_files = [
        HERMES_HOME / "gateway.pid",
        HERMES_HOME / "gateway.lock",
        HERMES_HOME / "feishu.lock",
    ]
    for f in lock_files:
        if f.exists():
            try:
                f.unlink()
                logger.info("已删除锁文件: %s", f.name)
            except Exception as e:
                logger.warning("删除锁文件失败 %s: %s", f.name, e)


def restart_gateway():
    """重启网关进程"""
    logger.info("======= 开始重启网关 =======")
    kill_gateway()
    clean_stale_files()
    time.sleep(3)

    python_exe = sys.executable
    logger.info("启动命令: %s %s", python_exe, GATEWAY_SCRIPT)
    try:
        proc = subprocess.Popen(
            [python_exe, str(GATEWAY_SCRIPT)],
            cwd=str(GATEWAY_SCRIPT.parent),
            env={**os.environ, "PYTHONIOENCODING": "utf-8", "HERMES_QUIET": "1", "HERMES_EXEC_ASK": "1"},
            stdout=open(LOG_DIR / f"gateway_restart_{int(time.time())}.log", "w", encoding="utf-8"),
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )
        logger.info("网关已重启，新 PID=%d", proc.pid)
        return True
    except Exception as e:
        logger.error("重启失败: %s", e)
        return False


def check_dedup_health():
    """检查并清理过期的去重缓存"""
    dedup_file = HERMES_HOME / "feishu_seen_message_ids.json"
    if not dedup_file.exists():
        return
    try:
        data = json.loads(dedup_file.read_text(encoding="utf-8"))
        ids = data.get("message_ids", {})
        now = time.time()
        ttl = 86400  # 24h
        valid = {k: v for k, v in ids.items() if now - v < ttl}
        removed = len(ids) - len(valid)
        if removed > 0:
            dedup_file.write_text(json.dumps({"message_ids": valid}), encoding="utf-8")
            logger.info("去重缓存清理: 删除 %d 条过期记录，保留 %d 条", removed, len(valid))
    except Exception as e:
        logger.warning("去重缓存检查失败: %s", e)


def main():
    parser = argparse.ArgumentParser(description="Feishu Gateway Watchdog")
    parser.add_argument("--interval", type=float, default=30, help="检查间隔（秒）")
    parser.add_argument("--timeout", type=float, default=180, help="无响应阈值（秒）")
    parser.add_argument("--dry-run", action="store_true", help="仅报告，不重启")
    args = parser.parse_args()

    logger.info("Watchdog 启动: 检查间隔=%.0fs 超时阈值=%.0fs dry_run=%s",
                args.interval, args.timeout, args.dry_run)

    last_dedup_check = 0
    restart_count = 0

    while True:
        try:
            # 每小时检查一次去重缓存
            if time.time() - last_dedup_check > 3600:
                check_dedup_health()
                last_dedup_check = time.time()

            state = get_gateway_state()

            if state is None:
                logger.warning("gateway_state.json 不存在，网关可能未启动")
                if not args.dry_run:
                    restart_gateway()
                    restart_count += 1
                time.sleep(args.interval)
                continue

            gateway_state_str = state.get("gateway_state", "unknown")
            active_agents = state.get("active_agents", 0)
            feishu_connected = feishu_is_connected(state)
            is_stale, age = state_is_stale(state, args.timeout)

            # 正常状态下的定期日志
            if not is_stale:
                logger.debug(
                    "网关正常: state=%s feishu=%s active_agents=%d age=%.0fs",
                    gateway_state_str,
                    "connected" if feishu_connected else "disconnected",
                    active_agents,
                    age,
                )
            else:
                logger.warning(
                    "【异常】网关状态过期 %.0fs! state=%s feishu=%s active_agents=%d",
                    age, gateway_state_str,
                    "connected" if feishu_connected else "disconnected",
                    active_agents,
                )

                if args.dry_run:
                    logger.info("[DRY-RUN] 跳过重启")
                else:
                    logger.info("触发自动重启 (第 %d 次)", restart_count + 1)
                    if restart_gateway():
                        restart_count += 1
                        logger.info("重启成功，等待 60s 让网关稳定...")
                        time.sleep(60)
                        continue

            # 检查飞书连接中断
            if not feishu_connected and gateway_state_str == "running":
                logger.warning("飞书连接已断开但网关仍在运行，将在下次检查时评估")

        except KeyboardInterrupt:
            logger.info("Watchdog 手动停止")
            break
        except Exception as e:
            logger.error("Watchdog 循环异常: %s", e, exc_info=True)

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
