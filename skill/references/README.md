# Seeking Alpha Alpha Picks 监控

监控 Seeking Alpha Alpha Picks 邮件，agent 判断交易信号后推送企业微信通知。

## 快速开始

```bash
# 1. 安装依赖
cp .env.example .env
# 编辑 .env 填入 IMAP 和 Webhook 配置

# 2. 获取最新邮件
python3 scripts/fetch.py

# 3. agent 判断后，如有信号则发送通知
python3 scripts/notify.py --signal=BUY --ticker=LITE
```

## 架构

```
fetch.py → agent LLM 判断 → notify.py → 微信通知
```

agent 负责判断信号，脚本只负责获取邮件和发通知。

## scripts/ 脚本说明

| 脚本 | 作用 |
|------|------|
| `fetch.py` | 获取最新 Alpha Picks 邮件内容并打印 |
| `notify.py` | 发送微信信号通知，支持去重 |
| `logger.py` | 共享日志模块 |

## 通知格式

| 信号 | 内容 |
|------|------|
| BUY | `📈 **Alpha Picks**\n🟢 **BUY** LITE` |
| SELL | `📈 **Alpha Picks**\n🔴 **SELL** POWL` |

## 去重

同一 `{ticker}:{signal}` 组合只通知一次。`--force` 强制重新发送。

## 调用日志

`~/.openclaw/logs/seeking-alpha-picks.log` 记录每次调用，用于排查问题。

## 部署

```bash
./install.sh
```

将 skill 部署到 `~/.openclaw/skills/seeking-alpha-picks/`。
