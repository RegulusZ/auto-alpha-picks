---
name: seeking-alpha-picks
description: "监控 Seeking Alpha Alpha Picks 邮件，agent 判断交易信号后推送企业微信通知。"
version: 5.0.0
metadata:
  openclaw:
    requires:
      env:
        - SACP_IMAP_HOST
        - SACP_IMAP_USER
        - SACP_IMAP_PASSWORD
        - SACP_WECOM_WEBHOOK
      bins:
        - python3
    primaryEnv: SACP_WECOM_WEBHOOK
    emoji: "📈"
---

# Seeking Alpha Alpha Picks 监控

## 架构

```
fetch.py → agent 用自己的 LLM 判断信号 → notify.py → 微信通知
```

agent 负责判断，脚本只负责获取邮件内容和发微信。

## 使用方式

**第一步：获取最新邮件内容**

```bash
cd ~/.openclaw/skills/seeking-alpha-picks
python3 scripts/fetch.py
```

**第二步：agent 判断是否为交易信号**

判断标准：
- **BUY**：邮件提及新建仓、首次买入某只股票
- **SELL**：邮件提及卖出、清仓、减仓、获利了结某只股票

非交易信号（忽略）：市场周报（Market Recap）、投资组合调整说明、业绩报告、纯研究文章

**第三步：发送微信通知（如有信号）**

```bash
python3 scripts/notify.py --signal=BUY --ticker=LITE
python3 scripts/notify.py --signal=SELL --ticker=POWL
```

## scripts/ 脚本说明

| 脚本 | 作用 |
|------|------|
| `fetch.py` | 获取最新 Alpha Picks 邮件内容并打印 |
| `notify.py` | 发送微信信号通知，支持去重 |

## 微信通知格式

| 信号 | 内容 |
|------|------|
| BUY | `📈 **Alpha Picks**\n🟢 **BUY** LITE` |
| SELL | `📈 **Alpha Picks**\n🔴 **SELL** POWL` |

## 去重机制

`notify.py` 会以 `{ticker}:{signal}` 为 key 写入 `~/.openclaw/workspace/seeking-alpha-picks/sent_signals.json`，同一信号组合只通知一次。

可用 `--force` 强制重新发送：
```bash
python3 scripts/notify.py --signal=BUY --ticker=LITE --force
```

## 测试

```bash
# 获取指定邮件内容（用于测试）
python3 scripts/fetch.py --email-id=40
python3 scripts/fetch.py --email-id=45

# 强制发送通知（绕过去重）
python3 scripts/notify.py --signal=BUY --ticker=LITE --force
python3 scripts/notify.py --signal=SELL --ticker=POWL --force
```
