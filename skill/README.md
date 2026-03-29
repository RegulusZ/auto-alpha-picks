# Seeking Alpha Alpha Picks 监控

监控 Seeking Alpha Alpha Picks 邮件，新交易信号自动推送企业微信通知。

## 快速开始

```bash
# 1. 安装依赖
cp .env.example .env
# 编辑 .env 填入 IMAP 和 Webhook 配置

# 2. 运行检查
python3 test_signal.py
```

## 架构

```
新邮件 → test_signal.py → LLM 判断信号 → 微信通知
```

## 文件说明

| 文件 | 作用 |
|------|------|
| `test_signal.py` | **生产入口**：自动判断 + 推送微信 |
| `poll.py` | 旧版参考（打印邮件内容） |
| `notify.py` | 企业微信 Webhook 发送 |
| `config.py` | 环境变量加载 |
| `install.sh` | 部署脚本（复制到 `~/.openclaw/skills/`） |

## 通知格式

| 情况 | 内容 |
|------|------|
| BUY 信号 | `📈 **Alpha Picks**\n🟢 **BUY** LITE` |
| SELL 信号 | `📈 **Alpha Picks**\n🔴 **SELL** POWL` |
| 无信号 | `📈 **Alpha Picks**\n暂无新交易信号` |

## 部署

```bash
./install.sh
```

将 skill 部署到 `~/.openclaw/skills/seeking-alpha-picks/`。
