---
name: seeking-alpha-picks
description: "监控 Seeking Alpha Alpha Picks 邮件，agent 判断交易信号后推送企业微信通知。"
version: 6.0.0
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
fetch.py → agent LLM 判断 → notify.py（可选）→ mark.py → 微信通知
                              ↓
                        状态机：已分析邮件不重复拉取，省 token
```

agent 负责判断信号，脚本只负责获取邮件、发通知、记录状态。

## 使用方式

**第一步：获取最新邮件（自动跳过已分析过的）**

```bash
cd ~/.openclaw/skills/seeking-alpha-picks
python3 scripts/fetch.py
```

已有新邮件时输出邮件内容；无新邮件时输出 `无新邮件（全部已分析）`。

**第二步：agent 判断是否为交易信号**

判断标准：
- **BUY**：邮件提及新建仓、首次买入某只股票
- **SELL**：邮件提及卖出、清仓、减仓、获利了结某只股票

非交易信号（忽略）：市场周报（Market Recap）、投资组合调整说明、业绩报告、纯研究文章

**第三步：发送微信通知（如有信号）**

```bash
python3 scripts/notify.py --signal=BUY --ticker=LITE
```

**第四步：标记邮件已分析（必须）**

```bash
python3 scripts/mark.py --email-id=50
```

`fetch.py` 下次运行时会自动跳过 `email-id` ≤ 50 的邮件，不再重复拉取分析。

## scripts/ 脚本说明

| 脚本 | 作用 |
|------|------|
| `fetch.py` | 获取最新未分析邮件；按 email_id 过滤已处理邮件 |
| `notify.py` | 发送微信信号通知，支持去重 |
| `mark.py` | 标记邮件已分析完毕，更新状态 |
| `logger.py` | 共享日志模块 |

## 微信通知格式

| 信号 | 内容 |
|------|------|
| BUY | `📈 **Alpha Picks**\n🟢 **BUY** LITE` |
| SELL | `📈 **Alpha Picks**\n🔴 **SELL** POWL` |

## 去重机制

- **邮件去重**：`fetch.py` 按 email_id 跳过已分析邮件（`fetch_state.json`）
- **通知去重**：`notify.py` 按 `{ticker}:{signal}` 去重（`sent_signals.json`）

## 调用日志

`~/.openclaw/logs/seeking-alpha-picks.log` 记录每次调用，用于排查问题。

## 测试

```bash
# 获取指定邮件（不受状态机影响）
python3 scripts/fetch.py --email-id=45

# 强制获取所有邮件（忽略状态）
python3 scripts/fetch.py --force

# 重置状态，重新分析所有邮件
python3 scripts/mark.py --reset

# 强制发送通知
python3 scripts/notify.py --signal=BUY --ticker=LITE --force
```
