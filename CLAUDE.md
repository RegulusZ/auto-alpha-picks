# Seeking Alpha Alpha Picks Skill

## 项目结构

```
auto-alpha-picks/
└── skill/              ← 源码仓库根目录
    ├── test_signal.py  ← 生产入口
    ├── poll.py         ← 旧版参考
    ├── notify.py       ← 微信发送
    ├── config.py       ← .env 加载
    ├── SKILL.md        ← OpenClaw skill manifest
    ├── install.sh      ← 部署脚本
    └── .env.example    ← 环境变量模板
```

## 部署流程

skill 源码在 `skill/`，部署到 `~/.openclaw/skills/seeking-alpha-picks/`：

```bash
./install.sh
```

或手动复制：
```bash
cp -r skill ~/.openclaw/skills/seeking-alpha-picks
```

## 生产入口

```bash
cd ~/.openclaw/skills/seeking-alpha-picks
python3 test_signal.py
```

## 开发流程

- 修改源码在 `skill/` 目录
- 测试通过后 `./install.sh` 部署
- 验证用 `--email-id` 指定邮件 ID：
  - `--email-id=40` → SELL POWL
  - `--email-id=45` → BUY LITE
  - `--email-id=50` → 无信号

## 技术要点

- iCloud IMAP：`BODY.PEEK[HEADER] BODY.PEEK[TEXT]` 格式拉取邮件
- LLM 判断：`claude -p --model haiku --output-format json`
- Webhook：`--output-format json` 输出需 `envelope.get("result")` 解包
- .env：`test_signal.py` 启动时自动加载同目录 `.env`
