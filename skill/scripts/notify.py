"""
企业微信机器人通知发送模块

支持:
1. Python 导入调用: notify_signal(), send_wecom_markdown()
2. 命令行调用（agent 使用）:
     python3 scripts/notify.py --signal=BUY --ticker=LITE
     python3 scripts/notify.py --signal=SELL --ticker=POWL
     python3 scripts/notify.py --signal=BUY --ticker=FN --force  # 强制发送（绕过去重）
"""
import json
import os
import sys
import time
import urllib.request
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class AlphaPick:
    """一条荐股数据"""
    ticker: str                    # 股票代码，如 NVDA
    entry_price: str = ""          # 进场价，如 $128.50（可选）
    current_price: Optional[str] = None   # 当前价
    gain_pct: Optional[str] = None        # 盈亏比例，如 +5.2%
    target_price: Optional[str] = None    # 目标价
    holding_period: Optional[str] = None  # 持仓周期
    thesis: str = ""                     # 荐股逻辑摘要
    article_url: Optional[str] = None      # 原文链接（不发送，仅内部记录）
    source: str = "opencli"              # 数据来源


def send_wecom_markdown(webhook_url: str, content: str) -> bool:
    """
    发送 Markdown 格式消息到企业微信群机器人
    https://developer.work.weixin.qq.com/document/path/91770
    """
    payload = json.dumps({
        "msgtype": "markdown",
        "markdown": {
            "content": content
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("errcode") == 0:
                return True
            else:
                print(f"[WECOM] 发送失败: {result}")
                return False
    except Exception as e:
        print(f"[WECOM] 请求异常: {e}")
        return False


def _strip_html(text: str) -> str:
    """去除 HTML 标签"""
    import re
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()


def _fmt_picks_summary(picks: list[AlphaPick]) -> str:
    """把多只股票格式化为一行摘要（用于组合通知）"""
    parts = []
    for p in picks:
        gain = f" {p.gain_pct}" if p.gain_pct else ""
        parts.append(f"**{p.ticker}**{gain}")
    return " | ".join(parts)


def _fmt_thesis_for_pick(pick: AlphaPick) -> str:
    """格式化单条股票的摘要文字"""
    thesis = pick.thesis or ""
    # 去除 HTML 标签
    thesis = _strip_html(thesis)
    # 截断
    if len(thesis) > 180:
        thesis = thesis[:177] + "..."
    return thesis


def format_single_notification(pick: AlphaPick, article_title: str = "") -> str:
    """
    格式化单条股票通知（用于新荐股邮件，一条股票一条通知）
    """
    date_str = datetime.now().strftime("%m-%d %H:%M")

    lines = [
        f"📈 **Alpha Picks**  `{date_str}`",
        "",
    ]

    if article_title:
        title_clean = _strip_html(article_title)
        lines.append(f"**《{title_clean}》**")
        lines.append("")

    lines.append(f"**{pick.ticker}**")

    if pick.gain_pct:
        lines.append(f"涨幅: {pick.gain_pct}")

    thesis = _fmt_thesis_for_pick(pick)
    if thesis:
        lines.append(f"摘要: {thesis}")

    return "\n".join(lines)


def format_batch_notification(picks: list[AlphaPick], article_title: str = "",
                               article_url: str = "") -> str:
    """
    格式化为一条汇总通知（推荐用法）
    微信 markdown 支持： **bold** | link显示文字 | emoji
    不支持: <b> <font> <a href> 等 HTML 标签
    """
    if not picks:
        return ""

    date_str = datetime.now().strftime("%Y-%m-%d")

    # 标题
    title_clean = _strip_html(article_title) if article_title else "Alpha Picks 最新"
    lines = [
        f"📈 **{title_clean}**",
        f"*{date_str}*",
        "",
    ]

    # 涨跌汇总行
    gain_tickers = [(p.ticker, p.gain_pct) for p in picks if p.gain_pct]
    if gain_tickers:
        gain_parts = [f"**{t}** {g}" for t, g in gain_tickers]
        lines.append("**涨跌:** " + " | ".join(gain_parts))
        lines.append("")

    # 所有 ticker 列表
    ticker_line = " | ".join([f"**{p.ticker}**" for p in picks])
    lines.append(f"**股票:** {ticker_line}")
    lines.append("")

    # 分类摘要（按上下文 group by）
    groups = {}
    for p in picks:
        # 用 thesis 前60字符作为分组键
        key = _strip_html(p.thesis or "")[:60]
        if key not in groups:
            groups[key] = []
        groups[key].append(p)

    for i, (ctx, members) in enumerate(groups.items()):
        if i >= 3:
            lines.append(f"...另有 {len(picks) - 3} 只")
            break
        tickers_str = " / ".join([f"**{p.ticker}**" for p in members])
        ctx_clean = _strip_html(ctx)
        if len(ctx_clean) > 120:
            ctx_clean = ctx_clean[:117] + "..."
        lines.append(f"• {tickers_str}: {ctx_clean}")

    return "\n".join(lines)


def notify_pick(webhook_url: str, pick: AlphaPick,
                article_title: str = "") -> bool:
    """发送单条荐股通知（保留兼容）"""
    content = format_single_notification(pick, article_title)
    print(f"[NOTIFY] 发送通知: {pick.ticker} — {pick.thesis[:40]}...")
    return send_wecom_markdown(webhook_url, content)


def notify_batch(webhook_url: str, picks: list[AlphaPick],
                 article_title: str = "", article_url: str = "") -> None:
    """
    批量发送荐股通知（合并为一条汇总消息）
    """
    if not picks:
        print("[NOTIFY] 无新荐股需要通知")
        return

    content = format_batch_notification(picks, article_title, article_url)
    print(f"[NOTIFY] 发送汇总通知 ({len(picks)} 只股票)...")
    ok = send_wecom_markdown(webhook_url, content)
    if ok:
        print(f"[NOTIFY] 发送成功")
    else:
        print(f"[NOTIFY] 发送失败")


# ---------------------------------------------------------------------------
# 信号通知（agent 使用）
# ---------------------------------------------------------------------------

def get_webhook() -> str:
    url = os.environ.get("SACP_WECOM_WEBHOOK")
    if not url:
        raise ValueError("缺少 SACP_WECOM_WEBHOOK 环境变量")
    return url


def get_state_file() -> Path:
    base = os.environ.get(
        "SACP_STATE_DIR",
        os.path.expanduser("~/.openclaw/workspace/seeking-alpha-picks")
    )
    return Path(base) / "sent_signals.json"


class SentSignalsStore:
    """幂等去重：基于 {ticker}:{signal} key 防止重复通知"""

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self._data: dict = {}
        self._load()

    def _load(self) -> None:
        if self.state_file.exists():
            try:
                self._data = json.loads(self.state_file.read_text())
            except Exception:
                self._data = {}

    def _save(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self._data, indent=2, ensure_ascii=False))

    def is_sent(self, ticker: str, signal: str) -> bool:
        return f"{ticker}:{signal}" in self._data

    def record(self, ticker: str, signal: str) -> None:
        key = f"{ticker}:{signal}"
        self._data[key] = {
            "ticker": ticker,
            "signal": signal,
            "sent_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        self._save()


def notify_signal(signal: str, ticker: str) -> bool:
    """
    发送 Alpha Picks 交易信号通知。
    返回 True 表示发送成功（已记录），False 表示失败或被去重跳过。
    """
    emoji = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "🟡"
    content = f"📈 **Alpha Picks**\n{emoji} **{signal}** {ticker}"

    webhook = get_webhook()
    ok = send_wecom_markdown(webhook, content)

    if ok:
        store = SentSignalsStore(get_state_file())
        store.record(ticker, signal)

    return ok


def main():
    signal = None
    ticker = None
    force = False

    for arg in sys.argv[1:]:
        if arg.startswith("--signal="):
            signal = arg.split("=", 1)[1].upper()
        elif arg.startswith("--ticker="):
            ticker = arg.split("=", 1)[1].upper()
        elif arg == "--force":
            force = True

    if not signal or not ticker:
        print("用法: python3 notify.py --signal=BUY --ticker=LITE [--force]")
        sys.exit(1)

    store = SentSignalsStore(get_state_file())
    key = f"{ticker}:{signal}"

    if not force and store.is_sent(ticker, signal):
        print(f"[去重] {key} 已发送过，跳过")
        return

    ok = notify_signal(signal, ticker)
    if ok:
        print(f"✅ 微信推送成功（已记录 {key}）")
    else:
        print(f"❌ 微信推送失败")


if __name__ == "__main__":
    main()
