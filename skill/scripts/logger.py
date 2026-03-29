"""
调用日志模块
写入 ~/.openclaw/logs/seeking-alpha-picks.log
"""
import logging
import os
import sys
from pathlib import Path

LOG_DIR = Path(os.path.expanduser("~/.openclaw/logs"))
LOG_FILE = LOG_DIR / "seeking-alpha-picks.log"

# 确保目录存在
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("seeking-alpha-picks")
logger.setLevel(logging.INFO)

# 避免重复添加 handler
if not logger.handlers:
    handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s  %(levelname)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(handler)

    # 同时输出到 stdout（查看实时日志时有用）
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(message)s",
        datefmt="%H:%M:%S"
    ))
    logger.addHandler(stdout_handler)
