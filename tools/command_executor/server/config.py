"""
服务端配置文件
"""
import os
from pathlib import Path

# 服务器配置
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8765"))
API_PORT = int(os.getenv("API_PORT", "8080"))

# WebSocket配置
WS_PING_INTERVAL = 30  # 心跳间隔（秒）
WS_PING_TIMEOUT = 10   # 心跳超时（秒）

# 数据库配置
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "command_executor")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# TLS配置（已启用）
# 服务端已配置TLS加密，证书位于 server/certs/
USE_TLS = os.getenv("USE_TLS", "true").lower() == "true"
TLS_CERT = os.getenv("TLS_CERT", "server/certs/server.crt")
TLS_KEY = os.getenv("TLS_KEY", "server/certs/server.key")

# 会话历史保留时间（天）
SESSION_HISTORY_RETENTION_DAYS = 90  # 服务端保留3个月

# 客户端离线自动注销配置
# 客户端离线超过此时间后，自动删除用户绑定关系（分钟）
CLIENT_OFFLINE_TIMEOUT = int(os.getenv("CLIENT_OFFLINE_TIMEOUT", "30"))  # 默认30分钟
# 定期清理离线客户端的间隔（秒）
CLIENT_CLEANUP_INTERVAL = int(os.getenv("CLIENT_CLEANUP_INTERVAL", "300"))  # 默认5分钟

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# 支持通过环境变量 LOG_DIR 指定日志目录（打包环境推荐使用绝对路径）
_log_dir_env = os.environ.get("LOG_DIR", "")
if _log_dir_env:
    LOG_DIR = Path(_log_dir_env)
else:
    LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "server.log"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5  # 保留5个备份文件
