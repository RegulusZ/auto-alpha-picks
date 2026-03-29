#!/usr/bin/env python3
"""
Seeking Alpha Alpha Picks 信号轮询

极简版：检测新邮件，打印内容，由 agent 自主判断是否交易信号并推送微信。
每次只处理最新一封邮件。
"""
import imaplib
import email
import re
import base64
import json
import sys
from pathlib import Path
from email.header import decode_header

sys.path.insert(0, str(Path(__file__).parent))
from config import Config


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
    # 去掉 style/script
    text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    # 去掉所有 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    # 去掉 HTML 实体
    text = re.sub(r'&#\d+;', ' ', text)
    text = re.sub(r'&[a-z]+;', ' ', text)
    # 去掉邮件尾部噪音
    lines = text.split('\n')
    meaningful = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        skip = any(k in line.lower() for k in [
            'unsubscribe', 'this email was sent', 'stay connected',
            'simply email', 'download our app', 'sent by seeking',
            '244 5th ave', 'new york', 'copyright',
            'box-sizing', 'margin:0', 'padding:0',
        ])
        if skip:
            continue
        meaningful.append(line)
    text = ' '.join(meaningful)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def main():
    cfg = Config.from_env()

    conn = imaplib.IMAP4_SSL(cfg.imap_host, cfg.imap_port)
    conn.login(cfg.imap_user, cfg.imap_password)
    conn.select("INBOX", readonly=False)

    # 支持命令行指定邮件 ID：python3 poll.py 40
    target_id = sys.argv[1] if len(sys.argv) > 1 else None

    if target_id:
        mids = [target_id]
    else:
        _, msg_ids = conn.search(None, 'FROM "subscriptions@seekingalpha.com"')
        mids = [m.decode() for m in msg_ids[0].split()] if msg_ids[0] else []

    if not mids:
        print("无 SA 邮件")
        conn.logout()
        return

    # 只取指定 ID 或最新一封
    mid = mids[0]

    # 取邮件内容
    _, rfc_data = conn.fetch(mid.encode(),
        "(BODY.PEEK[HEADER] BODY.PEEK[TEXT])")
    rfc_bytes = b""
    if isinstance(rfc_data, list):
        for part in rfc_data:
            if isinstance(part, tuple) and len(part) >= 2:
                rfc_bytes += part[1]
            elif isinstance(part, bytes) and len(part) > 100:
                rfc_bytes += part

    msg = email.message_from_bytes(rfc_bytes)
    subject = decode_str(msg.get("Subject", ""))
    body = strip_html(get_body(msg))

    conn.logout()

    # 打印供 agent 读取
    print("=" * 60)
    print(f"邮件主题: {subject}")
    print("=" * 60)
    print(body[:4000])
    print("=" * 60)
    print()
    print("请判断这封邮件是否包含 Seeking Alpha Alpha Picks 的交易信号。")
    print("交易信号类型：BUY（新建仓/首次买入）、SELL（卖出/清仓）、ADD（增持）、REDUCE（减仓）。")
    print("如果是交易信号，请发送微信通知，格式：📈 **Alpha Picks**\n🟢 **BUY** LITE")
    print()


if __name__ == "__main__":
    main()
