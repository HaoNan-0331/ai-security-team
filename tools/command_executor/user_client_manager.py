#!/usr/bin/env python3
"""
用户-客户端关系管理脚本
用于查看和管理用户与客户端之间的绑定关系

使用方式：
    交互式模式：python user_client_manager.py interactive
    命令行模式：python user_client_manager.py <command> [options]
    查看帮助：python user_client_manager.py --help
"""

import argparse
import os
import sys
import hashlib
import secrets
import uuid as uuid_lib
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict

# Python 3.6 兼容性补丁 - 使用 pysqlite3 替代 sqlite3
try:
    import pysqlite3 as sqlite3
except ImportError:
    import sqlite3


class UserClientManager:
    """用户-客户端关系管理器"""

    def __init__(self, db_path: str = None):
        """初始化管理器

        Args:
            db_path: 数据库文件路径，默认使用环境变量 DB_PATH 或 /opt/command-executor-server/data/server_data.db
        """
        if db_path is None:
            # 优先使用环境变量，否则使用默认的固定路径
            db_path = os.environ.get("DB_PATH", "/opt/command-executor-server/data/server_data.db")
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
        """查看所有用户-客户端绑定"""
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
        """查看指定用户的客户端列表"""
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

    def list_all_clients(self) -> List[Dict]:
        """查看所有客户端"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT client_id, hostname, os_info,
                   CASE WHEN is_online = 1 THEN '在线' ELSE '离线' END as status,
                   last_seen
            FROM client_connections
            ORDER BY is_online DESC, client_id
        """
        cursor.execute(query)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_client_info(self, client_id: str) -> Dict:
        """获取客户端详细信息"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT client_id, hostname, os_info, is_online, last_seen, first_connected
            FROM client_connections
            WHERE client_id = ?
        """
        cursor.execute(query, (client_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def list_all_users(self) -> List[Dict]:
        """查看所有用户"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = "SELECT id, username, created_at FROM users ORDER BY username"
        cursor.execute(query)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    # ==================== 绑定功能 ====================

    def assign_client(self, username: str, client_id: str, granted_by: str = "admin") -> bool:
        """分配客户端给用户"""
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

            # 检查是否已绑定
            cursor.execute("SELECT id FROM user_clients WHERE user_id = ? AND client_id = ?",
                         (user_id, client_id))
            if cursor.fetchone():
                print(f"提示: 客户端 '{client_id}' 已经绑定到用户 '{username}'")
                return True

            # 创建绑定记录
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

    # ==================== 删除功能 ====================

    def remove_binding(self, username: str, client_id: str) -> bool:
        """删除指定的用户-客户端绑定"""
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

            # 检查是否存在
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

    def delete_client(self, client_id: str, force: bool = False) -> bool:
        """删除客户端（包括在线客户端）

        Args:
            client_id: 客户端ID
            force: 是否强制删除（跳过确认）

        Returns:
            是否成功
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 获取客户端信息
            cursor.execute("""
                SELECT client_id, hostname, os_info, is_online, last_seen
                FROM client_connections
                WHERE client_id = ?
            """, (client_id,))
            client = cursor.fetchone()

            if not client:
                print(f"错误: 客户端 '{client_id}' 不存在")
                return False

            is_online = client[3]
            hostname = client[1]

            # 如果是在线客户端，警告用户
            if is_online:
                print(f"警告: 客户端 '{client_id}' ({hostname}) 当前在线!")
                print("删除后该客户端将被强制断开连接，且其Token将被撤销。")

                if not force:
                    confirm = input("确认删除此在线客户端? (yes/no): ").strip().lower()
                    if confirm != 'yes':
                        print("操作已取消")
                        return False

            # 获取绑定的用户数量
            cursor.execute("SELECT COUNT(*) FROM user_clients WHERE client_id = ?", (client_id,))
            binding_count = cursor.fetchone()[0]

            # 获取绑定的用户列表
            cursor.execute("""
                SELECT u.username
                FROM user_clients uc
                JOIN users u ON uc.user_id = u.id
                WHERE uc.client_id = ?
            """, (client_id,))
            bound_users = [row[0] for row in cursor.fetchall()]

            # 撤销相关用户的Token
            if bound_users:
                cursor.execute("""
                    UPDATE api_tokens SET is_revoked = 1
                    WHERE user_id IN (
                        SELECT uc.user_id FROM user_clients uc
                        JOIN users u ON uc.user_id = u.id
                        WHERE uc.client_id = ?
                    )
                """, (client_id,))
                revoked_tokens = cursor.rowcount
            else:
                revoked_tokens = 0

            # 删除绑定关系
            cursor.execute("DELETE FROM user_clients WHERE client_id = ?", (client_id,))
            deleted_bindings = cursor.rowcount

            # 删除客户端记录
            cursor.execute("DELETE FROM client_connections WHERE client_id = ?", (client_id,))

            conn.commit()

            print(f"成功: 客户端 '{client_id}' 已删除")
            print(f"  - 删除绑定关系: {deleted_bindings} 条")
            print(f"  - 撤销Token: {revoked_tokens} 个")
            if is_online:
                print(f"  - 在线状态: 客户端将在下次心跳时被强制断开")

            return True

        except Exception as e:
            conn.rollback()
            print(f"错误: {e}")
            return False
        finally:
            conn.close()

    def delete_all_offline_clients(self, days: int = 0) -> int:
        """删除所有离线客户端

        Args:
            days: 离线天数阈值，0表示删除所有离线客户端

        Returns:
            删除的客户端数量
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 构建查询条件
            if days > 0:
                threshold = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
                query = """
                    SELECT client_id, hostname, last_seen
                    FROM client_connections
                    WHERE is_online = 0
                    AND datetime(last_seen) < datetime(?)
                """
                cursor.execute(query, (threshold,))
            else:
                query = """
                    SELECT client_id, hostname, last_seen
                    FROM client_connections
                    WHERE is_online = 0
                """
                cursor.execute(query)

            offline_clients = cursor.fetchall()

            if not offline_clients:
                if days > 0:
                    print(f"提示: 没有离线超过 {days} 天的客户端")
                else:
                    print("提示: 没有离线客户端")
                return 0

            print(f"发现 {len(offline_clients)} 个离线客户端:")
            for client in offline_clients[:10]:  # 只显示前10个
                print(f"  - {client[0]} ({client[1]}) - 最后在线: {client[2]}")
            if len(offline_clients) > 10:
                print(f"  ... 还有 {len(offline_clients) - 10} 个")

            # 删除绑定关系
            client_ids = [c[0] for c in offline_clients]
            placeholders = ','.join('?' * len(client_ids))
            cursor.execute(f"DELETE FROM user_clients WHERE client_id IN ({placeholders})", client_ids)
            deleted_bindings = cursor.rowcount

            # 撤销相关Token
            cursor.execute(f"""
                UPDATE api_tokens SET is_revoked = 1
                WHERE user_id IN (
                    SELECT DISTINCT user_id FROM user_clients
                    WHERE client_id IN ({placeholders})
                ) AND is_revoked = 0
            """, client_ids)
            revoked_tokens = cursor.rowcount

            # 删除客户端记录
            cursor.execute(f"DELETE FROM client_connections WHERE client_id IN ({placeholders})", client_ids)
            deleted_clients = cursor.rowcount

            conn.commit()

            print(f"\n成功删除:")
            print(f"  - 离线客户端: {deleted_clients} 个")
            print(f"  - 绑定关系: {deleted_bindings} 条")
            print(f"  - 撤销Token: {revoked_tokens} 个")

            return deleted_clients

        except Exception as e:
            conn.rollback()
            print(f"错误: {e}")
            return 0
        finally:
            conn.close()

    def cleanup_offline(self, days: int = 30) -> int:
        """清理离线超过指定天数的客户端（包含client_connections表记录）

        Args:
            days: 天数阈值
        """
        return self.delete_all_offline_clients(days)

    # ==================== 用户管理功能 ====================

    def create_user(self, username: str, password: str) -> bool:
        """创建新用户"""
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

            # 创建用户
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

    def delete_user(self, username: str, force: bool = False) -> bool:
        """删除用户"""
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

            if binding_count > 0 and not force:
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
        """修改用户密码"""
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

    # ==================== 清理功能 ====================

    def cleanup_duplicates(self) -> int:
        """清理重复的绑定记录"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 删除重复的记录，保留rowid最小的
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
            print(f"成功: 已清理 {count} 个重复绑定记录")
            return count

        except Exception as e:
            conn.rollback()
            print(f"错误: {e}")
            return 0
        finally:
            conn.close()


# ==================== 表格打印工具 ====================

def print_table(headers: List[str], rows: List[List[str]], widths: List[int] = None):
    """打印表格"""
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
        print("  3. 查看所有客户端")
        print("  4. 查看所有用户")
        print()
        print("【用户管理功能】")
        print("  5. 创建新用户")
        print("  6. 删除用户")
        print("  7. 修改用户密码")
        print()
        print("【客户端绑定功能】")
        print("  8. 分配客户端给用户")
        print("  9. 删除指定绑定")
        print()
        print("【客户端删除功能】")
        print("  10. 删除单个客户端 (支持在线客户端)")
        print("  11. 删除所有离线客户端")
        print("  12. 清理离线超过N天的客户端")
        print()
        print("【清理功能】")
        print("  13. 清理重复绑定记录")
        print()
        print("  0. 退出")
        print()

        choice = input("请选择操作 [0-13]: ").strip()

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
            print("\n=== 所有客户端 ===")
            clients = manager.list_all_clients()
            if clients:
                headers = ["客户端ID", "主机名", "操作系统", "状态", "最后在线"]
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

        elif choice == "4":
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

        elif choice == "5":
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

        elif choice == "6":
            username = input("请输入要删除的用户名: ").strip()
            if username:
                manager.delete_user(username)
            else:
                print("错误: 用户名不能为空")

        elif choice == "7":
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

        elif choice == "8":
            username = input("请输入用户名: ").strip()
            client_id = input("请输入客户端ID: ").strip()
            if username and client_id:
                manager.assign_client(username, client_id)
            else:
                print("错误: 用户名和客户端ID不能为空")

        elif choice == "9":
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

        elif choice == "10":
            client_id = input("请输入要删除的客户端ID: ").strip()
            if client_id:
                # 先显示客户端信息
                info = manager.get_client_info(client_id)
                if info:
                    print(f"\n客户端信息:")
                    print(f"  ID: {info.get('client_id')}")
                    print(f"  主机名: {info.get('hostname')}")
                    print(f"  操作系统: {info.get('os_info')}")
                    print(f"  状态: {'在线' if info.get('is_online') else '离线'}")
                    print(f"  最后在线: {info.get('last_seen')}")
                    print()
                manager.delete_client(client_id)
            else:
                print("错误: 客户端ID不能为空")

        elif choice == "11":
            confirm = input("确认删除所有离线客户端? (yes/no): ").strip().lower()
            if confirm == 'yes':
                manager.delete_all_offline_clients()
            else:
                print("操作已取消")

        elif choice == "12":
            days_input = input("请输入离线天数阈值 (默认30): ").strip()
            days = int(days_input) if days_input.isdigit() else 30
            confirm = input(f"确认清理离线超过 {days} 天的客户端? (yes/no): ").strip().lower()
            if confirm == 'yes':
                manager.cleanup_offline(days)
            else:
                print("操作已取消")

        elif choice == "13":
            confirm = input("确认清理重复的绑定记录? (yes/no): ").strip().lower()
            if confirm == 'yes':
                manager.cleanup_duplicates()
            else:
                print("操作已取消")

        else:
            print("错误: 无效选择，请输入 0-13")

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

  查看所有客户端:
    python user_client_manager.py list-clients

  删除单个客户端 (包括在线客户端):
    python user_client_manager.py delete-client <client_id>
    python user_client_manager.py delete-client <client_id> --force

  删除所有离线客户端:
    python user_client_manager.py delete-offline

  清理离线超过N天的客户端:
    python user_client_manager.py cleanup --days 30

  查看所有绑定:
    python user_client_manager.py list
    python user_client_manager.py list --online

  创建用户:
    python user_client_manager.py create-user <username> <password>

  删除用户:
    python user_client_manager.py delete-user <username> -y

  分配客户端:
    python user_client_manager.py assign <username> <client_id>

  删除绑定:
    python user_client_manager.py remove <username> <client_id> -y
        """
    )

    parser.add_argument('--db', default=None, help='数据库文件路径（默认: /opt/command-executor-server/data/server_data.db）')
    parser.add_argument('--days', type=int, default=30, help='天数阈值（用于清理离线）')
    parser.add_argument('--yes', '-y', action='store_true', help='跳过确认提示')
    parser.add_argument('--force', '-f', action='store_true', help='强制执行')
    parser.add_argument('--online', action='store_true', help='只显示在线')

    # 使用 parse_known_args 让 --db 等全局参数可以在命令之前或之后
    args, remaining = parser.parse_known_args()

    # 解析剩余参数（命令和命令参数）
    if remaining:
        args.command = remaining[0]
        args.args = remaining[1:]
    else:
        args.command = None
        args.args = []

    # 如果没有参数则显示帮助
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

    elif args.command == 'list-clients':
        clients = manager.list_all_clients()
        if clients:
            headers = ["客户端ID", "主机名", "操作系统", "状态", "最后在线"]
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

    elif args.command == 'list-users':
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

    elif args.command == 'delete-client':
        if len(args.args) < 1:
            print("用法: python user_client_manager.py delete-client <client_id> [--force]")
            return
        client_id = args.args[0]
        manager.delete_client(client_id, force=args.force)

    elif args.command == 'delete-offline':
        manager.delete_all_offline_clients()

    elif args.command == 'cleanup':
        if args.days > 0:
            manager.cleanup_offline(args.days)
        else:
            manager.delete_all_offline_clients()

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
        manager.delete_user(username, force=args.yes)

    elif args.command == 'assign':
        if len(args.args) < 2:
            print("用法: python user_client_manager.py assign <username> <client_id>")
            return
        username = args.args[0]
        client_id = args.args[1]
        manager.assign_client(username, client_id)

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

    else:
        print(f"错误: 未知命令 '{args.command}'")
        parser.print_help()


if __name__ == "__main__":
    main()
