#!/usr/bin/env python3
"""
mark.py — 标记邮件已分析完毕

fetch.py 只取比 last_analyzed_id 更大的邮件，避免重复 LLM 分析。
agent 处理完当前邮件后调用此脚本更新状态。

用法：
  python3 scripts/mark.py --email-id=51
  python3 scripts/mark.py --email-id=51 --reset   # 重置状态，重新分析所有邮件
"""
import json
import os
import sys
from pathlib import Path

# 加载 .env
_SCRIPT_DIR = Path(__file__).resolve().parent
_SKILL_DIR = _SCRIPT_DIR.parent
_ENV_FILE = _SKILL_DIR / ".env"
if _ENV_FILE.exists():
    for line in _ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k, v)

from logger import logger


def get_state_file() -> Path:
    base = os.environ.get(
        "SACP_STATE_DIR",
        os.path.expanduser("~/.openclaw/workspace/seeking-alpha-picks")
    )
    return Path(base) / "fetch_state.json"


def load_state() -> dict:
    f = get_state_file()
    if f.exists():
        try:
            return json.loads(f.read_text())
        except Exception:
            return {}
    return {}


def save_state(state: dict) -> None:
    f = get_state_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def main():
    email_id = None
    reset = False

    for arg in sys.argv[1:]:
        if arg.startswith("--email-id="):
            email_id = int(arg.split("=", 1)[1])
        elif arg == "--reset":
            reset = True

    if reset:
        state = {}
        save_state(state)
        logger.info("mark.py 重置状态")
        print("✅ 状态已重置")
        return

    if email_id is None:
        print("用法: python3 scripts/mark.py --email-id=51")
        print("      python3 scripts/mark.py --email-id=51 --reset")
        sys.exit(1)

    state = load_state()
    prev = state.get("last_analyzed_id")

    # 只更新更大的 ID，避免回退
    if prev is None or email_id > prev:
        state["last_analyzed_id"] = email_id
        save_state(state)
        logger.info("mark.py 标记已分析 | email_id=%d | prev=%s", email_id, prev)
        print(f"✅ 已标记 email_id={email_id}（上次={prev}）")
    else:
        logger.warning("mark.py 跳过（ID 未增加）| email_id=%d | last=%s", email_id, prev)
        print(f"⚠️  email_id={email_id} <= 上次={prev}，无需更新")


if __name__ == "__main__":
    main()
