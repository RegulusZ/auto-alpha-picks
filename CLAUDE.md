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
    │   ├── fetch.py        # 获取最新 Alpha Picks 邮件内容
    │   ├── notify.py       # 发送微信信号通知
    │   ├── poll.py         # 旧版参考（已废弃）
    │   └── test_signal.py  # 旧版一体化脚本（已废弃）
    └── references/
        └── README.md
```

## Agent 使用流程

```
fetch.py → agent LLM 判断 → notify.py → 微信
```

1. `python3 scripts/fetch.py` — 获取最新邮件内容
2. agent 用自己的 LLM 判断是否为 BUY/SELL 信号
3. `python3 scripts/notify.py --signal=BUY --ticker=LITE` — 发送微信

## 去重

`notify.py` 内置 SentSignalsStore，同一 `{ticker}:{signal}` 只通知一次。`--force` 强制重新发送。

## 技术要点

- iCloud IMAP：`BODY.PEEK[HEADER] BODY.PEEK[TEXT]` 格式拉取邮件
- .env：`fetch.py` 启动时自动加载同目录 `.env`
