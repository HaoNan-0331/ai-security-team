"""
邮件网关主程序

功能：
- 统一的邮件收发接口
- 启动时检查工作邮件（支持从队列读取）
- 运行时轮询监听新邮件
- 回调机制通知orchestrator
"""

import os
import sys
import json
import logging
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable

from config import config_manager, whitelist_manager
from sender import EmailSender, NotificationSender
from receiver import EmailReceiver, EmailPoller, EmailMessage
from parser import wrap_email_for_orchestrator, format_raw_email, RawEmail

# 配置日志
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 待处理邮件队列文件
PENDING_FILE = Path(__file__).parent / "config" / "pending_emails.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "email_gateway.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class EmailQueue:
    """待处理邮件队列（与 email_service.py 共享）"""

    def __init__(self):
        self._file = PENDING_FILE

    def _load(self) -> List[Dict[str, Any]]:
        """加载队列"""
        if not self._file.exists():
            return []
        try:
            with open(self._file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save(self, data: List[Dict[str, Any]]) -> None:
        """保存队列"""
        self._file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_all(self) -> List[Dict[str, Any]]:
        """获取所有待处理邮件"""
        return self._load()

    def clear_processed(self, email_ids: List[str]) -> None:
        """清除已处理的邮件，并清空 pending_emails.json 文件"""
        queue = self._load()
        before = len(queue)

        # 1. 从队列中移除已处理的邮件（按ID过滤）
        queue = [item for item in queue if item["email_id"] not in email_ids]
        removed_count = before - len(queue)

        # 2. 【重要】清空整个 pending_emails.json 文件
        # 这将确保下次启动时不会重复读取已处理的邮件
        self._save([])  # 保存空列表，彻底清空文件

        logger.info(f"已从队列清除 {removed_count} 封处理完毕的邮件，并清空 pending_emails.json")

    def count(self) -> int:
        """获取待处理邮件数量"""
        return len(self._load())


class EmailGateway:
    """
    邮件网关 - 为AI Security Team orchestrator提供邮件收发能力

    使用方式:
        # 先设置环境变量: set EMAIL_AUTH_CODE=你的授权码
        gateway = EmailGateway()

        # 发送邮件
        gateway.send_email(
            to=["admin@example.com"],
            subject="安全报告",
            content="..."
        )

        # 获取待处理邮件
        emails = gateway.get_queued_emails()

        # 启动轮询监听
        gateway.start_polling(on_new_email_callback)
    """

    def __init__(self):
        """
        初始化邮件网关

        注意: 需要先设置环境变量 EMAIL_AUTH_CODE
        """
        self._sender: Optional[EmailSender] = None
        self._receiver: Optional[EmailReceiver] = None
        self._poller: Optional[EmailPoller] = None
        self._notification_sender: Optional[NotificationSender] = None
        self._pending_emails: List[RawEmail] = []
        self._lock = threading.Lock()
        self._queue = EmailQueue()  # 待处理邮件队列

        # 验证配置
        if not config_manager.is_configured():
            raise RuntimeError("邮箱未配置，请先运行 setup.py 进行配置")

        # 验证环境变量
        if not os.getenv("EMAIL_AUTH_CODE"):
            raise RuntimeError("未设置环境变量 EMAIL_AUTH_CODE")

        logger.info("邮件网关初始化完成")

    def _get_sender(self) -> EmailSender:
        """获取邮件发送器（懒加载）"""
        if self._sender is None:
            self._sender = EmailSender()
        return self._sender

    def _get_receiver(self) -> EmailReceiver:
        """获取邮件接收器（懒加载）"""
        if self._receiver is None:
            self._receiver = EmailReceiver()
        return self._receiver

    # ==================== 发送功能 ====================

    def send_email(
        self,
        to: List[str],
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
            to: 收件人列表
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
            sender = self._get_sender()
            result = sender.send(
                to_addresses=to,
                subject=subject,
                content=content,
                content_type=content_type,
                attachments=attachments,
                cc=cc,
                priority=priority,
            )
            logger.info(f"发送邮件: {subject} -> {to}, 结果: {result['success']}")
            return result
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return {"success": False, "error": str(e)}

    def send_to_admins(
        self,
        subject: str,
        content: str,
        content_type: str = "html",
        attachments: Optional[List[str]] = None,
        priority: str = "normal",
    ) -> Dict[str, Any]:
        """
        发送邮件给所有管理员

        Args:
            subject: 邮件主题
            content: 邮件内容
            content_type: 内容类型
            attachments: 附件列表
            priority: 优先级

        Returns:
            发送结果
        """
        admins = whitelist_manager.get_admins()
        if not admins:
            logger.warning("白名单中没有管理员")
            return {"success": False, "error": "白名单中没有管理员"}

        admin_emails = [admin["email"] for admin in admins]
        return self.send_email(
            to=admin_emails,
            subject=subject,
            content=content,
            content_type=content_type,
            attachments=attachments,
            priority=priority,
        )

    def send_incident_alert(
        self,
        incident_type: str,
        severity: str,
        description: str,
        details: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        发送安全事件告警邮件

        Args:
            incident_type: 事件类型
            severity: 严重级别 (critical/high/medium/low)
            description: 事件描述
            details: 详细信息

        Returns:
            发送结果
        """
        try:
            sender = self._get_sender()
            notifier = NotificationSender(sender)
            admins = whitelist_manager.get_admins()
            admin_emails = [admin["email"] for admin in admins]

            return notifier.send_incident_alert(
                to_addresses=admin_emails,
                incident_type=incident_type,
                severity=severity,
                description=description,
                details=details,
            )
        except Exception as e:
            logger.error(f"发送告警邮件失败: {e}")
            return {"success": False, "error": str(e)}

    def send_daily_report(
        self,
        report_date: str,
        summary: Dict[str, Any],
        events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        发送日报邮件

        Args:
            report_date: 报告日期
            summary: 摘要数据
            events: 事件列表

        Returns:
            发送结果
        """
        try:
            sender = self._get_sender()
            notifier = NotificationSender(sender)
            admins = whitelist_manager.get_admins()
            admin_emails = [admin["email"] for admin in admins]

            return notifier.send_daily_report(
                to_addresses=admin_emails,
                report_date=report_date,
                summary=summary,
                events=events,
            )
        except Exception as e:
            logger.error(f"发送日报邮件失败: {e}")
            return {"success": False, "error": str(e)}

    # ==================== 接收功能 ====================

    def check_startup_emails(self) -> List[RawEmail]:
        """
        启动时检查未读邮件（工作安排）

        Returns:
            未读邮件列表
        """
        logger.info("检查启动时的未读邮件...")
        try:
            receiver = self._get_receiver()
            messages = receiver.fetch_unread()

            emails = []
            for msg in messages:
                # 白名单过滤
                if not whitelist_manager.is_allowed(msg.sender):
                    logger.info(f"发件人不在白名单: {msg.sender}")
                    continue

                sender_info = whitelist_manager.get_sender_info(msg.sender)
                raw_email = wrap_email_for_orchestrator(msg, sender_info)
                emails.append(raw_email)

            logger.info(f"发现 {len(emails)} 封待处理邮件")
            return emails

        except Exception as e:
            logger.error(f"检查邮件失败: {e}")
            return []

    def get_queued_emails(self) -> List[RawEmail]:
        """
        从队列获取待处理邮件（由 email_service.py 收集的邮件）

        这是 orchestrator 启动时应该调用的方法，
        读取由独立运行的 email_service.py 收集的邮件。

        Returns:
            待处理邮件列表
        """
        queued = self._queue.get_all()
        emails = []

        for item in queued:
            # 将字典转回 RawEmail 对象
            raw_email = RawEmail(
                email_id=item["email_id"],
                subject=item["subject"],
                sender=item["sender"],
                sender_name=item["sender_name"],
                to=item["to"],
                date=item["date"],
                body_text=item["body_text"],
                body_html=item.get("body_html"),
                attachments=item.get("attachments", []),
                sender_role=item.get("sender_role", ""),
                sender_description=item.get("sender_description", ""),
            )
            emails.append(raw_email)

        logger.info(f"从队列读取 {len(emails)} 封待处理邮件")
        return emails

    def mark_emails_processed(self, email_ids: List[str]) -> None:
        """
        标记邮件已处理，从队列中清除，并在邮箱中标记为已读

        Args:
            email_ids: 已处理邮件的ID列表
        """
        if not email_ids:
            return

        # 1. 从本地队列中清除
        self._queue.clear_processed(email_ids)
        logger.info(f"已从本地队列清除 {len(email_ids)} 封邮件")

        # 2. 在邮箱中标记这些邮件为已读
        try:
            receiver = self._get_receiver()
            # 从已加载的待处理邮件中找到 source_id
            for email_id in email_ids:
                # 这里需要通过某种方式获取 source_id
                # 由于 email_id 已经是 source_id (在 parser.py 中 email_id=email_msg.id)
                # 所以可以直接使用 email_id 作为 source_id
                receiver.mark_as_read(email_id)
                logger.debug(f"已在邮箱中标记邮件为已读: {email_id}")
            logger.info(f"已在邮箱中标记 {len(email_ids)} 封邮件为已读")
        except Exception as e:
            logger.error(f"在邮箱中标记邮件为已读时出错: {e}")

    def get_queue_count(self) -> int:
        """获取队列中待处理邮件数量"""
        return self._queue.count()

    def get_pending_emails(self) -> List[RawEmail]:
        """
        获取待处理的邮件

        Returns:
            待处理邮件列表
        """
        with self._lock:
            emails = self._pending_emails.copy()
            self._pending_emails.clear()
            return emails

    def has_pending_emails(self) -> bool:
        """检查是否有待处理邮件"""
        with self._lock:
            return len(self._pending_emails) > 0

    # ==================== 轮询监听 ====================

    def start_polling(
        self,
        on_new_email: Optional[Callable[[RawEmail], None]] = None
    ) -> None:
        """
        启动邮件轮询监听

        Args:
            on_new_email: 新邮件回调函数
        """
        if self._poller is not None:
            logger.warning("轮询已经在运行")
            return

        def handle_new_email(msg: EmailMessage, sender_info: Dict):
            """处理新邮件"""
            raw_email = wrap_email_for_orchestrator(msg, sender_info)

            # 添加到待处理队列
            with self._lock:
                self._pending_emails.append(raw_email)

            # 调用回调
            if on_new_email:
                try:
                    on_new_email(raw_email)
                except Exception as e:
                    logger.error(f"回调处理失败: {e}")

            logger.info(f"收到新邮件: {raw_email.subject} from {raw_email.sender}")

        receiver = self._get_receiver()
        self._poller = EmailPoller(
            receiver=receiver,
            on_new_email=handle_new_email,
            filter_whitelist=True,
        )
        self._poller.start()
        logger.info("邮件轮询已启动")

    def stop_polling(self) -> None:
        """停止轮询监听"""
        if self._poller:
            self._poller.stop()
            self._poller = None
            logger.info("邮件轮询已停止")

    def is_polling(self) -> bool:
        """检查是否正在轮询"""
        return self._poller is not None and self._poller._running

    # ==================== 便捷方法 ====================

    def format_email_text(self, raw_email: RawEmail) -> str:
        """
        将邮件格式化为文本（供orchestrator阅读）

        Args:
            raw_email: 原始邮件

        Returns:
            格式化的文本
        """
        return format_raw_email(raw_email)

    def get_whitelist_senders(self) -> List[Dict[str, str]]:
        """获取白名单发件人列表"""
        return whitelist_manager.get_all_senders()

    def add_to_whitelist(
        self,
        email: str,
        name: str = "",
        description: str = "",
        role: str = "admin"
    ) -> bool:
        """
        添加发件人到白名单

        Args:
            email: 邮箱地址
            name: 姓名
            description: 描述
            role: 角色 (admin/operator/viewer)

        Returns:
            是否添加成功
        """
        return whitelist_manager.add_sender(email, name, description, role)


# ==================== 命令行入口 ====================

def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="AI Security Team 邮件网关")
    parser.add_argument("--setup", action="store_true", help="运行配置向导")
    parser.add_argument("--check", action="store_true", help="检查未读邮件")
    parser.add_argument("--test-send", action="store_true", help="测试发送邮件")
    parser.add_argument("--password", type=str, help="主密码")

    args = parser.parse_args()

    if args.setup:
        # 运行配置向导
        os.system(f"python {Path(__file__).parent / 'setup.py'}")
        return

    if not args.password:
        print("错误: 请提供主密码 --password")
        return

    try:
        gateway = EmailGateway(args.password)

        if args.check:
            emails = gateway.check_startup_emails()
            print(f"\n发现 {len(emails)} 封待处理邮件:\n")
            for email in emails:
                print(gateway.format_email_text(email))
                print("-" * 50)

        elif args.test_send:
            admins = gateway.get_whitelist_senders()
            if admins:
                result = gateway.send_email(
                    to=[admins[0]["email"]],
                    subject="[测试] AI安全团队邮件网关测试",
                    content="<h1>测试邮件</h1><p>这是一封测试邮件，来自AI安全团队邮件网关。</p>",
                    content_type="html",
                )
                print(f"发送结果: {result}")
            else:
                print("白名单为空，无法测试发送")

    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    main()
