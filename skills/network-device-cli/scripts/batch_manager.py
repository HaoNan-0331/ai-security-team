#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量设备操作管理器
支持交互式输入设备信息，对多台设备执行批量操作
"""

import sys
import argparse
import getpass
import json
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))


def input_device_info() -> Dict[str, Any]:
    """
    交互式输入设备信息

    Returns:
        设备信息字典
    """
    print("\n--- 输入设备信息 ---")
    print("（输入空行完成设备添加）")

    device = {}

    device['host'] = input("设备IP地址: ").strip()
    if not device['host']:
        return None

    device['vendor'] = input("设备厂商 (h3c/huawei/cisco/ruijie): ").strip().lower()
    if device['vendor'] not in ['h3c', 'huawei', 'cisco', 'ruijie']:
        print("[ERROR] 无效的厂商")
        return None

    device['username'] = input("用户名: ").strip()
    if not device['username']:
        print("[ERROR] 用户名不能为空")
        return None

    device['password'] = getpass.getpass("密码: ")
    if not device['password']:
        print("[ERROR] 密码不能为空")
        return None

    port_input = input("SSH端口 (默认22): ").strip()
    device['port'] = int(port_input) if port_input else 22

    # Cisco/Ruijie可能需要enable密码
    if device['vendor'] in ['cisco', 'ruijie']:
        enable_pw = getpass.getpass("Enable密码 (可选，直接回车跳过): ")
        if enable_pw:
            device['enable_password'] = enable_pw

    return device


def collect_devices() -> List[Dict[str, Any]]:
    """
    交互式收集多台设备信息

    Returns:
        设备信息列表
    """
    print("\n[INFO] 批量设备操作 - 交互式输入")
    print("[INFO] 请逐台输入设备信息，完成后输入空行")

    devices = []

    while True:
        device = input_device_info()
        if device is None:
            # 用户输入空行或无效信息
            if len(devices) == 0:
                print("[INFO] 至少需要输入一台设备信息")
                continue
            break

        devices.append(device)
        print(f"[OK] 已添加设备: {device['host']}")

        # 询问是否继续
        cont = input("\n继续添加设备? (y/N): ").strip().lower()
        if cont not in ['y', 'yes']:
            break

    print(f"\n[OK] 共收集 {len(devices)} 台设备信息")
    return devices


def execute_batch_commands(devices: List[Dict[str, Any]], commands: List[str]) -> List[Dict[str, Any]]:
    """
    批量执行命令

    Args:
        devices: 设备信息列表
        commands: 要执行的命令列表

    Returns:
        所有设备的执行结果
    """
    results = []

    for idx, device in enumerate(devices, 1):
        print(f"\n{'='*60}")
        print(f"[{idx}/{len(devices)}] 连接到设备: {device['host']}")
        print(f"{'='*60}")

        result = {
            'host': device['host'],
            'vendor': device['vendor'],
            'status': 'unknown',
            'success': False,
            'executed': 0,
            'total': len(commands),
            'results': [],
            'error': None
        }

        try:
            # 导入对应的执行器
            vendor = device['vendor']
            if vendor == 'h3c':
                from h3c_executor import H3CExecutor
                executor_class = H3CExecutor
            elif vendor == 'huawei':
                from huawei_executor import HuaweiExecutor
                executor_class = HuaweiExecutor
            elif vendor == 'cisco':
                from cisco_executor import CiscoExecutor
                executor_class = CiscoExecutor
            elif vendor == 'ruijie':
                from ruijie_executor import RuijieExecutor
                executor_class = RuijieExecutor
            else:
                raise ValueError(f"不支持的厂商: {vendor}")

            # 创建执行器
            kwargs = {
                'host': device['host'],
                'username': device['username'],
                'password': device['password'],
                'port': device['port']
            }

            if 'enable_password' in device:
                kwargs['enable_password'] = device['enable_password']

            executor = executor_class(**kwargs)

            # 连接设备
            if not executor.connect():
                result['status'] = 'failed'
                result['error'] = '连接失败'
                results.append(result)
                continue

            # 执行命令
            summary = executor.execute_commands(commands, stop_on_error=False)
            executor.disconnect()

            result['status'] = 'success' if summary['success'] else 'partial'
            result['success'] = summary['success']
            result['executed'] = summary['executed']
            result['results'] = summary['results']

            print(f"\n[结果] 成功: {summary['executed']}/{summary['total']}")
            if summary['failed_at']:
                print(f"[INFO] 在第 {summary['failed_at']} 条命令处失败")

        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            print(f"[ERROR] 执行失败: {str(e)}")

        results.append(result)

    return results


def execute_batch_backup(devices: List[Dict[str, Any]], backup_dir: str = "./backups") -> List[Dict[str, Any]]:
    """
    批量配置备份

    Args:
        devices: 设备信息列表
        backup_dir: 备份目录

    Returns:
        所有设备的备份结果
    """
    results = []

    for idx, device in enumerate(devices, 1):
        print(f"\n{'='*60}")
        print(f"[{idx}/{len(devices)}] 备份设备: {device['host']}")
        print(f"{'='*60}")

        result = {
            'host': device['host'],
            'vendor': device['vendor'],
            'status': 'unknown',
            'error': None,
            'backup_file': None
        }

        try:
            from config_backup import ConfigBackup

            backup_mgr = ConfigBackup(
                host=device['host'],
                username=device['username'],
                password=device['password'],
                vendor=device['vendor'],
                port=device['port'],
                backup_dir=backup_dir
            )

            backup_result = backup_mgr.backup_config()

            if backup_result['status'] == 'success':
                result['status'] = 'success'
                result['backup_file'] = backup_result['filename']
            else:
                result['status'] = 'failed'
                result['error'] = backup_result.get('error', '备份失败')

        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            print(f"[ERROR] 备份失败: {str(e)}")

        results.append(result)

    return results


def execute_batch_health_check(devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    批量健康检查

    Args:
        devices: 设备信息列表

    Returns:
        所有设备的检查结果
    """
    results = []

    for idx, device in enumerate(devices, 1):
        print(f"\n{'='*60}")
        print(f"[{idx}/{len(devices)}] 检查设备: {device['host']}")
        print(f"{'='*60}")

        result = {
            'host': device['host'],
            'vendor': device['vendor'],
            'status': 'unknown',
            'error': None,
            'score': None,
            'issues': []
        }

        try:
            from health_check import HealthChecker

            checker = HealthChecker(
                host=device['host'],
                username=device['username'],
                password=device['password'],
                vendor=device['vendor'],
                port=device['port']
            )

            check_result = checker.run_full_check()

            result['status'] = 'success'
            result['score'] = check_result['summary']['score']
            result['issues'] = check_result.get('issues', [])

            # 简要显示结果
            print(f"\n[健康评分] {result['score']}/100")
            if result['issues']:
                print(f"[问题数] {len(result['issues'])}")

        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            print(f"[ERROR] 检查失败: {str(e)}")

        results.append(result)

    return results


def display_summary(operation_type: str, results: List[Dict[str, Any]]):
    """显示执行摘要"""
    print(f"\n{'='*60}")
    print(f"[摘要] 批量{operation_type}完成")
    print(f"{'='*60}")

    total = len(results)
    success = sum(1 for r in results if r['status'] == 'success')
    partial = sum(1 for r in results if r['status'] == 'partial')
    failed = sum(1 for r in results if r['status'] in ['failed', 'error'])

    print(f"总设备数: {total}")
    print(f"成功: [green]{success}[/green]" if success > 0 else f"成功: {success}")
    print(f"部分成功: {partial}" if partial > 0 else "")
    print(f"失败: [red]{failed}[/red]" if failed > 0 else f"失败: {failed}")

    print("\n详细结果:")
    print(f"{'设备':<20} {'状态':<12} {'详情'}")
    print("-" * 60)

    for result in results:
        status = result['status']
        if status == 'success':
            status_display = '[OK]成功'
        elif status == 'partial':
            status_display = '[WARN]部分'
        elif status == 'failed':
            status_display = '[FAIL]失败'
        else:
            status_display = '[ERROR]错误'

        detail = ""
        if 'backup_file' in result and result['backup_file']:
            detail = result['backup_file'][:30]
        elif 'score' in result and result['score']:
            detail = f"评分: {result['score']}"
        elif 'error' in result and result['error']:
            detail = result['error'][:30]
        elif 'executed' in result:
            detail = f"{result['executed']}/{result['total']} 命令"

        print(f"{result['host']:<20} {status_display:<12} {detail}")


def save_results(results: List[Dict[str, Any]], output_file: str):
    """保存结果到文件"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n[OK] 结果已保存到: {output_file}")
    except Exception as e:
        print(f"[ERROR] 保存失败: {str(e)}")


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="批量设备操作管理器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 批量执行命令
  python batch_manager.py commands

  # 批量配置备份
  python batch_manager.py backup

  # 批量健康检查
  python batch_manager.py health

  # 保存结果
  python batch_manager.py commands --output results.json
        """
    )

    parser.add_argument("operation",
                       choices=['commands', 'backup', 'health'],
                       help="操作类型")

    parser.add_argument("--output", help="输出结果到文件")
    parser.add_argument("--backup-dir", default="./backups", help="备份目录（仅backup操作）")

    args = parser.parse_args()

    # 收集设备信息
    devices = collect_devices()

    if not devices:
        print("[ERROR] 没有有效的设备信息")
        sys.exit(1)

    # 根据操作类型执行
    results = []
    operation_name = ""

    if args.operation == 'commands':
        # 输入要执行的命令
        print("\n[INFO] 请输入要执行的命令（每行一条，空行结束）:")
        commands = []
        while True:
            cmd = input(f"命令{len(commands)+1}> ").strip()
            if not cmd:
                break
            commands.append(cmd)

        if not commands:
            print("[ERROR] 没有输入命令")
            sys.exit(1)

        print(f"\n[INFO] 将在 {len(devices)} 台设备上执行 {len(commands)} 条命令")
        confirm = input("确认执行? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("[INFO] 操作已取消")
            sys.exit(0)

        results = execute_batch_commands(devices, commands)
        operation_name = "命令执行"

    elif args.operation == 'backup':
        print(f"\n[INFO] 将备份 {len(devices)} 台设备的配置")
        confirm = input("确认执行? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("[INFO] 操作已取消")
            sys.exit(0)

        results = execute_batch_backup(devices, args.backup_dir)
        operation_name = "配置备份"

    elif args.operation == 'health':
        print(f"\n[INFO] 将检查 {len(devices)} 台设备的健康状态")
        confirm = input("确认执行? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("[INFO] 操作已取消")
            sys.exit(0)

        results = execute_batch_health_check(devices)
        operation_name = "健康检查"

    # 显示摘要
    display_summary(operation_name, results)

    # 保存结果
    if args.output:
        save_results(results, args.output)


if __name__ == "__main__":
    main()
