"""
配置管理：读取环境变量，验证必要配置
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    # IMAP 邮件配置
    imap_host: str
    imap_port: int
    imap_user: str
    imap_password: str

    # 企业微信 Webhook
    wecom_webhook: str

    # Seeking Alpha Cookie（可选，网页抓取用）
    sa_cookie: Optional[str] = None

    # 状态文件目录
    state_dir: str = "~/.openclaw/workspace/seeking-alpha-picks"

    @classmethod
    def from_env(cls) -> "Config":
        """从环境变量加载配置，缺失时抛出明确错误"""
        required = {
            "SACP_IMAP_HOST": "IMAP 服务器地址",
            "SACP_IMAP_USER": "IMAP 用户名",
            "SACP_IMAP_PASSWORD": "IMAP 密码（建议用应用专用密码）",
            "SACP_WECOM_WEBHOOK": "企业微信机器人 Webhook 地址",
        }
        missing = [msg for key, msg in required.items() if not os.environ.get(key)]
        if missing:
            raise ValueError(
                f"缺少必要配置:\n  - " + "\n  - ".join(missing) +
                f"\n请设置上述环境变量后重试。"
            )

        port_str = os.environ.get("SACP_IMAP_PORT", "993")
        try:
            port = int(port_str)
        except ValueError:
            port = 993

        return cls(
            imap_host=os.environ["SACP_IMAP_HOST"],
            imap_port=port,
            imap_user=os.environ["SACP_IMAP_USER"],
            imap_password=os.environ["SACP_IMAP_PASSWORD"],
            wecom_webhook=os.environ["SACP_WECOM_WEBHOOK"],
            sa_cookie=os.environ.get("SACP_SA_COOKIE"),
            state_dir=os.environ.get("SACP_STATE_DIR",
                                     os.path.expanduser("~/.openclaw/workspace/seeking-alpha-picks")),
        )


def ensure_state_dir(state_dir: str) -> None:
    """确保状态目录存在"""
    import pathlib
    pathlib.Path(state_dir).mkdir(parents=True, exist_ok=True)
