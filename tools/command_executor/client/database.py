"""
客户端本地数据库
使用SQLite存储会话历史
"""
import sqlite3
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from threading import Lock

from client.config import ConfigManager


def get_app_dir():
    """获取应用数据目录（兼容打包和开发环境）"""
    if getattr(sys, 'frozen', False):
        # 打包后的环境：使用 exe 所在目录
        return Path(sys.executable).parent
    else:
        # 开发环境：使用脚本所在目录
        return Path(__file__).parent.parent


class ClientDatabase:
    """客户端数据库管理器"""

    # 保留时间：6个月
    RETENTION_DAYS = 180

    def __init__(self):
        # 使用应用目录存储数据库
        self.db_path = get_app_dir() / "client_history.db"
        self.lock = Lock()
        self._init_database()

    def _init_database(self):
        """初始化数据库表"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    task_type TEXT NOT NULL,
                    request_data TEXT NOT NULL,
                    response_data TEXT,
                    success INTEGER NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMP NOT NULL
                )
            """)

            conn.commit()
            conn.close()

    def save_session(
        self,
        session_id: str,
        task_type: str,
        request_data: dict,
        response_data: Optional[dict],
        success: bool,
        error_message: Optional[str] = None
    ):
        """保存会话记录"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO sessions
                (session_id, task_type, request_data, response_data, success, error_message, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                task_type,
                json.dumps(request_data, ensure_ascii=False),
                json.dumps(response_data, ensure_ascii=False) if response_data else None,
                1 if success else 0,
                error_message,
                datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()

    def get_session(self, session_id: str) -> Optional[dict]:
        """获取会话记录"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT session_id, task_type, request_data, response_data, success, error_message, created_at
                FROM sessions WHERE session_id = ?
            """, (session_id,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    "session_id": row[0],
                    "task_type": row[1],
                    "request_data": json.loads(row[2]),
                    "response_data": json.loads(row[3]) if row[3] else None,
                    "success": bool(row[4]),
                    "error_message": row[5],
                    "created_at": row[6]
                }
            return None

    def get_recent_sessions(self, limit: int = 100) -> List[dict]:
        """获取最近的会话记录"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT session_id, task_type, request_data, response_data, success, error_message, created_at
                FROM sessions ORDER BY created_at DESC LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    "session_id": row[0],
                    "task_type": row[1],
                    "request_data": json.loads(row[2]),
                    "response_data": json.loads(row[3]) if row[3] else None,
                    "success": bool(row[4]),
                    "error_message": row[5],
                    "created_at": row[6]
                }
                for row in rows
            ]

    def cleanup_old_sessions(self) -> int:
        """清理过期的会话记录"""
        cutoff_date = datetime.now() - timedelta(days=self.RETENTION_DAYS)

        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM sessions WHERE created_at < ?
            """, (cutoff_date.isoformat(),))

            deleted = cursor.rowcount
            conn.commit()
            conn.close()

            return deleted


# 全局数据库实例
db = ClientDatabase()
