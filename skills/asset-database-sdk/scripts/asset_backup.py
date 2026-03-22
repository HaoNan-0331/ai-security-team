#!/usr/bin/env python3
"""
资产库备份工具
支持自动备份、压缩、保留策略

使用示例:
    python asset_backup.py                              # 备份到默认目录
    python asset_backup.py --output /backup/assets/     # 备份到指定目录
    python asset_backup.py --keep 30                     # 保留最近30天备份
    python asset_backup.py --compress                    # 备份并压缩
    python asset_backup.py --list                        # 列出备份文件
    python asset_backup.py --restore assets_backup_20260226.db  # 恢复备份
"""

import sys
import os
import argparse
import shutil
import gzip
from datetime import datetime, timedelta

# 添加资产库SDK路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sdk_path = os.path.join(script_dir, '../../../ai-security-team/asset-database')
sys.path.insert(0, sdk_path)


# 默认路径
DEFAULT_DB_PATH = os.path.join(sdk_path, 'data/assets.db')
DEFAULT_SECRET_KEY_PATH = os.path.join(sdk_path, 'data/.secret_key')
DEFAULT_OUTPUT_DIR = os.path.join(sdk_path, 'data/backups')


def create_backup(output_dir=None, compress=False, keep_days=None):
    """
    创建备份

    Args:
        output_dir: 输出目录
        compress: 是否压缩
        keep_days: 保留天数

    Returns:
        备份文件路径
    """
    # 确保输出目录存在
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    # 生成备份文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_backup = os.path.join(output_dir, f'assets_backup_{timestamp}.db')
    key_backup = os.path.join(output_dir, f'.secret_key_backup_{timestamp}')

    print(f"正在备份数据库...")
    print(f"  源: {DEFAULT_DB_PATH}")
    print(f"  目标: {db_backup}")

    # 备份数据库
    shutil.copy2(DEFAULT_DB_PATH, db_backup)
    print(f"  ✓ 数据库备份完成")

    # 备份密钥
    if os.path.exists(DEFAULT_SECRET_KEY_PATH):
        shutil.copy2(DEFAULT_SECRET_KEY_PATH, key_backup)
        print(f"  ✓ 密钥备份完成: {key_backup}")

    # 压缩
    if compress:
        print(f"\n正在压缩...")
        db_backup_gz = db_backup + '.gz'
        with open(db_backup, 'rb') as f_in:
            with gzip.open(db_backup_gz, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(db_backup)
        db_backup = db_backup_gz
        print(f"  ✓ 压缩完成: {db_backup_gz}")

    # 清理旧备份
    if keep_days:
        clean_old_backups(output_dir, keep_days)
        print(f"  ✓ 已清理 {keep_days} 天前的备份")

    # 获取文件大小
    size_mb = os.path.getsize(db_backup) / (1024 * 1024)
    print(f"\n备份完成!")
    print(f"  文件: {db_backup}")
    print(f"  大小: {size_mb:.2f} MB")

    return db_backup


def restore_backup(backup_file, restore_key=False):
    """
    恢复备份

    Args:
        backup_file: 备份文件路径
        restore_key: 是否恢复密钥
    """
    # 确定源文件
    if backup_file.endswith('.gz'):
        # 压缩文件
        temp_db = backup_file[:-3]  # 移除.gz
        print(f"正在解压: {backup_file}")
        with gzip.open(backup_file, 'rb') as f_in:
            with open(temp_db, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        source_db = temp_db
    else:
        source_db = backup_file

    # 检查备份文件是否存在
    if not os.path.exists(source_db):
        print(f"错误: 备份文件不存在: {source_db}")
        return False

    # 确认
    print(f"\n准备恢复备份:")
    print(f"  源: {source_db}")
    print(f"  目标: {DEFAULT_DB_PATH}")
    response = input("\n确认恢复? 这将覆盖当前数据库 (yes/no): ")
    if response.lower() != 'yes':
        print("已取消")
        return False

    # 备份当前数据库
    print(f"\n备份当前数据库...")
    current_backup = os.path.join(
        os.path.dirname(DEFAULT_DB_PATH),
        f'assets_before_restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    )
    shutil.copy2(DEFAULT_DB_PATH, current_backup)
    print(f"  ✓ 当前数据库已备份到: {current_backup}")

    # 恢复数据库
    print(f"\n恢复数据库...")
    shutil.copy2(source_db, DEFAULT_DB_PATH)
    print(f"  ✓ 数据库已恢复")

    # 恢复密钥
    if restore_key:
        backup_key = None
        if source_db.endswith('.db'):
            # 尝试找到对应的密钥备份
            base_name = os.path.basename(source_db).replace('assets_backup_', '').replace('.db', '')
            backup_key = os.path.join(
                os.path.dirname(source_db),
                f'.secret_key_backup_{base_name}'
            )
            if not os.path.exists(backup_key):
                # 尝试不带时间戳的密钥备份
                backup_key = os.path.join(
                    os.path.dirname(source_db),
                    '.secret_key_backup'
                )

        if backup_key and os.path.exists(backup_key):
            print(f"\n恢复密钥...")
            shutil.copy2(backup_key, DEFAULT_SECRET_KEY_PATH)
            print(f"  ✓ 密钥已恢复")
        else:
            print(f"\n警告: 未找到密钥备份，跳过密钥恢复")

    # 清理临时文件
    if backup_file.endswith('.gz') and os.path.exists(temp_db):
        os.remove(temp_db)

    print(f"\n恢复完成!")

    return True


def clean_old_backups(output_dir, keep_days):
    """
    清理旧备份

    Args:
        output_dir: 备份目录
        keep_days: 保留天数
    """
    cutoff_date = datetime.now() - timedelta(days=keep_days)

    for filename in os.listdir(output_dir):
        filepath = os.path.join(output_dir, filename)

        # 只处理备份文件
        if not (filename.startswith('assets_backup_') or filename.startswith('.secret_key_backup_')):
            continue

        # 获取文件修改时间
        file_time = datetime.fromtimestamp(os.path.getmtime(filepath))

        # 如果文件过期则删除
        if file_time < cutoff_date:
            print(f"  删除旧备份: {filename}")
            os.remove(filepath)


def list_backups(output_dir=None):
    """
    列出备份文件

    Args:
        output_dir: 备份目录
    """
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR

    if not os.path.exists(output_dir):
        print(f"备份目录不存在: {output_dir}")
        return

    print(f"\n备份文件列表 ({output_dir}):\n")

    backups = []
    for filename in os.listdir(output_dir):
        if not (filename.startswith('assets_backup_') or filename.startswith('.secret_key_backup_')):
            continue

        filepath = os.path.join(output_dir, filename)
        file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        file_size = os.path.getsize(filepath)

        backups.append({
            'name': filename,
            'time': file_time,
            'size': file_size
        })

    # 按时间排序
    backups.sort(key=lambda x: x['time'], reverse=True)

    if not backups:
        print("  没有备份文件")
        return

    # 打印表格
    print(f"{'文件名':<40} {'时间':<20} {'大小':>10}")
    print("-" * 75)
    for backup in backups:
        size_mb = backup['size'] / (1024 * 1024)
        print(f"{backup['name']:<40} {backup['time'].strftime('%Y-%m-%d %H:%M:%S'):<20} {size_mb:>10.2f} MB")


def main():
    parser = argparse.ArgumentParser(description='资产库备份工具')

    # 备份选项
    parser.add_argument('--output', help='输出目录')
    parser.add_argument('--compress', action='store_true', help='压缩备份')
    parser.add_argument('--keep', type=int, help='保留天数')

    # 恢复选项
    parser.add_argument('--restore', help='恢复指定备份文件')
    parser.add_argument('--restore-key', action='store_true', help='恢复密钥')

    # 列表选项
    parser.add_argument('--list', action='store_true', help='列出备份文件')

    args = parser.parse_args()

    # 列出备份
    if args.list:
        list_backups(args.output)
        return

    # 恢复备份
    if args.restore:
        restore_backup(args.restore, args.restore_key)
        return

    # 创建备份
    create_backup(args.output, args.compress, args.keep)


if __name__ == '__main__':
    main()
