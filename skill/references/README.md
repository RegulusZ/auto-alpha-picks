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

# 4. 标记邮件已分析（下次自动跳过）
python3 scripts/mark.py --email-id=50
```

## 架构

```
fetch.py → agent LLM 判断 → notify.py → mark.py → 微信
                              ↓
                        状态机：已分析邮件不重复拉取
```

## scripts/ 脚本说明

| 脚本 | 作用 |
|------|------|
| `fetch.py` | 获取最新未分析邮件，按 email_id 过滤已处理邮件 |
| `notify.py` | 发送微信信号通知，支持去重 |
| `mark.py` | 标记邮件已分析完毕，更新状态 |
| `logger.py` | 共享日志模块 |

## 通知格式

| 信号 | 内容 |
|------|------|
| BUY | `📈 **Alpha Picks**\n🟢 **BUY** LITE` |
| SELL | `📈 **Alpha Picks**\n🔴 **SELL** POWL` |

## 去重

- 邮件去重：`fetch.py` 按 email_id 跳过已分析邮件
- 通知去重：同一 `{ticker}:{signal}` 组合只通知一次
- `--force` 强制重新发送

## 调用日志

`~/.openclaw/logs/seeking-alpha-picks.log` 记录每次调用。

## 部署

```bash
./install.sh
```

将 skill 部署到 `~/.openclaw/skills/seeking-alpha-picks/`。
