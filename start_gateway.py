#!/usr/bin/env python3
"""
Hermes Feishu Gateway Launcher
Loads .env and starts the gateway cleanly on Windows.
"""
import os
import sys
import asyncio
import platform
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────
PROJECT_DIR = Path(r"D:\hermes_agent")
HERMES_HOME = Path.home() / ".hermes"
ENV_FILE = HERMES_HOME / ".env"

sys.path.insert(0, str(PROJECT_DIR))

# ── Load .env ────────────────────────────────────────────────
def load_env():
    if not ENV_FILE.exists():
        print(f"[WARN] .env not found at {ENV_FILE}")
        return
    with open(ENV_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())
    print(f"[OK] Loaded .env from {ENV_FILE}")

# ── Clean stale locks ────────────────────────────────────────
def clean_locks():
    lock_files = ["gateway.pid", "gateway_state.json", "feishu.lock", "gateway.lock"]
    for name in lock_files:
        p = HERMES_HOME / name
        if p.exists():
            try:
                p.unlink()
                print(f"[Clean] Removed {name}")
            except Exception:
                pass

# ── Main ─────────────────────────────────────────────────────
def main():
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUTF8"] = "1"

    print("=" * 50)
    print("  Hermes Agent - Feishu Gateway")
    print(f"  Platform: {platform.system()}")
    print("=" * 50)

    load_env()
    clean_locks()

    app_id = os.environ.get("FEISHU_APP_ID", "NOT SET")
    mode   = os.environ.get("FEISHU_CONNECTION_MODE", "websocket")
    print(f"[Info] App ID : {app_id}")
    print(f"[Info] Mode   : {mode}")
    print("[Info] Starting gateway... (Ctrl+C to stop)")
    print()

    from gateway.run import start_gateway
    asyncio.run(start_gateway())

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[Info] Gateway stopped by user.")
    except Exception as e:
        print(f"\n[Error] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
