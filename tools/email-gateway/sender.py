"""
邮件发送模块

功能：
- SMTP邮件发送
- HTML格式支持
- 附件支持
- 模板渲染
"""

import os
import smtplib
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
from email.utils import formataddr, formatdate
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

from config import config_manager

logger = logging.getLogger(__name__)

# 模板目录
TEMPLATES_DIR = Path(__file__).parent / "templates"


class EmailSender:
    """邮件发送器"""

    def __init__(self):
        """
        初始化邮件发送器

        注意: 需要先设置环境变量 EMAIL_AUTH_CODE
        """
        self.config = config_manager.get_email_config()
        if not self.config:
            raise ValueError("邮箱配置无效或未设置环境变量 EMAIL_AUTH_CODE")

        self.display_name = config_manager.get_display_name()

    def send(
        self,
        to_addresses: List[str],
        subject: str,
        content: str,
        content_type: str = "html",
        attachments: Optional[List[str]] = None,
        cc: Optional[List[str]] = None,
        priority: str = "normal",
    ) -> Dict[str, Any]:
        """
        发送邮件

        Args:
            to_addresses: 收件人列表
            subject: 邮件主题
            content: 邮件内容
            content_type: 内容类型 (html/plain)
            attachments: 附件路径列表
            cc: 抄送列表
            priority: 优先级 (high/normal/low)

        Returns:
            发送结果
        """
        try:
            # 创建邮件
            if attachments:
                msg = MIMEMultipart("mixed")
            else:
                msg = MIMEMultipart("alternative")

            # 设置邮件头
            msg["From"] = formataddr((self.display_name, self.config["address"]))
            msg["To"] = ", ".join(to_addresses)
            msg["Subject"] = subject
            msg["Date"] = formatdate(localtime=True)

            if cc:
                msg["Cc"] = ", ".join(cc)

            # 设置优先级
            if priority == "high":
                msg["X-Priority"] = "1"
            elif priority == "low":
                msg["X-Priority"] = "5"

            # 添加邮件正文
            if content_type == "html":
                msg.attach(MIMEText(content, "html", "utf-8"))
            else:
                msg.attach(MIMEText(content, "plain", "utf-8"))

            # 添加附件
            if attachments:
                for attachment_path in attachments:
                    self._add_attachment(msg, attachment_path)

            # 发送邮件
            all_recipients = to_addresses + (cc or [])

            if self.config["smtp_ssl"]:
                with smtplib.SMTP_SSL(
                    self.config["smtp_server"], self.config["smtp_port"]
                ) as server:
                    server.login(self.config["address"], self.config["auth_code"])
                    server.sendmail(
                        self.config["address"], all_recipients, msg.as_string()
                    )
            else:
                with smtplib.SMTP(
                    self.config["smtp_server"], self.config["smtp_port"]
                ) as server:
                    server.starttls()
                    server.login(self.config["address"], self.config["auth_code"])
                    server.sendmail(
                        self.config["address"], all_recipients, msg.as_string()
                    )

            logger.info(f"邮件发送成功: {subject} -> {to_addresses}")

            return {
                "success": True,
                "message": "邮件发送成功",
                "subject": subject,
                "recipients": to_addresses,
                "sent_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "subject": subject,
                "recipients": to_addresses,
            }

    def _add_attachment(self, msg: MIMEMultipart, file_path: str) -> None:
        """添加附件"""
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"附件不存在: {file_path}")
            return

        # 猜测MIME类型
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = "application/octet-stream"

        main_type, sub_type = mime_type.split("/", 1)

        with open(file_path, "rb") as f:
            if main_type == "text":
                attachment = MIMEText(f.read().decode("utf-8"), sub_type)
            elif main_type == "image":
                attachment = MIMEImage(f.read(), sub_type)
            else:
                attachment = MIMEBase(main_type, sub_type)
                attachment.set_payload(f.read())
                encoders.encode_base64(attachment)

        attachment.add_header(
            "Content-Disposition",
            "attachment",
            filename=("utf-8", "", path.name),
        )
        msg.attach(attachment)

    def send_from_template(
        self,
        to_addresses: List[str],
        template_name: str,
        context: Dict[str, Any],
        attachments: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        使用模板发送邮件

        Args:
            to_addresses: 收件人列表
            template_name: 模板名称（不带.html后缀）
            context: 模板变量
            attachments: 附件列表

        Returns:
            发送结果
        """
        template_path = TEMPLATES_DIR / f"{template_name}.html"
        if not template_path.exists():
            raise FileNotFoundError(f"模板不存在: {template_name}")

        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()

        # 简单变量替换
        content = template_content
        for key, value in context.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))

        # 从模板中提取主题（第一行以 <!-- Subject: 开头）
        subject = context.get("subject", "AI安全团队通知")
        lines = template_content.split("\n")
        for line in lines:
            if line.strip().startswith("<!-- Subject:"):
                subject = line.split("Subject:")[1].split("-->")[0].strip()
                break

        return self.send(
            to_addresses=to_addresses,
            subject=subject,
            content=content,
            content_type="html",
            attachments=attachments,
        )


class NotificationSender:
    """通知邮件发送器（预定义场景）"""

    def __init__(self, sender: EmailSender):
        self.sender = sender

    def send_incident_alert(
        self,
        to_addresses: List[str],
        incident_type: str,
        severity: str,
        description: str,
        details: Dict[str, Any],
    ) -> Dict[str, Any]:
        """发送安全事件告警"""
        severity_colors = {
            "critical": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#28a745",
        }
        severity_labels = {
            "critical": "严重",
            "high": "高",
            "medium": "中",
            "low": "低",
        }

        color = severity_colors.get(severity, "#6c757d")
        label = severity_labels.get(severity, severity)

        content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: {color}; color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">🚨 安全事件告警</h1>
            </div>
            <div style="padding: 20px; border: 1px solid #ddd;">
                <table style="width: 100%;">
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>事件类型</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{incident_type}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>严重级别</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">
                            <span style="background: {color}; color: white; padding: 3px 10px; border-radius: 3px;">{label}</span>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>发生时间</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</td>
                    </tr>
                </table>
                <h3 style="margin-top: 20px;">事件描述</h3>
                <p style="background: #f5f5f5; padding: 15px; border-radius: 5px;">{description}</p>
                <h3 style="margin-top: 20px;">详细信息</h3>
                <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto;">{json.dumps(details, indent=2, ensure_ascii=False)}</pre>
                <hr style="margin: 20px 0;">
                <p style="color: #666; font-size: 12px;">
                    此邮件由 AI 安全团队自动发送，请勿直接回复。
                </p>
            </div>
        </body>
        </html>
        """

        return self.sender.send(
            to_addresses=to_addresses,
            subject=f"[{label}] 安全事件告警 - {incident_type}",
            content=content,
            content_type="html",
            priority="high" if severity in ["critical", "high"] else "normal",
        )

    def send_daily_report(
        self,
        to_addresses: List[str],
        report_date: str,
        summary: Dict[str, Any],
        events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """发送日报"""
        events_html = ""
        for event in events[:10]:  # 只显示最近10条
            events_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{event.get('time', '-')}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{event.get('type', '-')}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{event.get('severity', '-')}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{event.get('status', '-')}</td>
            </tr>
            """

        content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #2c3e50; color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">📊 安全运维日报</h1>
                <p style="margin: 10px 0 0 0;">{report_date}</p>
            </div>
            <div style="padding: 20px; border: 1px solid #ddd;">
                <h3>今日概要</h3>
                <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                    <div style="flex: 1; min-width: 120px; background: #e3f2fd; padding: 15px; text-align: center; border-radius: 5px;">
                        <div style="font-size: 24px; font-weight: bold; color: #1976d2;">{summary.get('total_events', 0)}</div>
                        <div style="color: #666;">安全事件</div>
                    </div>
                    <div style="flex: 1; min-width: 120px; background: #fff3e0; padding: 15px; text-align: center; border-radius: 5px;">
                        <div style="font-size: 24px; font-weight: bold; color: #f57c00;">{summary.get('incidents', 0)}</div>
                        <div style="color: #666;">已处置</div>
                    </div>
                    <div style="flex: 1; min-width: 120px; background: #fce4ec; padding: 15px; text-align: center; border-radius: 5px;">
                        <div style="font-size: 24px; font-weight: bold; color: #c2185b;">{summary.get('alerts', 0)}</div>
                        <div style="color: #666;">告警数</div>
                    </div>
                </div>

                <h3 style="margin-top: 20px;">最近事件</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background: #f5f5f5;">
                        <th style="padding: 10px; text-align: left;">时间</th>
                        <th style="padding: 10px; text-align: left;">类型</th>
                        <th style="padding: 10px; text-align: left;">级别</th>
                        <th style="padding: 10px; text-align: left;">状态</th>
                    </tr>
                    {events_html}
                </table>

                <hr style="margin: 20px 0;">
                <p style="color: #666; font-size: 12px;">
                    此邮件由 AI 安全团队自动发送，请勿直接回复。
                </p>
            </div>
        </body>
        </html>
        """

        return self.sender.send(
            to_addresses=to_addresses,
            subject=f"安全运维日报 - {report_date}",
            content=content,
            content_type="html",
        )

    def send_task_notification(
        self,
        to_addresses: List[str],
        task_type: str,
        task_id: str,
        status: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """发送任务通知"""
        import json

        status_colors = {
            "completed": "#28a745",
            "in_progress": "#17a2b8",
            "failed": "#dc3545",
            "pending": "#6c757d",
        }
        status_labels = {
            "completed": "已完成",
            "in_progress": "进行中",
            "failed": "失败",
            "pending": "等待中",
        }

        color = status_colors.get(status, "#6c757d")
        label = status_labels.get(status, status)

        details_html = ""
        if details:
            details_html = f"""
            <h3 style="margin-top: 20px;">详细信息</h3>
            <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto;">{json.dumps(details, indent=2, ensure_ascii=False)}</pre>
            """

        content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #343a40; color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">📋 任务通知</h1>
            </div>
            <div style="padding: 20px; border: 1px solid #ddd;">
                <table style="width: 100%;">
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>任务类型</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{task_type}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>任务ID</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;"><code>{task_id}</code></td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>状态</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">
                            <span style="background: {color}; color: white; padding: 3px 10px; border-radius: 3px;">{label}</span>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>时间</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</td>
                    </tr>
                </table>
                <h3 style="margin-top: 20px;">消息</h3>
                <p style="background: #f5f5f5; padding: 15px; border-radius: 5px;">{message}</p>
                {details_html}
                <hr style="margin: 20px 0;">
                <p style="color: #666; font-size: 12px;">
                    此邮件由 AI 安全团队自动发送，请勿直接回复。
                </p>
            </div>
        </body>
        </html>
        """

        return self.sender.send(
            to_addresses=to_addresses,
            subject=f"[{label}] {task_type} - {task_id[:8]}",
            content=content,
            content_type="html",
            priority="high" if status == "failed" else "normal",
        )


# 导入json用于NotificationSender
import json
