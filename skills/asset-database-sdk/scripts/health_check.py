#!/usr/bin/env python3
"""
资产健康检查工具
支持批量检查资产连通性和端口状态

使用示例:
    python health_check.py --type Server                    # 检查所有服务器
    python health_check.py --assets id1,id2,id3             # 检查指定资产
    python health_check.py --check-type port                # 检查端口
    python health_check.py --output report.json             # 导出报告
    python health_check.py --retry 3                        # 失败重试3次
"""

import sys
import os
import argparse
import json
import socket
import subprocess
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加资产库SDK路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sdk_path = os.path.join(script_dir, '../../../ai-security-team/asset-database')
sys.path.insert(0, sdk_path)

from asset_sdk import AssetClient


def ping_host(host, timeout=2):
    """
    Ping主机检查连通性

    Args:
        host: 主机地址
        timeout: 超时时间（秒）

    Returns:
        dict: {'status': 'reachable'/'unreachable', 'latency_ms': latency}
    """
    try:
        # Windows使用ping -n，Linux使用ping -c
        if os.name == 'nt':
            cmd = ['ping', '-n', '1', '-w', str(int(timeout * 1000)), host]
        else:
            cmd = ['ping', '-c', '1', '-W', str(timeout), host]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout + 1
        )

        if result.returncode == 0:
            # 解析延迟
            latency_ms = None
            output = result.stdout.decode('gbk' if os.name == 'nt' else 'utf-8')
            if 'time=' in output or 'time<' in output:
                # 提取延迟时间
                import re
                match = re.search(r'time[=<](\d+\.?\d*)', output)
                if match:
                    latency_ms = float(match.group(1))

            return {
                'status': 'reachable',
                'latency_ms': latency_ms
            }
        else:
            return {
                'status': 'unreachable',
                'latency_ms': None
            }

    except subprocess.TimeoutExpired:
        return {
            'status': 'timeout',
            'latency_ms': None
        }
    except Exception as e:
        return {
            'status': 'error',
            'latency_ms': None,
            'error': str(e)
        }


def check_port(host, port, timeout=2):
    """
    检查端口是否开放

    Args:
        host: 主机地址
        port: 端口号
        timeout: 超时时间（秒）

    Returns:
        dict: {'status': 'open'/'closed', 'port': port}
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        result = s.connect_ex((host, port))
        s.close()

        if result == 0:
            return {
                'status': 'open',
                'port': port
            }
        else:
            return {
                'status': 'closed',
                'port': port
            }

    except socket.timeout:
        return {
            'status': 'timeout',
            'port': port
        }
    except Exception as e:
        return {
            'status': 'error',
            'port': port,
            'error': str(e)
        }


def check_asset(asset, check_type='connectivity', timeout=2):
    """
    检查单个资产

    Args:
        asset: 资产信息
        check_type: 检查类型 (connectivity/port)
        timeout: 超时时间

    Returns:
        dict: 检查结果
    """
    result = {
        'asset_id': asset['asset_id'],
        'asset_name': asset['name'],
        'asset_type': asset['asset_type'],
        'ip_address': asset.get('ip_address', ''),
        'check_type': check_type,
        'timestamp': datetime.now().isoformat()
    }

    if not asset.get('ip_address'):
        result.update({
            'status': 'skipped',
            'error': '没有IP地址'
        })
        return result

    if check_type == 'connectivity':
        check_result = ping_host(asset['ip_address'], timeout)
    elif check_type == 'port':
        port = asset.get('ssh_port', 22)  # 默认检查SSH端口
        check_result = check_port(asset['ip_address'], port, timeout)
    else:
        result.update({
            'status': 'error',
            'error': f'不支持的检查类型: {check_type}'
        })
        return result

    result.update(check_result)
    return result


def run_health_checks(assets, check_type='connectivity', timeout=2, max_workers=10):
    """
    批量执行健康检查（并行）

    Args:
        assets: 资产列表
        check_type: 检查类型
        timeout: 超时时间
        max_workers: 最大并发数

    Returns:
        list: 检查结果列表
    """
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(check_asset, asset, check_type, timeout): asset
            for asset in assets
        }

        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            # 打印进度
            status = result.get('status', 'unknown')
            print(f"  {result['asset_name']}: {status}")

    return results


def print_summary(results):
    """打印检查摘要"""
    if not results:
        print("没有检查结果")
        return

    total = len(results)
    reachable = sum(1 for r in results if r.get('status') == 'reachable' or r.get('status') == 'open')
    unreachable = sum(1 for r in results if r.get('status') == 'unreachable' or r.get('status') == 'closed')
    timeout = sum(1 for r in results if r.get('status') == 'timeout')
    errors = sum(1 for r in results if r.get('status') == 'error')
    skipped = sum(1 for r in results if r.get('status') == 'skipped')

    print(f"\n=== 检查摘要 ===")
    print(f"总数: {total}")
    print(f"正常: {reachable}")
    print(f"异常: {unreachable}")
    print(f"超时: {timeout}")
    print(f"错误: {errors}")
    print(f"跳过: {skipped}")

    # 列出异常资产
    if unreachable > 0:
        print(f"\n=== 异常资产 ===")
        for r in results:
            if r.get('status') == 'unreachable' or r.get('status') == 'closed':
                print(f"  {r['asset_name']} ({r['ip_address']})")


def export_report(results, filename):
    """导出检查报告"""
    report = {
        'generated_at': datetime.now().isoformat(),
        'total_checks': len(results),
        'reachable': sum(1 for r in results if r.get('status') == 'reachable' or r.get('status') == 'open'),
        'unreachable': sum(1 for r in results if r.get('status') == 'unreachable' or r.get('status') == 'closed'),
        'timeout': sum(1 for r in results if r.get('status') == 'timeout'),
        'errors': sum(1 for r in results if r.get('status') == 'error'),
        'results': results
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n报告已导出到: {filename}")


def main():
    parser = argparse.ArgumentParser(description='资产健康检查工具')

    # 查询选项
    query_group = parser.add_mutually_exclusive_group()
    query_group.add_argument('--type', help='按资产类型查询')
    query_group.add_argument('--assets', help='指定资产ID (逗号分隔)')
    query_group.add_argument('--env', help='按环境查询')

    # 检查选项
    parser.add_argument('--check-type', choices=['connectivity', 'port'], default='connectivity',
                        help='检查类型 (默认: connectivity)')
    parser.add_argument('--timeout', type=float, default=2, help='超时时间（秒）')
    parser.add_argument('--workers', type=int, default=10, help='并发数')

    # 输出选项
    parser.add_argument('--output', help='导出报告到文件')

    args = parser.parse_args()

    # 创建客户端
    client = AssetClient()

    # 获取要检查的资产
    assets = []

    if args.assets:
        # 指定资产ID
        asset_ids = args.assets.split(',')
        for asset_id in asset_ids:
            asset = client.get_asset(asset_id.strip())
            if asset:
                assets.append(asset)
            else:
                print(f"警告: 资产不存在: {asset_id}")

    elif args.type:
        # 按类型查询
        assets = client.list_assets(asset_type=args.type)

    elif args.env:
        # 按环境查询
        assets = client.list_assets(environment=args.env)

    else:
        # 默认检查所有Server
        print("未指定查询条件，默认检查所有Server...")
        assets = client.list_assets(asset_type='Server')

    if not assets:
        print("没有找到要检查的资产")
        return

    print(f"开始检查 {len(assets)} 个资产...")
    print(f"检查类型: {args.check_type}")
    print(f"超时时间: {args.timeout}秒")
    print()

    # 执行检查
    results = run_health_checks(
        assets,
        check_type=args.check_type,
        timeout=args.timeout,
        max_workers=args.workers
    )

    # 打印摘要
    print_summary(results)

    # 导出报告
    if args.output:
        export_report(results, args.output)


if __name__ == '__main__':
    main()
