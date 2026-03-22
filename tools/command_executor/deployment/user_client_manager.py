#!/usr/bin/env python3
"""
用户-客户端关系管理脚本
用于查看、变更、清除、整理用户与客户端之间的绑定关系

使用方式：
    交互式模式：python user_client_manager.py interactive
    命令行模式：python user_client_manager.py <command> [options]
    查看帮助：python user_client_manager.py --help
"""

import argparse
import sys
import sqlite3
import hashlib
import secrets
import uuid as uuid_lib
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple


class UserClientManager:
    """用户-客户端关系管理器"""

    def __init__(self, db_path: str = "server/server_data.db"):
        """初始化管理器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            print(f"错误: 数据库文件不存在: {self.db_path}")
            sys.exit(1)

    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    # ==================== 查看功能 ====================

    def list_all_bindings(self, show_online: bool = False) -> List[Dict]:
        """查看所有用户-客户端绑定

        Args:
            show_online: 是否只显示在线的客户端

        Returns:
            绑定记录列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        if show_online:
            query = """
                SELECT u.username, uc.client_id, cc.hostname, cc.os_info,
                       uc.granted_at, uc.granted_by, cc.is_online
                FROM user_clients uc
                JOIN users u ON uc.user_id = u.id
                LEFT JOIN client_connections cc ON uc.client_id = cc.client_id
                WHERE cc.is_online = 1
                ORDER BY u.username, uc.granted_at
            """
        else:
            query = """
                SELECT u.username, uc.client_id, cc.hostname, cc.os_info,
                       uc.granted_at, uc.granted_by,
                       CASE WHEN cc.is_online = 1 THEN '在线' ELSE '离线' END as status
                FROM user_clients uc
                JOIN users u ON uc.user_id = u.id
                LEFT JOIN client_connections cc ON uc.client_id = cc.client_id
                ORDER BY u.username, uc.granted_at
            """

        cursor.execute(query)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def list_user_clients(self, username: str) -> List[Dict]:
        """查看指定用户的客户端列表

        Args:
            username: 用户名

        Returns:
            客户端列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT uc.client_id, cc.hostname, cc.os_info,
                   uc.granted_at, uc.granted_by,
                   CASE WHEN cc.is_online = 1 THEN '在线' ELSE '离线' END as status
            FROM user_clients uc
            JOIN users u ON uc.user_id = u.id
            LEFT JOIN client_connections cc ON uc.client_id = cc.client_id
            WHERE u.username = ?
            ORDER BY uc.granted_at
        """

        cursor.execute(query, (username,))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def list_client_users(self, client_id: str) -> List[Dict]:
        """查看指定客户端绑定的用户

        Args:
            client_id: 客户端ID

        Returns:
            用户列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT u.username, uc.granted_at, uc.granted_by,
                   cc.hostname, cc.os_info,
                   CASE WHEN cc.is_online = 1 THEN '在线' ELSE '离线' END as status
            FROM user_clients uc
            JOIN users u ON uc.user_id = u.id
            LEFT JOIN client_connections cc ON uc.client_id = cc.client_id
            WHERE uc.client_id = ?
            ORDER BY uc.granted_at
        """

        cursor.execute(query, (client_id,))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def list_online_clients(self) -> List[Dict]:
        """查看当前在线的客户端

        Returns:
            在线客户端列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT cc.client_id, cc.hostname, cc.os_info,
                   GROUP_CONCAT(u.username, ', ') as users
            FROM client_connections cc
            LEFT JOIN user_clients uc ON cc.client_id = uc.client_id
            LEFT JOIN users u ON uc.user_id = u.id
            WHERE cc.is_online = 1
            GROUP BY cc.client_id
            ORDER BY cc.client_id
        """

        cursor.execute(query)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def list_all_users(self) -> List[Dict]:
        """查看所有用户

        Returns:
            用户列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        query = "SELECT id, username, created_at FROM users ORDER BY username"
        cursor.execute(query)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def list_all_clients(self) -> List[Dict]:
        """查看所有客户端

        Returns:
            客户端列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT client_id, hostname, os_info,
                   CASE WHEN is_online = 1 THEN '在线' ELSE '离线' END as status,
                   last_seen
            FROM client_connections
            ORDER BY client_id
        """
        cursor.execute(query)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    # ==================== 变更功能 ====================

    def assign_client(self, username: str, client_id: str, granted_by: str = "admin") -> bool:
        """分配客户端给用户

        Args:
            username: 用户名
            client_id: 客户端ID
            granted_by: 操作人

        Returns:
            是否成功
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 获取用户ID
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if not user:
                print(f"错误: 用户 '{username}' 不存在")
                return False

            user_id = user[0]

            # 检查是否已经绑定
            cursor.execute("SELECT id FROM user_clients WHERE user_id = ? AND client_id = ?",
                         (user_id, client_id))
            if cursor.fetchone():
                print(f"提示: 客户端 '{client_id}' 已经绑定到用户 '{username}'")
                return True

            # 插入绑定记录
            import uuid
            cursor.execute(
                "INSERT INTO user_clients (id, user_id, client_id, granted_at, granted_by) "
                "VALUES (?, ?, ?, datetime('now'), ?)",
                (str(uuid.uuid4()), user_id, client_id, granted_by)
            )
            conn.commit()
            print(f"成功: 客户端 '{client_id}' 已分配给用户 '{username}'")
            return True

        except Exception as e:
            conn.rollback()
            print(f"错误: {e}")
            return False
        finally:
            conn.close()

    def transfer_client(self, from_user: str, to_user: str, client_id: str) -> bool:
        """转移客户端从一个用户到另一个用户

        Args:
            from_user: 原用户
            to_user: 目标用户
            client_id: 客户端ID

        Returns:
            是否成功
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 获取用户ID
            cursor.execute("SELECT id FROM users WHERE username = ?", (from_user,))
            from_user_row = cursor.fetchone()
            if not from_user_row:
                print(f"错误: 原用户 '{from_user}' 不存在")
                return False

            cursor.execute("SELECT id FROM users WHERE username = ?", (to_user,))
            to_user_row = cursor.fetchone()
            if not to_user_row:
                print(f"错误: 目标用户 '{to_user}' 不存在")
                return False

            from_user_id = from_user_row[0]
            to_user_id = to_user_row[0]

            # 检查绑定是否存在
            cursor.execute("SELECT id FROM user_clients WHERE user_id = ? AND client_id = ?",
                         (from_user_id, client_id))
            if not cursor.fetchone():
                print(f"错误: 客户端 '{client_id}' 未绑定到用户 '{from_user}'")
                return False

            # 删除旧绑定
            cursor.execute("DELETE FROM user_clients WHERE user_id = ? AND client_id = ?",
                         (from_user_id, client_id))

            # 创建新绑定
            import uuid
            cursor.execute(
                "INSERT INTO user_clients (id, user_id, client_id, granted_at, granted_by) "
                "VALUES (?, ?, ?, datetime('now'), 'transfer')",
                (str(uuid.uuid4()), to_user_id, client_id)
            )
            conn.commit()
            print(f"成功: 客户端 '{client_id}' 已从 '{from_user}' 转移到 '{to_user}'")
            return True

        except Exception as e:
            conn.rollback()
            print(f"错误: {e}")
            return False
        finally:
            conn.close()

    def batch_transfer(self, from_user: str, to_user: str) -> int:
        """批量转移所有客户端

        Args:
            from_user: 原用户
            to_user: 目标用户

        Returns:
            转移的客户端数量
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 获取用户ID
            cursor.execute("SELECT id FROM users WHERE username = ?", (from_user,))
            from_user_row = cursor.fetchone()
            if not from_user_row:
                print(f"错误: 原用户 '{from_user}' 不存在")
                return 0

            cursor.execute("SELECT id FROM users WHERE username = ?", (to_user,))
            to_user_row = cursor.fetchone()
            if not to_user_row:
                print(f"错误: 目标用户 '{to_user}' 不存在")
                return 0

            from_user_id = from_user_row[0]
            to_user_id = to_user_row[0]

            # 获取所有客户端
            cursor.execute("SELECT client_id FROM user_clients WHERE user_id = ?", (from_user_id,))
            clients = [row[0] for row in cursor.fetchall()]

            if not clients:
                print(f"提示: 用户 '{from_user}' 没有绑定的客户端")
                return 0

            # 转移每个客户端
            import uuid
            count = 0
            for client_id in clients:
                cursor.execute("DELETE FROM user_clients WHERE user_id = ? AND client_id = ?",
                             (from_user_id, client_id))
                cursor.execute(
                    "INSERT INTO user_clients (id, user_id, client_id, granted_at, granted_by) "
                    "VALUES (?, ?, ?, datetime('now'), 'batch_transfer')",
                    (str(uuid.uuid4()), to_user_id, client_id)
                )
                count += 1

            conn.commit()
            print(f"成功: 已转移 {count} 个客户端从 '{from_user}' 到 '{to_user}'")
            return count

        except Exception as e:
            conn.rollback()
            print(f"错误: {e}")
            return 0
        finally:
            conn.close()

    # ==================== 清除功能 ====================

    def remove_binding(self, username: str, client_id: str) -> bool:
        """删除指定的用户-客户端绑定

        Args:
            username: 用户名
            client_id: 客户端ID

        Returns:
            是否成功
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 获取用户ID
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if not user:
                print(f"错误: 用户 '{username}' 不存在")
                return False

            user_id = user[0]

            # 检查绑定是否存在
            cursor.execute("SELECT id FROM user_clients WHERE user_id = ? AND client_id = ?",
                         (user_id, client_id))
            if not cursor.fetchone():
                print(f"错误: 绑定关系不存在: 用户 '{username}' - 客户端 '{client_id}'")
                return False

            # 删除绑定
            cursor.execute("DELETE FROM user_clients WHERE user_id = ? AND client_id = ?",
                         (user_id, client_id))
            conn.commit()
            print(f"成功: 已删除绑定: 用户 '{username}' - 客户端 '{client_id}'")
            return True

        except Exception as e:
            conn.rollback()
            print(f"错误: {e}")
            return False
        finally:
            conn.close()

    def remove_user_all(self, username: str) -> int:
        """清除某个用户的所有绑定

        Args:
            username: 用户名

        Returns:
            删除的绑定数量
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 获取用户ID
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if not user:
                print(f"错误: 用户 '{username}' 不存在")
                return 0

            user_id = user[0]

            # 获取绑定数量
            cursor.execute("SELECT COUNT(*) FROM user_clients WHERE user_id = ?", (user_id,))
            count = cursor.fetchone()[0]

            if count == 0:
                print(f"提示: 用户 '{username}' 没有绑定的客户端")
                return 0

            # 删除所有绑定
            cursor.execute("DELETE FROM user_clients WHERE user_id = ?", (user_id,))
            conn.commit()
            print(f"成功: 已删除用户 '{username}' 的 {count} 个绑定")
            return count

        except Exception as e:
            conn.rollback()
            print(f"错误: {e}")
            return 0
        finally:
            conn.close()

    def remove_client_all(self, client_id: str) -> int:
        """清除某个客户端的所有绑定

        Args:
            client_id: 客户端ID

        Returns:
            删除的绑定数量
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 获取绑定数量
            cursor.execute("SELECT COUNT(*) FROM user_clients WHERE client_id = ?", (client_id,))
            count = cursor.fetchone()[0]

            if count == 0:
                print(f"提示: 客户端 '{client_id}' 没有绑定到任何用户")
                return 0

            # 删除所有绑定
            cursor.execute("DELETE FROM user_clients WHERE client_id = ?", (client_id,))
            conn.commit()
            print(f"成功: 已删除客户端 '{client_id}' 的 {count} 个绑定")
            return count

        except Exception as e:
            conn.rollback()
            print(f"错误: {e}")
            return 0
        finally:
            conn.close()

    # ==================== 用户管理功能 ====================

    def create_user(self, username: str, password: str) -> bool:
        """创建新用户

        Args:
            username: 用户名
            password: 密码

        Returns:
            是否成功
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 检查用户是否已存在
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                print(f"错误: 用户 '{username}' 已存在")
                return False

            # 生成密码哈希和API密钥
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            api_key = "cmd_" + secrets.token_urlsafe(32)
            user_id = str(uuid_lib.uuid4())

            # 插入用户
            cursor.execute(
                "INSERT INTO users (id, username, password_hash, api_key, is_active, created_at) "
                "VALUES (?, ?, ?, ?, 1, datetime('now'))",
                (user_id, username, password_hash, api_key)
            )
            conn.commit()
            print(f"成功: 用户 '{username}' 已创建")
            print(f"  用户ID: {user_id}")
            print(f"  API密钥: {api_key}")
            return True

        except Exception as e:
            conn.rollback()
            print(f"错误: {e}")
            return False
        finally:
            conn.close()

    def delete_user(self, username: str) -> bool:
        """删除用户

        Args:
            username: 用户名

        Returns:
            是否成功
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 获取用户ID
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if not user:
                print(f"错误: 用户 '{username}' 不存在")
                return False

            user_id = user[0]

            # 检查是否有绑定的客户端
            cursor.execute("SELECT COUNT(*) FROM user_clients WHERE user_id = ?", (user_id,))
            binding_count = cursor.fetchone()[0]

            if binding_count > 0:
                print(f"警告: 用户 '{username}' 有 {binding_count} 个绑定的客户端")
                confirm = input("是否仍然删除用户？这将同时删除所有绑定关系 (yes/no): ").strip().lower()
                if confirm != 'yes':
                    print("操作已取消")
                    return False

            # 删除用户的所有绑定
            cursor.execute("DELETE FROM user_clients WHERE user_id = ?", (user_id,))

            # 删除用户的所有Token
            cursor.execute("DELETE FROM api_tokens WHERE user_id = ?", (user_id,))

            # 删除用户
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            print(f"成功: 用户 '{username}' 已删除")
            return True

        except Exception as e:
            conn.rollback()
            print(f"错误: {e}")
            return False
        finally:
            conn.close()

    def change_password(self, username: str, new_password: str) -> bool:
        """修改用户密码

        Args:
            username: 用户名
            new_password: 新密码

        Returns:
            是否成功
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 检查用户是否存在
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if not user:
                print(f"错误: 用户 '{username}' 不存在")
                return False

            # 更新密码
            password_hash = hashlib.sha256(new_password.encode()).hexdigest()
            cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?",
                         (password_hash, username))
            conn.commit()
            print(f"成功: 用户 '{username}' 的密码已修改")
            return True

        except Exception as e:
            conn.rollback()
            print(f"错误: {e}")
            return False
        finally:
            conn.close()

    def get_user_info(self, username: str) -> Dict:
        """获取用户详细信息

        Args:
            username: 用户名

        Returns:
            用户信息字典
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT u.id, u.username, u.api_key, u.is_active, u.created_at,
                       COUNT(DISTINCT uc.client_id) as client_count
                FROM users u
                LEFT JOIN user_clients uc ON u.id = uc.user_id
                WHERE u.username = ?
                GROUP BY u.id
            """, (username,))

            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

        finally:
            conn.close()

    # ==================== 整理功能 ====================

    def cleanup_duplicates(self) -> int:
        """清理重复的绑定记录（保留最早的）"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 删除重复记录，保留rowid最小的
            cursor.execute("""
                DELETE FROM user_clients
                WHERE rowid NOT IN (
                    SELECT MIN(rowid)
                    FROM user_clients
                    GROUP BY user_id, client_id
                )
            """)
            count = cursor.rowcount
            conn.commit()
            print(f"成功: 已清理 {count} 条重复绑定记录")
            return count

        except Exception as e:
            conn.rollback()
            print(f"错误: {e}")
            return 0
        finally:
            conn.close()

    def cleanup_offline(self, days: int = 30) -> int:
        """清理离线超过指定天数的客户端绑定

        Args:
            days: 天数阈值
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 检查数据库中是否有 last_seen 字段
            cursor.execute("PRAGMA table_info(client_connections)")
            columns = [row[1] for row in cursor.fetchall()]

            if 'last_seen' not in columns:
                print("提示: 数据库中没有 last_seen 字段，无法执行离线清理")
                return 0

            # 获取离线超过指定天数的客户端
            threshold = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("""
                SELECT DISTINCT uc.client_id
                FROM user_clients uc
                JOIN client_connections cc ON uc.client_id = cc.client_id
                WHERE cc.is_online = 0
                AND datetime(cc.last_seen) < datetime(?)
            """, (threshold,))

            clients = [row[0] for row in cursor.fetchall()]

            if not clients:
                print(f"提示: 没有离线超过 {days} 天的客户端")
                return 0

            # 删除这些客户端的绑定
            count = 0
            for client_id in clients:
                cursor.execute("DELETE FROM user_clients WHERE client_id = ?", (client_id,))
                count += cursor.rowcount

            conn.commit()
            print(f"成功: 已删除 {count} 个离线超过 {days} 天的客户端绑定")
            return count

        except Exception as e:
            conn.rollback()
            print(f"错误: {e}")
            return 0
        finally:
            conn.close()


# ==================== 格式化输出 ====================

def print_table(headers: List[str], rows: List[List[str]], widths: List[int] = None):
    """打印表格

    Args:
        headers: 表头列表
        rows: 数据行列表
        widths: 列宽列表（可选）
    """
    if widths is None:
        widths = [max(len(str(row[i])) for row in [headers] + rows) + 2 for i in range(len(headers))]

    # 打印表头
    header_line = "|".join(str(h).center(w) for h, w in zip(headers, widths))
    print(header_line)
    print("-" * len(header_line))

    # 打印数据行
    for row in rows:
        print("|".join(str(cell).center(w) for cell, w in zip(row, widths)))


def print_bindings_table(bindings: List[Dict]):
    """打印绑定关系表格"""
    if not bindings:
        print("没有找到绑定记录")
        return

    headers = ["用户", "客户端ID", "主机名", "操作系统", "状态", "授权时间", "授权人"]
    rows = []
    for b in bindings:
        rows.append([
            b.get('username', '-'),
            b.get('client_id', '-'),
            b.get('hostname', '-'),
            b.get('os_info', '-'),
            b.get('status', b.get('is_online', '-')),
            b.get('granted_at', '-')[:19] if b.get('granted_at') else '-',
            b.get('granted_by', '-')
        ])

    print_table(headers, rows)


# ==================== 交互式菜单 ====================

def interactive_mode(manager: UserClientManager):
    """交互式菜单模式"""
    while True:
        print("\n" + "=" * 60)
        print("           用户-客户端关系管理工具")
        print("=" * 60)
        print()
        print("【查看功能】")
        print("  1. 查看所有绑定关系")
        print("  2. 查看指定用户的客户端")
        print("  3. 查看指定客户端的用户")
        print("  4. 查看在线客户端")
        print("  5. 查看所有用户")
        print("  6. 查看所有客户端")
        print()
        print("【用户管理】")
        print("  7. 创建新用户")
        print("  8. 删除用户")
        print("  9. 修改用户密码")
        print(" 10. 查看用户详细信息")
        print()
        print("【客户端绑定管理】")
        print(" 11. 分配客户端给用户")
        print(" 12. 转移客户端到另一用户")
        print(" 13. 批量转移所有客户端")
        print()
        print("【清除功能】")
        print(" 14. 删除指定绑定")
        print(" 15. 清除用户的所有绑定")
        print(" 16. 清除客户端的所有绑定")
        print()
        print("【整理功能】")
        print(" 17. 清理重复绑定记录")
        print(" 18. 清理离线客户端绑定")
        print()
        print("  0. 退出")
        print()

        choice = input("请选择操作 [0-18]: ").strip()

        if choice == "0":
            print("再见！")
            break

        elif choice == "1":
            print("\n=== 所有绑定关系 ===")
            bindings = manager.list_all_bindings()
            print_bindings_table(bindings)

        elif choice == "2":
            username = input("请输入用户名: ").strip()
            if username:
                print(f"\n=== 用户 '{username}' 的客户端 ===")
                bindings = manager.list_user_clients(username)
                print_bindings_table(bindings)
            else:
                print("错误: 用户名不能为空")

        elif choice == "3":
            client_id = input("请输入客户端ID: ").strip()
            if client_id:
                print(f"\n=== 客户端 '{client_id}' 的绑定用户 ===")
                bindings = manager.list_client_users(client_id)
                if bindings:
                    headers = ["用户", "授权时间", "授权人", "主机名", "状态"]
                    rows = [[
                        b.get('username', '-'),
                        b.get('granted_at', '-')[:19] if b.get('granted_at') else '-',
                        b.get('granted_by', '-'),
                        b.get('hostname', '-'),
                        b.get('status', '-')
                    ] for b in bindings]
                    print_table(headers, rows)
                else:
                    print(f"客户端 '{client_id}' 没有绑定到任何用户")
            else:
                print("错误: 客户端ID不能为空")

        elif choice == "4":
            print("\n=== 在线客户端 ===")
            clients = manager.list_online_clients()
            if clients:
                headers = ["客户端ID", "主机名", "操作系统", "绑定用户"]
                rows = [[
                    c.get('client_id', '-'),
                    c.get('hostname', '-'),
                    c.get('os_info', '-'),
                    c.get('users', '-')
                ] for c in clients]
                print_table(headers, rows)
            else:
                print("当前没有在线客户端")

        elif choice == "5":
            print("\n=== 所有用户 ===")
            users = manager.list_all_users()
            if users:
                headers = ["用户名", "创建时间"]
                rows = [[
                    u.get('username', '-'),
                    u.get('created_at', '-')[:19] if u.get('created_at') else '-'
                ] for u in users]
                print_table(headers, rows)
            else:
                print("没有找到用户")

        elif choice == "6":
            print("\n=== 所有客户端 ===")
            clients = manager.list_all_clients()
            if clients:
                headers = ["客户端ID", "主机名", "操作系统", "状态", "最后连接"]
                rows = [[
                    c.get('client_id', '-'),
                    c.get('hostname', '-'),
                    c.get('os_info', '-'),
                    c.get('status', '-'),
                    c.get('last_seen', '-')[:19] if c.get('last_seen') else '-'
                ] for c in clients]
                print_table(headers, rows)
            else:
                print("没有找到客户端")

        elif choice == "7":
            # 创建新用户
            username = input("请输入新用户名: ").strip()
            if not username:
                print("错误: 用户名不能为空")
            else:
                password = input("请输入密码: ").strip()
                if not password:
                    print("错误: 密码不能为空")
                else:
                    confirm_password = input("请再次输入密码: ").strip()
                    if password != confirm_password:
                        print("错误: 两次输入的密码不一致")
                    else:
                        manager.create_user(username, password)

        elif choice == "8":
            # 删除用户
            username = input("请输入要删除的用户名: ").strip()
            if username:
                manager.delete_user(username)
            else:
                print("错误: 用户名不能为空")

        elif choice == "9":
            # 修改用户密码
            username = input("请输入用户名: ").strip()
            if not username:
                print("错误: 用户名不能为空")
            else:
                new_password = input("请输入新密码: ").strip()
                if not new_password:
                    print("错误: 密码不能为空")
                else:
                    confirm_password = input("请再次输入新密码: ").strip()
                    if new_password != confirm_password:
                        print("错误: 两次输入的密码不一致")
                    else:
                        manager.change_password(username, new_password)

        elif choice == "10":
            # 查看用户详细信息
            username = input("请输入用户名: ").strip()
            if username:
                info = manager.get_user_info(username)
                if info:
                    print(f"\n=== 用户 '{username}' 详细信息 ===")
                    print(f"用户ID: {info.get('id', '-')}")
                    print(f"用户名: {info.get('username', '-')}")
                    print(f"API密钥: {info.get('api_key', '-')}")
                    print(f"状态: {'激活' if info.get('is_active') else '未激活'}")
                    print(f"创建时间: {info.get('created_at', '-')}")
                    print(f"绑定客户端数: {info.get('client_count', 0)}")
                else:
                    print(f"用户 '{username}' 不存在")
            else:
                print("错误: 用户名不能为空")

        elif choice == "11":
            username = input("请输入用户名: ").strip()
            client_id = input("请输入客户端ID: ").strip()
            if username and client_id:
                manager.assign_client(username, client_id)
            else:
                print("错误: 用户名和客户端ID不能为空")

        elif choice == "12":
            from_user = input("请输入原用户名: ").strip()
            to_user = input("请输入目标用户名: ").strip()
            client_id = input("请输入客户端ID: ").strip()
            if from_user and to_user and client_id:
                # 确认操作
                confirm = input(f"确认将客户端 '{client_id}' 从 '{from_user}' 转移到 '{to_user}'? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    manager.transfer_client(from_user, to_user, client_id)
                else:
                    print("操作已取消")
            else:
                print("错误: 所有参数不能为空")

        elif choice == "13":
            from_user = input("请输入原用户名: ").strip()
            to_user = input("请输入目标用户名: ").strip()
            if from_user and to_user:
                # 显示将要转移的客户端
                bindings = manager.list_user_clients(from_user)
                if bindings:
                    print(f"\n将转移以下 {len(bindings)} 个客户端:")
                    for b in bindings:
                        print(f"  - {b.get('client_id')}")
                    confirm = input(f"\n确认将所有客户端从 '{from_user}' 转移到 '{to_user}'? (yes/no): ").strip().lower()
                    if confirm == 'yes':
                        manager.batch_transfer(from_user, to_user)
                    else:
                        print("操作已取消")
                else:
                    print(f"用户 '{from_user}' 没有绑定的客户端")
            else:
                print("错误: 用户名不能为空")

        elif choice == "14":
            username = input("请输入用户名: ").strip()
            client_id = input("请输入客户端ID: ").strip()
            if username and client_id:
                confirm = input(f"确认删除绑定: 用户 '{username}' - 客户端 '{client_id}'? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    manager.remove_binding(username, client_id)
                else:
                    print("操作已取消")
            else:
                print("错误: 用户名和客户端ID不能为空")

        elif choice == "15":
            username = input("请输入用户名: ").strip()
            if username:
                bindings = manager.list_user_clients(username)
                if bindings:
                    print(f"\n将删除以下 {len(bindings)} 个绑定:")
                    for b in bindings:
                        print(f"  - {b.get('client_id')}")
                    confirm = input(f"\n确认删除用户 '{username}' 的所有绑定? (yes/no): ").strip().lower()
                    if confirm == 'yes':
                        manager.remove_user_all(username)
                    else:
                        print("操作已取消")
                else:
                    print(f"用户 '{username}' 没有绑定的客户端")
            else:
                print("错误: 用户名不能为空")

        elif choice == "16":
            client_id = input("请输入客户端ID: ").strip()
            if client_id:
                bindings = manager.list_client_users(client_id)
                if bindings:
                    print(f"\n将删除客户端 '{client_id}' 与以下 {len(bindings)} 个用户的绑定:")
                    for b in bindings:
                        print(f"  - {b.get('username')}")
                    confirm = input(f"\n确认删除客户端 '{client_id}' 的所有绑定? (yes/no): ").strip().lower()
                    if confirm == 'yes':
                        manager.remove_client_all(client_id)
                    else:
                        print("操作已取消")
                else:
                    print(f"客户端 '{client_id}' 没有绑定到任何用户")
            else:
                print("错误: 客户端ID不能为空")

        elif choice == "17":
            confirm = input("确认清理重复的绑定记录? (yes/no): ").strip().lower()
            if confirm == 'yes':
                manager.cleanup_duplicates()
            else:
                print("操作已取消")

        elif choice == "18":
            days_input = input("请输入离线天数阈值 (默认30): ").strip()
            days = int(days_input) if days_input.isdigit() else 30
            confirm = input(f"确认清理离线超过 {days} 天的客户端绑定? (yes/no): ").strip().lower()
            if confirm == 'yes':
                manager.cleanup_offline(days)
            else:
                print("操作已取消")

        else:
            print("错误: 无效的选择，请输入 0-18")

        input("\n按回车继续...")


# ==================== 命令行模式 ====================

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='用户-客户端关系管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  交互式模式:
    python user_client_manager.py interactive

  查看所有绑定:
    python user_client_manager.py list
    python user_client_manager.py list --online

  查看指定用户的客户端:
    python user_client_manager.py list-user --username dzj

  查看指定客户端的用户:
    python user_client_manager.py list-client --client-id 5B15DB0C

  查看用户详细信息:
    python user_client_manager.py user-info --username dzj

  创建用户:
    python user_client_manager.py create-user testuser password123

  删除用户:
    python user_client_manager.py delete-user testuser

  修改密码:
    python user_client_manager.py change-password testuser newpass123

  分配客户端:
    python user_client_manager.py assign dzj 5B15DB0C

  转移客户端:
    python user_client_manager.py transfer dzj testuser 5B15DB0C

  批量转移:
    python user_client_manager.py batch-transfer dzj testuser

  删除绑定:
    python user_client_manager.py remove dzj 5B15DB0C

  清除用户所有绑定:
    python user_client_manager.py remove-user-bindings dzj

  清除客户端所有绑定:
    python user_client_manager.py remove-client-bindings 5B15DB0C

  清理重复:
    python user_client_manager.py cleanup --duplicates

  清理离线:
    python user_client_manager.py cleanup --offline --days 30
        """
    )

    parser.add_argument('command', nargs='?', help='要执行的命令')
    parser.add_argument('args', nargs=argparse.REMAINDER, help='命令参数')
    parser.add_argument('--db', default='server/server_data.db', help='数据库文件路径')
    parser.add_argument('--username', '-u', help='用户名')
    parser.add_argument('--client-id', '-c', help='客户端ID')
    parser.add_argument('--to-user', help='目标用户名（用于转移）')
    parser.add_argument('--online', action='store_true', help='只显示在线')
    parser.add_argument('--days', type=int, default=30, help='天数阈值（用于清理离线）')
    parser.add_argument('--yes', '-y', action='store_true', help='跳过确认提示')
    parser.add_argument('--duplicates', action='store_true', help='清理重复记录')
    parser.add_argument('--offline', action='store_true', help='清理离线客户端')

    args = parser.parse_args()

    # 如果没有参数，显示帮助
    if not args.command:
        parser.print_help()
        return

    # 初始化管理器
    manager = UserClientManager(args.db)

    # 交互式模式
    if args.command == 'interactive':
        interactive_mode(manager)
        return

    # 命令行模式
    if args.command == 'list':
        bindings = manager.list_all_bindings(show_online=args.online)
        print_bindings_table(bindings)

    elif args.command == 'list-user':
        if not args.username:
            print("错误: 请使用 --username 指定用户名")
            return
        bindings = manager.list_user_clients(args.username)
        print_bindings_table(bindings)

    elif args.command == 'list-client':
        if not args.client_id:
            print("错误: 请使用 --client-id 指定客户端ID")
            return
        bindings = manager.list_client_users(args.client_id)
        if bindings:
            headers = ["用户", "授权时间", "授权人", "主机名", "状态"]
            rows = [[
                b.get('username', '-'),
                b.get('granted_at', '-')[:19] if b.get('granted_at') else '-',
                b.get('granted_by', '-'),
                b.get('hostname', '-'),
                b.get('status', '-')
            ] for b in bindings]
            print_table(headers, rows)
        else:
            print(f"客户端 '{args.client_id}' 没有绑定到任何用户")

    elif args.command == 'list-online':
        clients = manager.list_online_clients()
        if clients:
            headers = ["客户端ID", "主机名", "操作系统", "绑定用户"]
            rows = [[
                c.get('client_id', '-'),
                c.get('hostname', '-'),
                c.get('os_info', '-'),
                c.get('users', '-')
            ] for c in clients]
            print_table(headers, rows)
        else:
            print("当前没有在线客户端")

    elif args.command == 'create-user':
        if len(args.args) < 2:
            print("用法: python user_client_manager.py create-user <username> <password>")
            return
        username = args.args[0]
        password = args.args[1]
        manager.create_user(username, password)

    elif args.command == 'delete-user':
        if len(args.args) < 1:
            print("用法: python user_client_manager.py delete-user <username>")
            return
        username = args.args[0]

        if not args.yes:
            confirm = input(f"确认删除用户 '{username}'? 这将同时删除所有绑定关系 (yes/no): ").strip().lower()
            if confirm != 'yes':
                print("操作已取消")
                return

        manager.delete_user(username)

    elif args.command == 'change-password':
        if len(args.args) < 2:
            print("用法: python user_client_manager.py change-password <username> <new_password>")
            return
        username = args.args[0]
        new_password = args.args[1]
        manager.change_password(username, new_password)

    elif args.command == 'user-info':
        if not args.username:
            print("用法: python user_client_manager.py user-info --username <username>")
            return
        info = manager.get_user_info(args.username)
        if info:
            print(f"\n=== 用户 '{args.username}' 详细信息 ===")
            print(f"用户ID: {info.get('id', '-')}")
            print(f"用户名: {info.get('username', '-')}")
            print(f"API密钥: {info.get('api_key', '-')}")
            print(f"状态: {'激活' if info.get('is_active') else '未激活'}")
            print(f"创建时间: {info.get('created_at', '-')}")
            print(f"绑定客户端数: {info.get('client_count', 0)}")
        else:
            print(f"用户 '{args.username}' 不存在")

    elif args.command == 'assign':
        if len(args.args) < 2:
            print("用法: python user_client_manager.py assign <username> <client_id>")
            return
        username = args.args[0]
        client_id = args.args[1]
        manager.assign_client(username, client_id)

    elif args.command == 'transfer':
        if len(args.args) < 3:
            print("用法: python user_client_manager.py transfer <from_user> <to_user> <client_id>")
            return
        from_user = args.args[0]
        to_user = args.args[1]
        client_id = args.args[2]

        if not args.yes:
            confirm = input(f"确认将客户端 '{client_id}' 从 '{from_user}' 转移到 '{to_user}'? (yes/no): ").strip().lower()
            if confirm != 'yes':
                print("操作已取消")
                return

        manager.transfer_client(from_user, to_user, client_id)

    elif args.command == 'batch-transfer':
        if len(args.args) < 2:
            print("用法: python user_client_manager.py batch-transfer <from_user> <to_user>")
            return
        from_user = args.args[0]
        to_user = args.args[1]

        if not args.yes:
            bindings = manager.list_user_clients(from_user)
            if bindings:
                print(f"\n将转移以下 {len(bindings)} 个客户端:")
                for b in bindings:
                    print(f"  - {b.get('client_id')}")
                confirm = input(f"\n确认将所有客户端从 '{from_user}' 转移到 '{to_user}'? (yes/no): ").strip().lower()
                if confirm != 'yes':
                    print("操作已取消")
                    return
            else:
                print(f"用户 '{from_user}' 没有绑定的客户端")
                return

        manager.batch_transfer(from_user, to_user)

    elif args.command == 'remove':
        if len(args.args) < 2:
            print("用法: python user_client_manager.py remove <username> <client_id>")
            return
        username = args.args[0]
        client_id = args.args[1]

        if not args.yes:
            confirm = input(f"确认删除绑定: 用户 '{username}' - 客户端 '{client_id}'? (yes/no): ").strip().lower()
            if confirm != 'yes':
                print("操作已取消")
                return

        manager.remove_binding(username, client_id)

    elif args.command == 'remove-user-bindings':
        if len(args.args) < 1:
            print("用法: python user_client_manager.py remove-user-bindings <username>")
            return
        username = args.args[0]

        if not args.yes:
            bindings = manager.list_user_clients(username)
            if bindings:
                print(f"\n将删除以下 {len(bindings)} 个绑定:")
                for b in bindings:
                    print(f"  - {b.get('client_id')}")
                confirm = input(f"\n确认删除用户 '{username}' 的所有绑定? (yes/no): ").strip().lower()
                if confirm != 'yes':
                    print("操作已取消")
                    return

        manager.remove_user_all(username)

    elif args.command == 'remove-client-bindings':
        if len(args.args) < 1:
            print("用法: python user_client_manager.py remove-client-bindings <client_id>")
            return
        client_id = args.args[0]

        if not args.yes:
            bindings = manager.list_client_users(client_id)
            if bindings:
                print(f"\n将删除客户端 '{client_id}' 与以下 {len(bindings)} 个用户的绑定:")
                for b in bindings:
                    print(f"  - {b.get('username')}")
                confirm = input(f"\n确认删除客户端 '{client_id}' 的所有绑定? (yes/no): ").strip().lower()
                if confirm != 'yes':
                    print("操作已取消")
                    return

        manager.remove_client_all(client_id)

    elif args.command == 'cleanup':
        if args.duplicates:
            if not args.yes:
                confirm = input("确认清理重复的绑定记录? (yes/no): ").strip().lower()
                if confirm != 'yes':
                    print("操作已取消")
                    return
            manager.cleanup_duplicates()

        if args.offline:
            if not args.yes:
                confirm = input(f"确认清理离线超过 {args.days} 天的客户端绑定? (yes/no): ").strip().lower()
                if confirm != 'yes':
                    print("操作已取消")
                    return
            manager.cleanup_offline(args.days)

        if not args.duplicates and not args.offline:
            print("错误: 请指定 --duplicates 或 --offline 选项")

    else:
        print(f"错误: 未知命令 '{args.command}'")
        parser.print_help()


if __name__ == "__main__":
    main()
