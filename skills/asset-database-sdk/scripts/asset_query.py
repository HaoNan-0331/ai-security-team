#!/usr/bin/env python3
"""
资产查询工具
提供命令行交互式资产查询功能

使用示例:
    python asset_query.py --type Server
    python asset_query.py --ip 192.168.1.100
    python asset_query.py --search web
    python asset_query.py --risk --min 60
    python asset_query.py --export assets.json
"""

import sys
import os
import argparse
import json
from datetime import datetime

# 添加资产库SDK路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sdk_path = os.path.join(script_dir, '../../../ai-security-team/asset-database')
sys.path.insert(0, sdk_path)

from asset_sdk import AssetClient


def print_table(data, headers=None, max_rows=None):
    """打印表格"""
    if not data:
        print("没有数据")
        return

    if headers is None:
        headers = data[0].keys()

    # 计算每列宽度
    col_widths = {}
    for header in headers:
        col_widths[header] = len(header)
        for row in data:
            value = str(row.get(header, ''))
            col_widths[header] = max(col_widths[header], len(value))

    # 打印表头
    header_line = ' | '.join(headers)
    separator = '-+-'.join(['-' * col_widths[h] for h in headers])
    print(header_line)
    print(separator)

    # 打印数据
    for i, row in enumerate(data):
        if max_rows and i >= max_rows:
            print(f"... (共 {len(data)} 条记录，显示前 {max_rows} 条)")
            break

        values = [str(row.get(h, ''))[:col_widths[h]] for h in headers]
        line = ' | '.join(values)
        print(line)


def query_by_type(client, asset_type, **filters):
    """按类型查询"""
    filters['asset_type'] = asset_type
    assets = client.list_assets(**filters)
    return assets


def query_by_ip(client, ip_address):
    """按IP查询"""
    asset = client.get_asset_by_ip(ip_address)
    return [asset] if asset else []


def query_by_name(client, name):
    """按名称查询"""
    asset = client.get_asset_by_name(name)
    return [asset] if asset else []


def search_assets(client, keyword, **filters):
    """关键字搜索"""
    results = client.find_assets(keyword, **filters)
    return results


def query_by_risk(client, min_score=None, max_score=None, **filters):
    """按风险分数查询"""
    assets = client.list_assets_by_risk(
        min_score=min_score,
        max_score=max_score,
        limit=100
    )
    return assets


def query_by_isolation(client, isolation_status, **filters):
    """按隔离状态查询"""
    assets = client.list_assets_by_isolation_status(isolation_status)
    return assets


def query_by_network_segment(client, network_segment, **filters):
    """按网段查询"""
    assets = client.list_assets_by_network_segment(network_segment)
    return assets


def export_assets(client, filename, format='json', **filters):
    """导出资产数据"""
    data = client.export_assets(format=format, **filters)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(data)

    print(f"数据已导出到: {filename}")

    if format == 'json':
        assets = json.loads(data)
        print(f"共 {len(assets)} 条记录")


def show_statistics(client):
    """显示统计信息"""
    stats = client.get_statistics(
        by_type=True,
        by_status=True,
        by_environment=True,
        by_importance=True
    )

    print("\n=== 资产统计 ===")
    print(f"\n按类型:")
    for asset_type, count in stats.get('by_type', {}).items():
        print(f"  {asset_type}: {count}")

    print(f"\n按状态:")
    for status, count in stats.get('by_status', {}).items():
        print(f"  {status}: {count}")

    print(f"\n按环境:")
    for env, count in stats.get('by_environment', {}).items():
        print(f"  {env}: {count}")

    print(f"\n按重要性:")
    for importance, count in stats.get('by_importance', {}).items():
        print(f"  {importance}: {count}")


def get_asset_details(client, asset_id):
    """获取资产详细信息"""
    asset = client.get_asset(asset_id)
    if not asset:
        print(f"资产 {asset_id} 不存在")
        return None

    print(f"\n=== 资产详情 ===")
    for key, value in asset.items():
        if key in ['password_encrypted', 'password']:  # 不显示密码
            continue
        print(f"{key}: {value}")

    return asset


def main():
    parser = argparse.ArgumentParser(description='资产查询工具')

    # 查询选项
    query_group = parser.add_mutually_exclusive_group()
    query_group.add_argument('--type', help='按资产类型查询 (Server/NetworkDevice/...)')
    query_group.add_argument('--ip', help='按IP地址查询')
    query_group.add_argument('--name', help='按名称查询')
    query_group.add_argument('--search', help='关键字搜索')
    query_group.add_argument('--risk', action='store_true', help='按风险分数查询')
    query_group.add_argument('--isolation', help='按隔离状态查询 (normal/network/host)')
    query_group.add_argument('--segment', help='按网段查询')
    query_group.add_argument('--id', help='按资产ID查询详细信息')
    query_group.add_argument('--stats', action='store_true', help='显示统计信息')

    # 过滤选项
    parser.add_argument('--env', help='环境 (production/development/test/...)')
    parser.add_argument('--status', help='状态 (active/maintenance/...)')
    parser.add_argument('--owner', help='负责人')
    parser.add_argument('--min-score', type=int, help='最小风险分数 (与--risk一起使用)')
    parser.add_argument('--max-score', type=int, help='最大风险分数 (与--risk一起使用)')

    # 输出选项
    parser.add_argument('--output', choices=['table', 'json'], default='table', help='输出格式')
    parser.add_argument('--export', help='导出到文件 (自动判断格式: .json或.csv)')
    parser.add_argument('--limit', type=int, help='限制返回数量')

    args = parser.parse_args()

    # 创建客户端
    client = AssetClient()

    # 如果有导出选项
    if args.export:
        filters = {}
        if args.type:
            filters['asset_type'] = args.type
        if args.env:
            filters['environment'] = args.env
        if args.status:
            filters['status'] = args.status
        if args.owner:
            filters['owner'] = args.owner

        # 根据文件扩展名确定格式
        if args.export.endswith('.csv'):
            format = 'csv'
        else:
            format = 'json'

        export_assets(client, args.export, format, **filters)
        return

    # 显示统计信息
    if args.stats:
        show_statistics(client)
        return

    # 按ID查询详细信息
    if args.id:
        get_asset_details(client, args.id)
        return

    # 构建过滤条件
    filters = {}
    if args.env:
        filters['environment'] = args.env
    if args.status:
        filters['status'] = args.status
    if args.owner:
        filters['owner'] = args.owner
    if args.limit:
        filters['limit'] = args.limit

    # 执行查询
    assets = []
    if args.type:
        assets = query_by_type(client, args.type, **filters)
    elif args.ip:
        assets = query_by_ip(client, args.ip)
    elif args.name:
        assets = query_by_name(client, args.name)
    elif args.search:
        assets = search_assets(client, args.search, **filters)
    elif args.risk:
        assets = query_by_risk(client, args.min_score, args.max_score, **filters)
    elif args.isolation:
        assets = query_by_isolation(client, args.isolation, **filters)
    elif args.segment:
        assets = query_by_network_segment(client, args.segment, **filters)
    else:
        # 默认: 列出所有资产（限制数量）
        assets = client.list_assets(limit=args.limit or 20)

    # 输出结果
    if not assets:
        print("没有找到匹配的资产")
        return

    print(f"\n找到 {len(assets)} 条记录\n")

    if args.output == 'json':
        # 过滤敏感字段
        for asset in assets:
            asset.pop('password_encrypted', None)
            asset.pop('password', None)
        print(json.dumps(assets, indent=2, ensure_ascii=False))
    else:
        # 表格输出
        headers = ['asset_id', 'name', 'asset_type', 'ip_address', 'environment', 'status', 'risk_score']
        print_table(assets, headers)


if __name__ == '__main__':
    main()
