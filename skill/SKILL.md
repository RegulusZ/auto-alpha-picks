---
name: seeking-alpha-picks
description: "监控 Seeking Alpha Alpha Picks 新邮件，自动判断交易信号并推送微信通知。"
version: 4.0.0
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
        - claude
    primaryEnv: SACP_WECOM_WEBHOOK
    emoji: "📈"
---

# Seeking Alpha Alpha Picks 监控

## 架构

```
新邮件到达 → test_signal.py 自动完成 → 微信通知
                         ↓
              LLM 判断信号类型 + ticker
              有信号 → 推送信号通知
              无信号 → 推送"暂无新交易信号"
```

## 使用方式

Agent 收到通知需求时，执行：

```bash
cd ~/.openclaw/skills/seeking-alpha-picks
python3 test_signal.py
```

无需额外判断，脚本自动完成。

## 微信通知格式

| 情况 | 通知内容 |
|------|---------|
| 有 BUY 信号 | `📈 **Alpha Picks**\n🟢 **BUY** LITE` |
| 有 SELL 信号 | `📈 **Alpha Picks**\n🔴 **SELL** POWL` |
| 无新信号 | `📈 **Alpha Picks**\n暂无新交易信号` |

## 文件说明

| 文件 | 作用 |
|------|------|
| `test_signal.py` | 生产入口：自动判断 + 推送微信 |
| `poll.py` | 旧版：打印邮件内容（已停用）|
| `notify.py` | WeChat Webhook 发送 |
| `config.py` | 环境变量 + `.env` 加载 |

## 去重机制

每次推送后以 `{ticker}:{signal}` 为 key 写入 `~/.openclaw/workspace/seeking-alpha-picks/sent_signals.json`，已记录过的信号自动跳过（幂等）。

## 测试

```bash
# 正常检查（会去重）
python3 test_signal.py

# 强制推送（绕过去重，用于重新测试）
python3 test_signal.py --force

# 指定邮件 ID 测试（绕过去重）
python3 test_signal.py --email-id=40   # SELL POWL
python3 test_signal.py --email-id=45   # BUY LITE
python3 test_signal.py --email-id=50   # Market Recap → 无信号
```
