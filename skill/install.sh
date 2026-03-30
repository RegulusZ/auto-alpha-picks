#!/bin/bash
# =============================================================================
# Seeking Alpha Alpha Picks Skill 部署脚本
# 将 skill/ 目录链接到 ~/.openclaw/skills/seeking-alpha-picks
# =============================================================================
set -e

SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
OPENCLAW_DIR="$HOME/.openclaw"
SKILLS_DIR="$OPENCLAW_DIR/skills"
TARGET="$SKILLS_DIR/seeking-alpha-picks"

echo "📈 Seeking Alpha Alpha Picks — 部署脚本"
echo ""

# 1. 确认 OpenClaw skills 目录存在
if [ ! -d "$SKILLS_DIR" ]; then
    echo "❌ 未找到 OpenClaw skills 目录: $SKILLS_DIR"
    exit 1
fi

# 2. 建立软链接（删除旧的重新创建）
if [ -L "$TARGET" ]; then
    echo "✅ Skill 已链接: $TARGET"
elif [ -d "$TARGET" ]; then
    echo "⚠️  目录已存在，删除后重新链接..."
    rm -rf "$TARGET"
    ln -s "$SKILL_DIR" "$TARGET"
    echo "✅ 软链接已创建: $TARGET"
else
    ln -s "$SKILL_DIR" "$TARGET"
    echo "✅ 软链接已创建: $TARGET"
fi

# 3. 注册到 openclaw.json
CONFIG_FILE="$OPENCLAW_DIR/openclaw.json"
if [ -f "$CONFIG_FILE" ]; then
    if grep -q '"seeking-alpha-picks"' "$CONFIG_FILE"; then
        echo "✅ Skill 已注册"
    else
        python3 - << 'PYEOF'
import json, os
cfg_file = os.path.expanduser("~/.openclaw/openclaw.json")
with open(cfg_file) as f:
    cfg = json.load(f)
cfg.setdefault("skills", {}).setdefault("entries", {})
cfg["skills"]["entries"]["seeking-alpha-picks"] = {"enabled": True}
with open(cfg_file, "w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
print("✅ Skill 已注册到 openclaw.json")
PYEOF
    fi
else
    echo "⚠️  未找到 openclaw.json，跳过注册"
fi

# 4. 创建状态目录
STATE_DIR="$OPENCLAW_DIR/workspace/seeking-alpha-picks"
mkdir -p "$STATE_DIR"
STATE_FILE="$STATE_DIR/sent_signals.json"
if [ ! -f "$STATE_FILE" ]; then
    echo "{}" > "$STATE_FILE"
    echo "✅ 状态文件已创建: $STATE_FILE"
else
    echo "✅ 状态文件已存在: $STATE_FILE"
fi

# 5. 确认 .env 是否已配置
ENV_FILE="$TARGET/.env"
if [ -f "$ENV_FILE" ]; then
    echo "✅ .env 已存在"
else
    if [ -f "$SKILL_DIR/.env.example" ]; then
        cp "$SKILL_DIR/.env.example" "$ENV_FILE"
        echo "⚠️  .env 已从 .env.example 复制，请编辑填入真实凭据"
    fi
fi

echo ""
echo "========================================================"
echo "✅ 部署完成"
echo "========================================================"
echo ""
echo "使用流程："
echo "  cd $TARGET"
echo "  1. python3 scripts/fetch.py              # 获取最新邮件"
echo "  2. agent 判断信号"
echo "  3. python3 scripts/notify.py --signal=BUY --ticker=LITE   # 发微信"
echo "  4. python3 scripts/mark.py --email-id=50  # 标记已分析"
echo ""
echo "测试验证："
echo "  python3 scripts/fetch.py --force           # 强制获取所有邮件"
echo "  python3 scripts/mark.py --reset            # 重置状态"
echo "  python3 scripts/notify.py --signal=BUY --ticker=TEST --force"
echo ""
