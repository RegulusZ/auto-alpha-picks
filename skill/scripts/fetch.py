#!/usr/bin/env python3
"""
fetch.py — 获取 Seeking Alpha Alpha Picks 最新邮件内容

用法：
  python3 scripts/fetch.py              # 获取最新一封
  python3 scripts/fetch.py --email-id 40  # 获取指定邮件

输出：
  邮件主题: xxx
  邮件正文: xxx
  ---
  由 agent 判断是否为交易信号。
"""
import imaplib
import email
import re
import sys
import os
from pathlib import Path
from email.header import decode_header

# 加载 .env 文件
ENV_FILE = Path(__file__).parent.parent / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k, v)


def decode_str(s: str) -> str:
    if not s:
        return ""
    parts = decode_header(s)
    result = []
    for part, charset in parts:
        if isinstance(part, bytes):
            charset = charset or "utf-8"
            try:
                result.append(part.decode(charset, errors="replace"))
            except Exception:
                result.append(part.decode("utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)


def get_body(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                p = part.get_payload(decode=True)
                if p:
                    return p.decode(part.get_content_charset() or "utf-8", errors="replace")
    else:
        p = msg.get_payload(decode=True)
        if p:
            return p.decode(msg.get_content_charset() or "utf-8", errors="replace")
    return ""


def strip_html(html: str) -> str:
    text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&#\d+;', ' ', text)
    text = re.sub(r'&[a-z]+;', ' ', text)
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    meaningful = [l for l in lines if not any(k in l.lower() for k in [
        'unsubscribe', 'this email was sent', 'stay connected',
        'simply email', 'download our app', 'sent by seeking',
        '244 5th ave', 'new york', 'copyright',
        'box-sizing', 'margin:0', 'padding:0',
    ])]
    return re.sub(r'\s+', ' ', ' '.join(meaningful)).strip()


def fetch_email(target_id: str = None) -> tuple:
    host = os.environ.get("SACP_IMAP_HOST")
    port = int(os.environ.get("SACP_IMAP_PORT", "993"))
    user = os.environ.get("SACP_IMAP_USER")
    password = os.environ.get("SACP_IMAP_PASSWORD")

    if not all([host, user, password]):
        print("错误：缺少 IMAP 配置（检查 SACP_IMAP_HOST / SACP_IMAP_USER / SACP_IMAP_PASSWORD）")
        return None, None

    conn = imaplib.IMAP4_SSL(host, port)
    conn.login(user, password)
    conn.select("INBOX", readonly=False)

    if target_id:
        mids = [target_id]
    else:
        _, msg_ids = conn.search(None, 'FROM "subscriptions@seekingalpha.com"')
        mids = [m.decode() for m in msg_ids[0].split()] if msg_ids[0] else []
        mids.sort(key=int, reverse=True)

    if not mids:
        conn.logout()
        return None, None

    mid = mids[0]
    _, rfc_data = conn.fetch(mid.encode(),
        "(BODY.PEEK[HEADER] BODY.PEEK[TEXT])")
    rfc_bytes = b""
    if isinstance(rfc_data, list):
        for part in rfc_data:
            if isinstance(part, tuple) and len(part) >= 2:
                rfc_bytes += part[1]
            elif isinstance(part, bytes) and len(part) > 100:
                rfc_bytes += part

    msg = email.message_from_bytes(rfc_bytes) if rfc_bytes else None
    conn.logout()
    return mid, msg


def main():
    target_id = None
    for arg in sys.argv[1:]:
        if arg.startswith("--email-id"):
            target_id = arg.split("=", 1)[1] if "=" in arg else None

    mid, msg = fetch_email(target_id)
    if not mid or not msg:
        print("未找到 Seeking Alpha 邮件")
        return

    subject = decode_str(msg.get("Subject", ""))
    body = strip_html(get_body(msg))

    print(f"邮件 ID: {mid}")
    print(f"邮件主题: {subject}")
    print("=" * 60)
    print(body[:4000])
    print("=" * 60)
    print()
    print("=== Agent 判断指南 ===")
    print()
    print("【Alpha Picks 交易信号判断标准】")
    print()
    print(" BUY（买入信号）：邮件提及新建仓、首次买入某只股票")
    print(" SELL（卖出信号）：邮件提及卖出、清仓、减仓、获利了结某只股票")
    print()
    print("【非交易信号（忽略）】")
    print()
    print(" - 市场周报（Market Recap / Market Overview）")
    print(" - 投资组合调整说明（Portfolio Update）")
    print(" - 业绩报告（Earnings）")
    print(" - 纯研究文章、无交易操作的邮件")
    print()
    print("【判断后操作】")
    print()
    print(" 如有 BUY/SELL 信号，调用 notify.py 发送微信通知：")
    print("   python3 scripts/notify.py --signal=BUY --ticker=LITE")
    print("   python3 scripts/notify.py --signal=SELL --ticker=POWL")
    print()
    print(" 如无交易信号，无需任何操作。")


if __name__ == "__main__":
    main()
