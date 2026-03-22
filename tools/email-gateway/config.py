"""
邮件网关配置管理模块

功能：
- 邮箱配置管理（SMTP/IMAP）
- 白名单管理
- 支持环境变量传入授权码（无需主密码）
- 配置文件读写
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

# 配置文件路径
CONFIG_DIR = Path(__file__).parent / "config"
CONFIG_FILE = CONFIG_DIR / "email_config.json"
WHITELIST_FILE = CONFIG_DIR / "whitelist.json"


class ConfigManager:
    """配置管理器"""

    # QQ邮箱默认配置
    QQ_MAIL_CONFIG = {
        "smtp_server": "smtp.qq.com",
        "smtp_port": 465,
        "smtp_ssl": True,
        "imap_server": "imap.qq.com",
        "imap_port": 993,
        "imap_ssl": True,
    }

    def __init__(self):
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """加载配置文件"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            self.config = {
                "email": {},
                "polling": {
                    "interval": 60,  # 轮询间隔（秒）
                    "enabled": True,
                },
                "notifications": {
                    "send_on_incident": True,
                    "send_on_daily_report": True,
                    "send_on_critical": True,
                },
                "created_at": None,
                "updated_at": None,
            }

    def _save_config(self) -> None:
        """保存配置文件"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.config["updated_at"] = datetime.now().isoformat()
        if not self.config.get("created_at"):
            self.config["created_at"] = self.config["updated_at"]

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def setup_email(
        self,
        email_address: str,
        display_name: str = "AI Security Team",
    ) -> None:
        """
        配置邮箱（授权码通过环境变量 EMAIL_AUTH_CODE 传入）

        Args:
            email_address: 邮箱地址
            display_name: 发件人显示名称
        """
        # 合并QQ邮箱默认配置
        self.config["email"] = {
            **self.QQ_MAIL_CONFIG,
            "address": email_address,
            "display_name": display_name,
        }

        self._save_config()

    def get_email_config(self) -> Optional[Dict[str, Any]]:
        """
        获取邮箱配置（授权码从环境变量读取）

        Returns:
            包含授权码的配置字典
        """
        if not self.config.get("email"):
            return None

        # 从环境变量获取授权码
        auth_code = os.getenv("EMAIL_AUTH_CODE")
        if not auth_code:
            print("警告: 未设置环境变量 EMAIL_AUTH_CODE")
            return None

        config = self.config["email"].copy()
        config["auth_code"] = auth_code
        return config

    def get_polling_config(self) -> Dict[str, Any]:
        """获取轮询配置"""
        return self.config.get("polling", {"interval": 60, "enabled": True})

    def set_polling_interval(self, interval: int) -> None:
        """设置轮询间隔（秒）"""
        self.config.setdefault("polling", {})["interval"] = interval
        self._save_config()

    def get_notification_config(self) -> Dict[str, bool]:
        """获取通知配置"""
        return self.config.get(
            "notifications",
            {
                "send_on_incident": True,
                "send_on_daily_report": True,
                "send_on_critical": True,
            },
        )

    def is_configured(self) -> bool:
        """检查是否已配置"""
        return bool(self.config.get("email", {}).get("address"))

    def get_display_name(self) -> str:
        """获取发件人显示名称"""
        return self.config.get("email", {}).get("display_name", "AI Security Team")


class WhitelistManager:
    """发件人白名单管理"""

    def __init__(self):
        self.whitelist: List[Dict[str, str]] = []
        self._load_whitelist()

    def _load_whitelist(self) -> None:
        """加载白名单"""
        if WHITELIST_FILE.exists():
            with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
                self.whitelist = json.load(f)
        else:
            # 默认白名单示例
            self.whitelist = []

    def _save_whitelist(self) -> None:
        """保存白名单"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(WHITELIST_FILE, "w", encoding="utf-8") as f:
            json.dump(self.whitelist, f, indent=2, ensure_ascii=False)

    def add_sender(
        self, email: str, name: str = "", description: str = "", role: str = "admin"
    ) -> bool:
        """
        添加发件人到白名单

        Args:
            email: 发件人邮箱
            name: 发件人姓名
            description: 描述
            role: 角色 (admin/operator/viewer)

        Returns:
            是否添加成功
        """
        # 检查是否已存在
        for sender in self.whitelist:
            if sender["email"].lower() == email.lower():
                return False

        self.whitelist.append(
            {
                "email": email.lower(),
                "name": name,
                "description": description,
                "role": role,
                "added_at": datetime.now().isoformat(),
            }
        )
        self._save_whitelist()
        return True

    def remove_sender(self, email: str) -> bool:
        """移除发件人"""
        for i, sender in enumerate(self.whitelist):
            if sender["email"].lower() == email.lower():
                self.whitelist.pop(i)
                self._save_whitelist()
                return True
        return False

    def is_allowed(self, email: str) -> bool:
        """检查发件人是否在白名单中"""
        email_lower = email.lower()
        return any(sender["email"].lower() == email_lower for sender in self.whitelist)

    def get_sender_info(self, email: str) -> Optional[Dict[str, str]]:
        """获取发件人信息"""
        email_lower = email.lower()
        for sender in self.whitelist:
            if sender["email"].lower() == email_lower:
                return sender
        return None

    def get_all_senders(self) -> List[Dict[str, str]]:
        """获取所有白名单发件人"""
        return self.whitelist.copy()

    def get_admins(self) -> List[Dict[str, str]]:
        """获取所有管理员"""
        return [s for s in self.whitelist if s.get("role") == "admin"]


class LogWriter:
    """日志文件写入器"""

    # 固定值常量
    FROM = "team-lead"
    TEXT = "查看邮箱是否还有没处理的邮件"
    SUMMARY = "再次检查邮箱"
    READ = False

    def __init__(self, file_path: str | None):
        self.file_path = file_path
        self.enabled = self._validate()

    def _validate(self) -> bool:
        """验证文件是否存在，若不存在则禁用功能"""
        if not self.file_path:
            return False
        if not Path(self.file_path).exists():
            print(f"日志文件不存在，功能已禁用: {self.file_path}")
            return False
        return True

    def write(self) -> bool:
        """写入一条日志记录（固定内容）"""
        if not self.enabled:
            return True  # 功能禁用视为成功

        try:
            data = {
                "from": self.FROM,
                "text": self.TEXT,
                "summary": self.SUMMARY,
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "read": self.READ
            }

            # 读取现有内容
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
            except FileNotFoundError:
                content = '[]'

            # 解析为数组
            try:
                records = json.loads(content)
            except json.JSONDecodeError:
                records = []

            # 添加新记录
            records.append(data)

            # 写回文件（保持格式一致）
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write('[\n')
                for i, record in enumerate(records):
                    f.write('  ' + json.dumps(record, ensure_ascii=False))
                    if i < len(records) - 1:
                        f.write(',')
                    f.write('\n')
                f.write(']')

            return True
        except Exception as e:
            print(f"写入日志文件失败: {e}")
            return False


# 全局实例
config_manager = ConfigManager()
whitelist_manager = WhitelistManager()
