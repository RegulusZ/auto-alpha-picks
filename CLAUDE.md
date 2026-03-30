# Seeking Alpha Alpha Picks Skill

## 项目结构

遵循 OpenClaw 官方 skill 格式：

```
auto-alpha-picks/
└── skill/
    ├── SKILL.md            ← OpenClaw manifest（必需）
    ├── install.sh          ← 部署脚本
    ├── .env.example        ← 环境变量模板
    ├── scripts/
    │   ├── fetch.py        # 获取最新未分析邮件（状态机过滤）
    │   ├── notify.py       # 发送微信信号通知
    │   ├── mark.py         # 标记邮件已分析完毕
    │   ├── logger.py       # 调用日志模块
    │   ├── poll.py         # 旧版参考（已废弃）
    │   └── test_signal.py  # 旧版一体化脚本（已废弃）
    └── references/
        └── README.md
```

## Agent 使用流程

```
fetch.py → agent LLM 判断 → notify.py（可选）→ mark.py → 微信
```

1. `python3 scripts/fetch.py` — 获取最新未分析邮件（状态机跳过旧邮件）
2. agent 用自己的 LLM 判断是否为 BUY/SELL 信号
3. `python3 scripts/notify.py --signal=BUY --ticker=LITE` — 发送微信
4. `python3 scripts/mark.py --email-id=50` — 标记邮件已分析（省 token）

## 去重

- **邮件去重**：`fetch.py` 按 email_id 跳过已分析邮件（`fetch_state.json`）
- **通知去重**：`notify.py` 按 `{ticker}:{signal}` 去重（`sent_signals.json`）
- `--force` / `--reset` 强制忽略状态

## 调用日志

`~/.openclaw/logs/seeking-alpha-picks.log` 记录每次 `fetch.py` / `notify.py` 调用，用于排查不达预期时定位问题。

## 技术要点

- iCloud IMAP：`BODY.PEEK[HEADER] BODY.PEEK[TEXT]` 格式拉取邮件
- .env：`fetch.py` 启动时自动加载同目录 `.env`
