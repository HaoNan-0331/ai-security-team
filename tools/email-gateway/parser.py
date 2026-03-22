"""
邮件信息传递模块

功能：
- 将邮件原文直接传递给orchestrator
- 不做任何信息提取或处理
- orchestrator自己理解邮件内容
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from datetime import datetime

from receiver import EmailMessage


@dataclass
class RawEmail:
    """原始邮件数据 - 直接传给orchestrator"""

    email_id: str
    subject: str
    sender: str
    sender_name: str
    to: List[str]
    date: str
    body_text: str
    body_html: Optional[str]
    attachments: List[Dict[str, str]]

    # 发件人白名单信息
    sender_role: str = ""
    sender_description: str = ""

    # 原始邮箱消息ID - 用于在邮箱中标记已读
    source_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def wrap_email_for_orchestrator(
    email_msg: EmailMessage,
    sender_info: Optional[Dict] = None
) -> RawEmail:
    """
    将邮件封装为RawEmail对象

    Args:
        email_msg: 原始邮件消息
        sender_info: 发件人白名单信息

    Returns:
        RawEmail对象
    """
    return RawEmail(
        email_id=email_msg.id,
        subject=email_msg.subject,
        sender=email_msg.sender,
        sender_name=email_msg.sender_name,
        to=email_msg.to,
        date=email_msg.date.isoformat() if email_msg.date else "",
        body_text=email_msg.body_text,
        body_html=email_msg.body_html,
        attachments=email_msg.attachments,
        sender_role=sender_info.get("role", "") if sender_info else "",
        sender_description=sender_info.get("description", "") if sender_info else "",
        source_id=email_msg.id,  # 保存原始邮箱消息ID，用于在邮箱中标记已读
    )


def format_raw_email(raw: RawEmail) -> str:
    """
    将邮件格式化为纯文本，供orchestrator阅读

    Args:
        raw: RawEmail对象

    Returns:
        格式化的文本
    """
    text = f"""=== 新邮件 ===
发件人: {raw.sender_name} <{raw.sender}>
角色: {raw.sender_role or '未知'}
收件人: {', '.join(raw.to)}
主题: {raw.subject}
时间: {raw.date}
邮件ID: {raw.email_id}
"""

    if raw.sender_description:
        text += f"发件人说明: {raw.sender_description}\n"

    text += f"""
--- 正文 ---
{raw.body_text}
"""

    if raw.attachments:
        text += "\n--- 附件 ---\n"
        for att in raw.attachments:
            text += f"- {att['filename']} ({att.get('size', 0)} bytes)\n"
            text += f"  路径: {att['path']}\n"

    text += "\n=== 邮件结束 ===\n"

    return text
