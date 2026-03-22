"""
邮件监听服务 - 独立运行的后台服务

功能：
- 持续监听邮箱，检查新邮件
- 收到新邮件后保存到待处理队列
- 供 orchestrator 启动时读取

使用方式：
    python email_service.py --password "主密码"

    # Windows 后台运行（无窗口）
    pythonw email_service.py --password "主密码"

    # Linux 后台运行
    nohup python email_service.py --password "主密码" &
"""

import os
import sys
import json
import time
import signal
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from threading import Event

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import config_manager, whitelist_manager, LogWriter
from receiver import EmailReceiver, EmailMessage
from parser import wrap_email_for_orchestrator, RawEmail

# 配置
PENDING_FILE = Path(__file__).parent / "config" / "pending_emails.json"
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "email_service.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class EmailQueue:
    """待处理邮件队列"""

    def __init__(self):
        self._file = PENDING_FILE
        self._ensure_file()

    def _ensure_file(self):
        """确保文件存在"""
        if not self._file.exists():
            self._file.parent.mkdir(parents=True, exist_ok=True)
            self._save([])

    def _load(self) -> List[Dict[str, Any]]:
        """加载队列"""
        try:
            with open(self._file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save(self, data: List[Dict[str, Any]]) -> None:
        """保存队列"""
        with open(self._file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add(self, email: RawEmail) -> None:
        """添加邮件到队列"""
        queue = self._load()

        # 检查是否已存在（避免重复）
        for item in queue:
            if item["email_id"] == email.email_id:
                logger.debug(f"邮件已存在于队列: {email.email_id}")
                return

        queue.append(email.to_dict())
        self._save(queue)
        logger.info(f"邮件已添加到队列: {email.subject}")

    def get_all(self) -> List[Dict[str, Any]]:
        """获取所有待处理邮件"""
        return self._load()

    def clear_processed(self, email_ids: List[str]) -> None:
        """清除已处理的邮件"""
        queue = self._load()
        queue = [item for item in queue if item["email_id"] not in email_ids]
        self._save(queue)
        logger.info(f"已清除 {len(email_ids)} 封处理完毕的邮件")

    def count(self) -> int:
        """获取待处理邮件数量"""
        return len(self._load())


class EmailMonitorService:
    """邮件监听服务"""

    def __init__(self, agent_file_path: str | None = None):
        self.receiver: EmailReceiver = None
        self.queue = EmailQueue()
        self.running = False
        self.stop_event = Event()
        self.last_check = None
        self.log_writer = LogWriter(agent_file_path)

    def start(self) -> None:
        """启动服务"""
        logger.info("=" * 50)
        logger.info("邮件监听服务启动")
        logger.info("=" * 50)

        # 验证配置
        if not config_manager.is_configured():
            logger.error("邮箱未配置，请先运行 setup.py")
            return

        # 验证环境变量
        if not os.getenv("EMAIL_AUTH_CODE"):
            logger.error("未设置环境变量 EMAIL_AUTH_CODE")
            return

        # 获取轮询配置
        polling_config = config_manager.get_polling_config()
        interval = polling_config.get("interval", 60)
        logger.info(f"轮询间隔: {interval} 秒")

        # 初始化接收器
        try:
            self.receiver = EmailReceiver()
        except Exception as e:
            logger.error(f"初始化邮件接收器失败: {e}")
            return

        self.running = True

        # 首次检查
        self._check_emails()

        # 主循环
        while self.running and not self.stop_event.is_set():
            try:
                # 等待下一次检查
                self.stop_event.wait(timeout=interval)

                if not self.running or self.stop_event.is_set():
                    break

                # 检查新邮件
                self._check_emails()

            except Exception as e:
                logger.error(f"检查邮件时出错: {e}")
                time.sleep(10)  # 出错后等待一下再继续

        # 清理
        self._cleanup()
        logger.info("邮件监听服务已停止")

    def stop(self) -> None:
        """停止服务"""
        logger.info("正在停止邮件监听服务...")
        self.running = False
        self.stop_event.set()

    def _check_emails(self) -> None:
        """检查新邮件"""
        try:
            # 连接邮箱
            if not self.receiver.connect():
                logger.warning("连接邮箱失败，稍后重试")
                return

            # 获取未读邮件
            messages = self.receiver.fetch_unread()
            self.last_check = datetime.now()

            if not messages:
                logger.debug("没有新邮件")
                return

            logger.info(f"发现 {len(messages)} 封未读邮件")

            # 处理每封邮件
            new_count = 0
            for msg in messages:
                # 白名单过滤
                if not whitelist_manager.is_allowed(msg.sender):
                    logger.info(f"发件人不在白名单，跳过: {msg.sender}")
                    continue

                # 获取发件人信息
                sender_info = whitelist_manager.get_sender_info(msg.sender)

                # 封装为 RawEmail
                raw_email = wrap_email_for_orchestrator(msg, sender_info)

                # 添加到队列
                self.queue.add(raw_email)
                new_count += 1

                logger.info(
                    f"新邮件入队: [{raw_email.sender_role}] {raw_email.sender_name} - {raw_email.subject}"
                )

                # 邮件保持未读状态，等待 orchestrator 处理后再标记
                # 避免邮件被处理后邮箱中已读但本地队列丢失的情况
                logger.debug(f"邮件已入队，保持未读状态: {msg.id}")

            if new_count > 0:
                logger.info(f"本次新增 {new_count} 封待处理邮件，队列共 {self.queue.count()} 封")

                # 队列写完后写入文件
                self.log_writer.write()

            # 断开连接
            self.receiver.disconnect()

        except Exception as e:
            logger.error(f"检查邮件失败: {e}")
            if self.receiver:
                self.receiver.disconnect()

    def _cleanup(self) -> None:
        """清理资源"""
        if self.receiver:
            self.receiver.disconnect()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AI安全团队邮件监听服务")
    parser.add_argument(
        "--check-once",
        action="store_true",
        help="只检查一次，不持续运行",
    )
    parser.add_argument(
        "--show-queue",
        action="store_true",
        help="显示当前待处理队列",
    )
    parser.add_argument(
        "--clear-queue",
        action="store_true",
        help="清空待处理队列",
    )
    parser.add_argument(
        "--agent",
        type=str,
        help="追加邮件日志的文件路径（文件必须存在，否则功能禁用）"
    )

    args = parser.parse_args()

    # 显示队列
    if args.show_queue:
        queue = EmailQueue()
        emails = queue.get_all()
        print(f"\n待处理邮件队列 ({len(emails)} 封):\n")
        for email in emails:
            print(f"  - [{email['sender_role']}] {email['sender_name']}: {email['subject']}")
        print()
        return

    # 清空队列
    if args.clear_queue:
        queue = EmailQueue()
        queue._save([])
        print("待处理队列已清空")
        return

    # 验证环境变量
    if not os.getenv("EMAIL_AUTH_CODE"):
        print("错误: 请设置环境变量 EMAIL_AUTH_CODE")
        sys.exit(1)

    # 创建服务
    service = EmailMonitorService(agent_file_path=args.agent)

    # 只检查一次
    if args.check_once:
        service._check_emails()
        print(f"\n当前队列: {service.queue.count()} 封待处理邮件")
        return

    # 注册信号处理（优雅退出）
    def signal_handler(signum, frame):
        logger.info(f"收到信号 {signum}，准备退出...")
        service.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Windows 不支持 SIGQUIT
    if hasattr(signal, "SIGQUIT"):
        signal.signal(signal.SIGQUIT, signal_handler)

    # 启动服务
    try:
        service.start()
    except KeyboardInterrupt:
        service.stop()


if __name__ == "__main__":
    main()
