#!/usr/bin/env python3
"""
test_signal.py — 回归测试 & 生产检查

自动找最近一次交易信号邮件，有则发微信，无则告知。
用法：
  python3 test_signal.py              # 正常检查
  python3 test_signal.py --email-id 40  # 指定邮件 ID 测试
"""
import imaplib
import email
import re
import sys
import subprocess
import json
import time
import os
from pathlib import Path
from email.header import decode_header

# 加载 .env 文件（如有）
ENV_FILE = Path(__file__).parent / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k, v)

sys.path.insert(0, str(Path(__file__).parent))
from config import Config
from notify import send_wecom_markdown


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


def judge_with_llm(subject: str, body: str) -> dict:
    text = strip_html(body)
    prompt = (
        f"邮件主题: {subject}\n\n"
        f"邮件正文:\n{text[:2500]}\n\n"
        f"判断是否为交易信号，输出JSON（仅JSON，无其他内容）:\n"
        f'{{"signal": "BUY或SELL或null", "ticker": "大写股票代码", "reason": "原因"}}'
    )
    try:
        result = subprocess.run(
            ["claude", "-p", "--model", "haiku", "--output-format", "json"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout.strip()
        if not output:
            return {"signal": None}
        try:
            envelope = json.loads(output)
            output = envelope.get("result", output)
        except Exception:
            pass
        m = re.search(r'\{.*?"signal".*?\}', output, re.DOTALL)
        if m:
            return json.loads(m.group())
        return json.loads(output)
    except Exception:
        return {"signal": None}


def find_latest_signal(cfg: Config, target_id: int = None) -> tuple:
    """找最近交易信号邮件，返回 (mid, subject, body)"""
    conn = imaplib.IMAP4_SSL(cfg.imap_host, cfg.imap_port)
    conn.login(cfg.imap_user, cfg.imap_password)
    conn.select("INBOX", readonly=False)

    if target_id:
        mids = [str(target_id)]
    else:
        _, msg_ids = conn.search(None, 'FROM "subscriptions@seekingalpha.com"')
        mids = [m.decode() for m in msg_ids[0].split()] if msg_ids[0] else []
        mids.sort(key=int, reverse=True)

    if not mids:
        conn.logout()
        return None, None, None

    for mid in mids:
        _, rfc_data = conn.fetch(mid.encode(),
            "(BODY.PEEK[HEADER] BODY.PEEK[TEXT])")
        rfc_bytes = b""
        if isinstance(rfc_data, list):
            for part in rfc_data:
                if isinstance(part, tuple) and len(part) >= 2:
                    rfc_bytes += part[1]
                elif isinstance(part, bytes) and len(part) > 100:
                    rfc_bytes += part
        if not rfc_bytes:
            continue

        msg = email.message_from_bytes(rfc_bytes)
        subject = decode_str(msg.get("Subject", ""))
        body = get_body(msg)

        if target_id:
            conn.logout()
            return mid, subject, body

        # 自动判断
        result = judge_with_llm(subject, body)
        sig = result.get("signal")
        if sig and sig != "null":
            conn.logout()
            return mid, subject, body

    conn.logout()
    return None, None, None


def send_notification(cfg: Config, sig: str, ticker: str):
    emoji = "🟢" if sig == "BUY" else "🔴" if sig == "SELL" else "🟡"
    content = f"📈 **Alpha Picks**\n{emoji} **{sig}** {ticker}"
    return send_wecom_markdown(cfg.wecom_webhook, content)


def main():
    cfg = Config.from_env()
    target_id = None
    for arg in sys.argv[1:]:
        if arg.startswith("--email-id"):
            target_id = int(arg.split("=", 1)[1]) if "=" in arg else None

    print(f"[{time.strftime('%H:%M:%S')}] 开始检查...")

    mid, subject, body = find_latest_signal(cfg, target_id)

    if not mid or not body:
        print("未找到交易信号邮件")
        send_wecom_markdown(cfg.wecom_webhook, "📈 **Alpha Picks**\n暂无新交易信号")
        return

    result = judge_with_llm(subject, body)
    sig = result.get("signal", "null")
    ticker = result.get("ticker") or "?"

    print(f"邮件 ID: {mid}")
    print(f"邮件主题: {subject}")
    print(f"LLM 判断: {sig} | Ticker: {ticker}")

    if sig == "null" or not sig:
        print("非交易信号")
        send_wecom_markdown(cfg.wecom_webhook, "📈 **Alpha Picks**\n暂无新交易信号")
        return

    ok = send_notification(cfg, sig, ticker)
    print(f"微信推送: {'✅ 成功' if ok else '❌ 失败'}")


if __name__ == "__main__":
    main()
