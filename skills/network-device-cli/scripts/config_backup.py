#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置备份和恢复工具
支持配置备份、恢复和对比
使用显式连接参数
"""

import sys
import argparse
import getpass
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))


class ConfigBackup:
    """配置备份管理器（使用厂商执行器）"""

    def __init__(self, host: str, username: str, password: str,
                 vendor: str, port: int = 22, backup_dir: str = "./backups"):
        self.host = host
        self.username = username
        self.password = password
        self.vendor = vendor.lower()
        self.port = port
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # 导入对应的执行器
        if self.vendor == 'h3c':
            from h3c_executor import H3CExecutor
            self.executor_class = H3CExecutor
        elif self.vendor == 'huawei':
            from huawei_executor import HuaweiExecutor
            self.executor_class = HuaweiExecutor
        elif self.vendor == 'cisco':
            from cisco_executor import CiscoExecutor
            self.executor_class = CiscoExecutor
        elif self.vendor == 'ruijie':
            from ruijie_executor import RuijieExecutor
            self.executor_class = RuijieExecutor
        else:
            raise ValueError(f"不支持的厂商: {vendor}")

        self.hostname = self.host.replace('.', '-')

        # 创建设备专用目录
        self.device_backup_dir = self.backup_dir / self.hostname
        self.device_backup_dir.mkdir(exist_ok=True)

    def _get_config_command(self) -> str:
        """获取显示配置的命令"""
        if self.vendor in ['h3c', 'huawei']:
            return 'display current-configuration'
        else:  # cisco, ruijie
            return 'show running-config'

    def _calculate_hash(self, content: str) -> str:
        """计算配置文件的哈希值"""
        return hashlib.md5(content.encode()).hexdigest()

    def backup_config(self, description: str = "") -> Dict[str, str]:
        """
        备份设备配置

        Args:
            description: 备份描述

        Returns:
            备份结果信息字典
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        print(f"\n[INFO] 备份设备配置: {self.hostname}")
        print(f"[INFO] 厂商: {self.vendor}")
        print(f"[INFO] 备份时间: {timestamp}")

        try:
            # 创建执行器并连接
            executor = self.executor_class(
                host=self.host,
                username=self.username,
                password=self.password,
                port=self.port
            )

            if not executor.connect():
                return {'status': 'error', 'error': '连接失败'}

            # 获取配置
            command = self._get_config_command()
            result = executor.execute_command(command, timeout=60)

            executor.disconnect()

            if not result['success']:
                return {'status': 'error', 'error': result.get('error', '命令执行失败')}

            output = result['output']

            # 生成文件名
            filename = f"{self.hostname}_running_{timestamp}.cfg"
            filepath = self.device_backup_dir / filename

            # 保存配置
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(output)

            # 计算哈希值
            file_hash = self._calculate_hash(output)

            result_info = {
                'status': 'success',
                'filename': str(filepath),
                'hash': file_hash,
                'size': len(output),
                'timestamp': timestamp
            }

            print(f"[OK] 配置备份成功")
            print(f"[INFO] 文件路径: {filepath}")
            print(f"[INFO] 文件大小: {len(output)} 字节")

            return result_info

        except Exception as e:
            error_result = {
                'status': 'error',
                'error': str(e)
            }
            print(f"[ERROR] 备份失败: {str(e)}")
            return error_result

    def list_backups(self) -> list:
        """列出所有备份文件"""
        backups = []

        for cfg_file in self.device_backup_dir.glob('*.cfg'):
            try:
                stat = cfg_file.stat()
                backups.append({
                    'filename': cfg_file.name,
                    'filepath': str(cfg_file),
                    'size': stat.st_size,
                    'mtime': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
            except Exception:
                continue

        # 按修改时间排序
        backups.sort(key=lambda x: x['mtime'], reverse=True)
        return backups

    def display_backups(self):
        """显示备份列表"""
        backups = self.list_backups()

        if not backups:
            print("[INFO] 未找到备份文件")
            return

        print(f"\n[INFO] 设备 {self.hostname} 的配置备份列表:\n")
        print(f"{'序号':<6} {'备份时间':<20} {'文件大小':<12} {'文件名'}")
        print("-" * 80)

        for idx, backup in enumerate(backups, 1):
            size_kb = backup['size'] / 1024
            print(f"{idx:<6} {backup['mtime']:<20} {size_kb:>8.1f} KB  {backup['filename']}")


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="配置备份和恢复工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 备份配置
  python config_backup.py --host 192.168.1.1 --username admin --vendor h3c --backup

  # 指定密码
  python config_backup.py --host 192.168.1.1 --username admin --password xxx --vendor cisco --backup

  # 列出备份
  python config_backup.py --host 192.168.1.1 --username admin --vendor huawei --list
        """
    )

    # 连接参数（必填）
    parser.add_argument("--host", required=True, help="设备IP地址")
    parser.add_argument("--username", required=True, help="用户名")
    parser.add_argument("--password", help="密码（不指定则交互式输入）")
    parser.add_argument("--vendor", required=True,
                       choices=['h3c', 'huawei', 'cisco', 'ruijie'],
                       help="设备厂商")
    parser.add_argument("--port", type=int, default=22, help="SSH端口")

    # 操作参数
    parser.add_argument("--backup", action="store_true", help="执行配置备份")
    parser.add_argument("--list", action="store_true", help="列出备份文件")
    parser.add_argument("--backup-dir", default="./backups", help="备份目录")

    args = parser.parse_args()

    # 获取密码
    password = args.password
    if not password:
        password = getpass.getpass("密码: ")

    # 创建备份管理器
    try:
        backup_mgr = ConfigBackup(
            host=args.host,
            username=args.username,
            password=password,
            vendor=args.vendor,
            port=args.port,
            backup_dir=args.backup_dir
        )

        if args.list:
            backup_mgr.display_backups()
        elif args.backup:
            result = backup_mgr.backup_config()
            if result['status'] == 'success':
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            parser.error("必须指定 --backup 或 --list")

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
