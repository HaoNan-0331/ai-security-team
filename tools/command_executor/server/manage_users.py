#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户管理脚本
用于在服务端管理用户、分配客户端权限

使用方法:
    python manage_users.py add_user <username> <password>     # 添加用户
    python manage_users.py list_users                       # 列出所有用户
    python manage_users.py assign_client <username> <client_id>  # 分配客户端给用户
    python manage_users.py revoke_client <username> <client_id>   # 撤销客户端权限
    python manage_users.py user_clients <username>           # 查看用户的客户端列表
    python manage_users.py delete_user <username>             # 删除用户
    python manage_users.py reset_password <username> <new_password>  # 重置密码
    python manage_users.py show_apikey <username>              # 显示用户API密钥
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from server.database import (
    Session, UserManager, get_db, init_database,
    User as DBUser
)


def add_user(username: str, password: str):
    """添加新用户"""
    db = next(get_db())
    try:
        user = UserManager.create_user(db, username, password)
        if user:
            print(f"✅ 用户创建成功！")
            print(f"   用户名: {user.username}")
            print(f"   API密钥: {user.api_key}")
            print(f"   创建时间: {user.created_at}")
        else:
            print(f"❌ 用户创建失败：用户 '{username}' 已存在")
    finally:
        db.close()


def list_users():
    """列出所有用户"""
    db = next(get_db())
    try:
        users = UserManager.list_all_users(db)
        if not users:
            print("⚠️  暂无用户")
            return

        print(f"\n共有 {len(users)} 个用户：")
        print("-" * 60)
        for user in users:
            # 获取用户的客户端数量
            client_ids = UserManager.get_user_clients(db, user.username)
            print(f"👤 用户名: {user.username}")
            print(f"   状态: {'✅ 激活' if user.is_active else '❌ 禁用'}")
            print(f"   API密钥: {user.api_key}")
            print(f"   关联客户端数: {len(client_ids)}")
            if client_ids:
                print(f"   客户端列表: {', '.join(client_ids)}")
            print(f"   创建时间: {user.created_at}")
            print("-" * 60)
    finally:
        db.close()


def assign_client(username: str, client_id: str):
    """分配客户端给用户"""
    db = next(get_db())
    try:
        success = UserManager.assign_client_to_user(db, username, client_id)
        if success:
            print(f"✅ 客户端 '{client_id}' 已分配给用户 '{username}'")
        else:
            print(f"❌ 分配失败：用户 '{username}' 不存在")
    finally:
        db.close()


def revoke_client(username: str, client_id: str):
    """撤销用户对客户端的访问权限"""
    db = next(get_db())
    try:
        success = UserManager.revoke_client_access(db, username, client_id)
        if success:
            print(f"✅ 已撤销用户 '{username}' 对客户端 '{client_id}' 的访问权限")
        else:
            print(f"❌ 撤销失败：用户 '{username}' 或客户端 '{client_id}' 不存在")
    finally:
        db.close()


def user_clients(username: str):
    """查看用户的客户端列表"""
    db = next(get_db())
    try:
        client_ids = UserManager.get_user_clients(db, username)
        if client_ids:
            print(f"✅ 用户 '{username}' 有权使用 {len(client_ids)} 个客户端：")
            for i, client_id in enumerate(client_ids, 1):
                print(f"   {i}. {client_id}")
        else:
            print(f"⚠️  用户 '{username}' 暂无任何客户端权限")
    finally:
        db.close()


def delete_user(username: str):
    """删除用户"""
    db = next(get_db())
    try:
        user = db.query(DBUser).filter(DBUser.username == username).first()
        if user:
            db.delete(user)
            db.commit()
            print(f"✅ 用户 '{username}' 已删除")
        else:
            print(f"❌ 用户 '{username}' 不存在")
    finally:
        db.close()


def reset_password(username: str, new_password: str):
    """重置用户密码"""
    db = next(get_db())
    try:
        user = db.query(DBUser).filter(DBUser.username == username).first()
        if user:
            user.password_hash = UserManager.hash_password(new_password)
            db.commit()
            print(f"✅ 用户 '{username}' 的密码已重置")
        else:
            print(f"❌ 用户 '{username}' 不存在")
    finally:
        db.close()


def show_apikey(username: str):
    """显示用户的API密钥"""
    db = next(get_db())
    try:
        user = UserManager.get_user_by_username(db, username)
        if user:
            print(f"✅ 用户 '{username}' 的API密钥：")
            print(f"   {user.api_key}")
        else:
            print(f"❌ 用户 '{username}' 不存在")
    finally:
        db.close()


def show_help():
    """显示帮助信息"""
    print(__doc__)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)

    # 初始化数据库（如果需要）
    init_database()

    command = sys.argv[1]

    if command == "add_user":
        if len(sys.argv) < 4:
            print("用法: python manage_users.py add_user <username> <password>")
            sys.exit(1)
        add_user(sys.argv[2], sys.argv[3])

    elif command == "list_users":
        list_users()

    elif command == "assign_client":
        if len(sys.argv) < 4:
            print("用法: python manage_users.py assign_client <username> <client_id>")
            sys.exit(1)
        assign_client(sys.argv[2], sys.argv[3])

    elif command == "revoke_client":
        if len(sys.argv) < 4:
            print("用法: python manage_users.py revoke_client <username> <client_id>")
            sys.exit(1)
        revoke_client(sys.argv[2], sys.argv[3])

    elif command == "user_clients":
        if len(sys.argv) < 3:
            print("用法: python manage_users.py user_clients <username>")
            sys.exit(1)
        user_clients(sys.argv[2])

    elif command == "delete_user":
        if len(sys.argv) < 3:
            print("用法: python manage_users.py delete_user <username>")
            sys.exit(1)
        delete_user(sys.argv[2])

    elif command == "reset_password":
        if len(sys.argv) < 4:
            print("用法: python manage_users.py reset_password <username> <new_password>")
            sys.exit(1)
        reset_password(sys.argv[2], sys.argv[3])

    elif command == "show_apikey":
        if len(sys.argv) < 3:
            print("用法: python manage_users.py show_apikey <username>")
            sys.exit(1)
        show_apikey(sys.argv[2])

    else:
        print(f"❌ 未知命令: {command}")
        show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
