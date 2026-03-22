"""
邮件接收模块

功能：
- IMAP邮件接收
- 轮询检查新邮件
- 附件下载
- 白名单过滤
"""

import os
import email
import imaplib
import threading
import logging
from email.header import decode_header
from email.utils import parseaddr
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
import time
import re

from config import config_manager, whitelist_manager

logger = logging.getLogger(__name__)

# 附件存储目录
ATTACHMENTS_DIR = Path(__file__).parent / "attachments"


@dataclass
class EmailMessage:
    """邮件消息数据类"""

    id: str
    subject: str
    sender: str
    sender_name: str
    to: List[str]
    date: datetime
    body_text: str
    body_html: Optional[str] = None
    attachments: List[Dict[str, str]] = field(default_factory=list)
    is_read: bool = False
    flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "subject": self.subject,
            "sender": self.sender,
            "sender_name": self.sender_name,
            "to": self.to,
            "date": self.date.isoformat(),
            "body_text": self.body_text,
            "body_html": self.body_html,
            "attachments": self.attachments,
            "is_read": self.is_read,
            "flags": self.flags,
        }


class EmailReceiver:
    """邮件接收器"""

    def __init__(self):
        """
        初始化邮件接收器

        注意: 需要先设置环境变量 EMAIL_AUTH_CODE
        """
        self.config = config_manager.get_email_config()
        if not self.config:
            raise ValueError("邮箱配置无效或未设置环境变量 EMAIL_AUTH_CODE")

        self._connection: Optional[imaplib.IMAP4_SSL] = None
        self._last_uid: Optional[str] = None

        # 确保附件目录存在
        ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)

    def connect(self) -> bool:
        """连接到IMAP服务器"""
        try:
            if self.config["imap_ssl"]:
                self._connection = imaplib.IMAP4_SSL(
                    self.config["imap_server"], self.config["imap_port"]
                )
            else:
                self._connection = imaplib.IMAP4(
                    self.config["imap_server"], self.config["imap_port"]
                )

            self._connection.login(self.config["address"], self.config["auth_code"])
            self._connection.select("INBOX")
            logger.info("IMAP连接成功")
            return True

        except Exception as e:
            logger.error(f"IMAP连接失败: {e}")
            self._connection = None
            return False

    def disconnect(self) -> None:
        """断开连接"""
        if self._connection:
            try:
                self._connection.close()
                self._connection.logout()
            except Exception:
                pass
            self._connection = None
            logger.info("IMAP连接已断开")

    def _ensure_connection(self) -> bool:
        """确保连接有效"""
        if not self._connection:
            return self.connect()

        try:
            # 测试连接是否有效
            self._connection.noop()
            return True
        except Exception:
            logger.warning("IMAP连接已断开，尝试重连...")
            return self.connect()

    def _decode_header_value(self, value: str) -> str:
        """解码邮件头"""
        if not value:
            return ""

        decoded_parts = decode_header(value)
        result = []
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                try:
                    if charset:
                        result.append(part.decode(charset))
                    else:
                        result.append(part.decode("utf-8", errors="ignore"))
                except Exception:
                    result.append(part.decode("utf-8", errors="ignore"))
            else:
                result.append(str(part))

        return "".join(result)

    def _get_email_body(self, msg: email.message.Message) -> tuple:
        """提取邮件正文"""
        body_text = ""
        body_html = None

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # 跳过附件
                if "attachment" in content_disposition:
                    continue

                try:
                    payload = part.get_payload(decode=True)
                    if payload is None:
                        continue

                    charset = part.get_content_charset() or "utf-8"
                    text = payload.decode(charset, errors="ignore")

                    if content_type == "text/plain" and not body_text:
                        body_text = text
                    elif content_type == "text/html":
                        body_html = text

                except Exception as e:
                    logger.warning(f"解析邮件正文失败: {e}")
        else:
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or "utf-8"
                    body_text = payload.decode(charset, errors="ignore")
            except Exception as e:
                logger.warning(f"解析邮件正文失败: {e}")

        return body_text, body_html

    def _save_attachments(
        self, msg: email.message.Message, email_id: str
    ) -> List[Dict[str, str]]:
        """保存附件"""
        attachments = []

        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition", ""))
            if "attachment" not in content_disposition:
                continue

            filename = part.get_filename()
            if not filename:
                continue

            filename = self._decode_header_value(filename)

            try:
                payload = part.get_payload(decode=True)
                if payload is None:
                    continue

                # 创建邮件专用目录
                email_dir = ATTACHMENTS_DIR / email_id
                email_dir.mkdir(parents=True, exist_ok=True)

                # 保存文件
                file_path = email_dir / filename
                with open(file_path, "wb") as f:
                    f.write(payload)

                attachments.append(
                    {
                        "filename": filename,
                        "path": str(file_path),
                        "size": len(payload),
                        "content_type": part.get_content_type(),
                    }
                )
                logger.info(f"保存附件: {filename}")

            except Exception as e:
                logger.error(f"保存附件失败: {e}")

        return attachments

    def fetch_unread(self, limit: int = 50) -> List[EmailMessage]:
        """
        获取未读邮件

        Args:
            limit: 最大获取数量

        Returns:
            邮件列表
        """
        if not self._ensure_connection():
            return []

        messages = []

        try:
            # 搜索未读邮件
            status, data = self._connection.search(None, "UNSEEN")
            if status != "OK":
                return []

            email_ids = data[0].split()
            email_ids = email_ids[:limit]  # 限制数量

            for email_id in email_ids:
                email_id_str = email_id.decode()

                # 获取邮件
                status, msg_data = self._connection.fetch(
                    email_id, "(RFC822 FLAGS)"
                )
                if status != "OK":
                    continue

                # 解析邮件
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                # 解析标志
                flags = []
                if len(msg_data) > 1:
                    flags_str = msg_data[0][0]
                    if isinstance(flags_str, bytes):
                        flags = flags_str.decode().split()

                # 提取信息
                subject = self._decode_header_value(msg.get("Subject", ""))
                sender_full = msg.get("From", "")
                sender_name, sender_email = parseaddr(sender_full)
                sender_name = self._decode_header_value(sender_name)

                # 获取收件人
                to_header = msg.get("To", "")
                to_list = [
                    parseaddr(addr)[1]
                    for addr in to_header.split(",")
                    if addr.strip()
                ]

                # 获取日期
                date_str = msg.get("Date", "")
                try:
                    from email.utils import parsedate_to_datetime

                    date = parsedate_to_datetime(date_str)
                except Exception:
                    date = datetime.now()

                # 获取正文
                body_text, body_html = self._get_email_body(msg)

                # 保存附件
                attachments = self._save_attachments(msg, email_id_str)

                # 创建邮件对象
                email_msg = EmailMessage(
                    id=email_id_str,
                    subject=subject,
                    sender=sender_email,
                    sender_name=sender_name,
                    to=to_list,
                    date=date,
                    body_text=body_text,
                    body_html=body_html,
                    attachments=attachments,
                    is_read=False,
                    flags=flags,
                )

                messages.append(email_msg)

            logger.info(f"获取到 {len(messages)} 封未读邮件")

        except Exception as e:
            logger.error(f"获取邮件失败: {e}")

        return messages

    def fetch_since_uid(self, uid: str, limit: int = 50) -> List[EmailMessage]:
        """
        获取指定UID之后的邮件

        Args:
            uid: 起始UID
            limit: 最大获取数量

        Returns:
            邮件列表
        """
        if not self._ensure_connection():
            return []

        messages = []

        try:
            # 搜索UID大于指定值的邮件
            status, data = self._connection.uid("SEARCH", None, f"UID {uid}:*")
            if status != "OK":
                return []

            email_uids = data[0].split()
            if email_uids and email_uids[0].decode() == uid:
                email_uids = email_uids[1:]  # 排除已处理的

            email_uids = email_uids[:limit]

            for uid_bytes in email_uids:
                uid_str = uid_bytes.decode()

                # 获取邮件
                status, msg_data = self._connection.uid(
                    "FETCH", uid_str, "(RFC822 FLAGS)"
                )
                if status != "OK" or not msg_data or not msg_data[0]:
                    continue

                # 解析邮件
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                # 解析标志
                flags = []
                flags_str = msg_data[0][0]
                if isinstance(flags_str, bytes):
                    flags = flags_str.decode().split()

                # 提取信息（同上）
                subject = self._decode_header_value(msg.get("Subject", ""))
                sender_full = msg.get("From", "")
                sender_name, sender_email = parseaddr(sender_full)
                sender_name = self._decode_header_value(sender_name)

                to_header = msg.get("To", "")
                to_list = [
                    parseaddr(addr)[1]
                    for addr in to_header.split(",")
                    if addr.strip()
                ]

                date_str = msg.get("Date", "")
                try:
                    from email.utils import parsedate_to_datetime

                    date = parsedate_to_datetime(date_str)
                except Exception:
                    date = datetime.now()

                body_text, body_html = self._get_email_body(msg)
                attachments = self._save_attachments(msg, uid_str)

                email_msg = EmailMessage(
                    id=uid_str,
                    subject=subject,
                    sender=sender_email,
                    sender_name=sender_name,
                    to=to_list,
                    date=date,
                    body_text=body_text,
                    body_html=body_html,
                    attachments=attachments,
                    is_read="\\Seen" in flags,
                    flags=flags,
                )

                messages.append(email_msg)

                # 更新最后UID
                self._last_uid = uid_str

            logger.info(f"获取到 {len(messages)} 封新邮件")

        except Exception as e:
            logger.error(f"获取新邮件失败: {e}")

        return messages

    def mark_as_read(self, email_id: str) -> bool:
        """标记邮件为已读"""
        if not self._ensure_connection():
            return False

        try:
            self._connection.store(email_id, "+FLAGS", "\\Seen")
            return True
        except Exception as e:
            logger.error(f"标记已读失败: {e}")
            return False

    def delete_email(self, email_id: str) -> bool:
        """删除邮件"""
        if not self._ensure_connection():
            return False

        try:
            self._connection.store(email_id, "+FLAGS", "\\Deleted")
            self._connection.expunge()
            return True
        except Exception as e:
            logger.error(f"删除邮件失败: {e}")
            return False


class EmailPoller:
    """邮件轮询器"""

    def __init__(
        self,
        receiver: EmailReceiver,
        on_new_email: Callable[[EmailMessage], None],
        filter_whitelist: bool = True,
    ):
        """
        初始化轮询器

        Args:
            receiver: 邮件接收器
            on_new_email: 新邮件回调函数
            filter_whitelist: 是否过滤白名单
        """
        self.receiver = receiver
        self.on_new_email = on_new_email
        self.filter_whitelist = filter_whitelist

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._interval = config_manager.get_polling_config().get("interval", 60)

    def start(self) -> None:
        """开始轮询"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        logger.info(f"邮件轮询已启动，间隔: {self._interval}秒")

    def stop(self) -> None:
        """停止轮询"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self.receiver.disconnect()
        logger.info("邮件轮询已停止")

    def _poll_loop(self) -> None:
        """轮询循环"""
        # 首次连接并获取最新UID
        if self.receiver.connect():
            # 获取当前最新邮件的UID作为起点
            try:
                status, data = self.receiver._connection.uid(
                    "SEARCH", None, "ALL"
                )
                if status == "OK" and data[0]:
                    uids = data[0].split()
                    if uids:
                        self.receiver._last_uid = uids[-1].decode()
                        logger.info(f"初始化最后UID: {self.receiver._last_uid}")
            except Exception as e:
                logger.warning(f"获取初始UID失败: {e}")

        while self._running:
            try:
                self._check_new_emails()
            except Exception as e:
                logger.error(f"检查新邮件出错: {e}")

            # 等待下一次轮询
            for _ in range(self._interval):
                if not self._running:
                    break
                time.sleep(1)

    def _check_new_emails(self) -> None:
        """检查新邮件"""
        if self.receiver._last_uid:
            messages = self.receiver.fetch_since_uid(self.receiver._last_uid)
        else:
            messages = self.receiver.fetch_unread()

        for msg in messages:
            # 白名单过滤
            if self.filter_whitelist:
                if not whitelist_manager.is_allowed(msg.sender):
                    logger.info(
                        f"邮件发件人不在白名单中，跳过: {msg.sender}"
                    )
                    continue

            # 获取发件人信息
            sender_info = whitelist_manager.get_sender_info(msg.sender)

            try:
                # 调用回调处理邮件
                self.on_new_email(msg, sender_info)
            except Exception as e:
                logger.error(f"处理邮件回调失败: {e}")

    def check_now(self) -> List[EmailMessage]:
        """立即检查一次"""
        messages = self.receiver.fetch_unread()
        result = []

        for msg in messages:
            if self.filter_whitelist:
                if not whitelist_manager.is_allowed(msg.sender):
                    continue
            result.append(msg)

        return result
