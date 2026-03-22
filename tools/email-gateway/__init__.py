"""
Email Gateway - AI Security Team 邮件网关

为 orchestrator 提供邮件收发能力
"""

from email_gateway import EmailGateway
from parser import RawEmail, wrap_email_for_orchestrator, format_raw_email
from receiver import EmailMessage

__all__ = [
    "EmailGateway",
    "RawEmail",
    "EmailMessage",
    "wrap_email_for_orchestrator",
    "format_raw_email",
]

__version__ = "1.0.0"
